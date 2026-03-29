from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
from pathlib import Path
from typing import Sequence

from fastapi import UploadFile
from youtube_transcript_api import YouTubeTranscriptApi

from app.clients.firecrawl import FirecrawlClient
from app.clients.gemini import GeminiClient
from app.config import Settings
from app.models import ContentChunk, IntentResponse
from app.services.chunking import chunk_pdf_documents, chunk_text, extract_youtube_video_id


class SensoryService:
    def __init__(
        self,
        *,
        settings: Settings,
        gemini_client: GeminiClient,
        firecrawl_client: FirecrawlClient,
    ) -> None:
        self.settings = settings
        self.gemini_client = gemini_client
        self.firecrawl_client = firecrawl_client

    async def process_inputs(
        self,
        *,
        topic: str,
        intent: IntentResponse,
        files: Sequence[UploadFile] | None = None,
        resource_urls: Sequence[str] | None = None,
    ) -> list[ContentChunk]:
        tasks = []

        for upload in files or []:
            tasks.append(self._process_upload(topic=topic, intent=intent, upload=upload))

        for url in resource_urls or []:
            tasks.append(self._process_url(topic=topic, intent=intent, url=url))

        if not tasks:
            return []

        results = await asyncio.gather(*tasks)
        flattened: list[ContentChunk] = []
        for item in results:
            flattened.extend(item)
        return flattened

    async def _process_upload(
        self,
        *,
        topic: str,
        intent: IntentResponse,
        upload: UploadFile,
    ) -> list[ContentChunk]:
        file_bytes = await upload.read()
        filename = upload.filename or "upload"
        content_type = upload.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        suffix = Path(filename).suffix.lower()

        if suffix == ".pdf" or content_type == "application/pdf":
            pdf_chunks = chunk_pdf_documents(file_bytes, self.settings.pdf_pages_per_chunk)
            return [
                ContentChunk(
                    content=text,
                    source="user_upload",
                    topic=topic,
                    intent=intent.intent,
                    embedding_parts=[self._build_inline_part(file_bytes=pdf_bytes, mime_type="application/pdf")]
                    if len(pdf_bytes) <= self.settings.inline_media_limit_bytes
                    else None,
                    metadata={"filename": filename, "content_type": content_type, **meta},
                )
                for pdf_bytes, text, meta in pdf_chunks
            ]

        if content_type.startswith("text/") or suffix in {".md", ".txt", ".csv", ".json"}:
            decoded = file_bytes.decode("utf-8", errors="ignore")
            try:
                if suffix == ".json":
                    decoded = json.dumps(json.loads(decoded), indent=2)
            except json.JSONDecodeError:
                pass

            return [
                ContentChunk(
                    content=chunk,
                    source="user_upload",
                    topic=topic,
                    intent=intent.intent,
                    metadata={"filename": filename, "content_type": content_type, "chunk_index": index},
                )
                for index, chunk in enumerate(
                    chunk_text(decoded, self.settings.max_text_chars, self.settings.text_chunk_overlap),
                    start=1,
                )
            ]

        if content_type.startswith("image/"):
            media_description = await self._describe_media(
                topic=topic,
                intent=intent.intent,
                file_bytes=file_bytes,
                mime_type=content_type,
                file_name=filename,
                media_kind="image",
            )
            return [
                ContentChunk(
                    content=media_description,
                    source="user_upload",
                    topic=topic,
                    intent=intent.intent,
                    embedding_parts=[self._build_inline_part(file_bytes=file_bytes, mime_type=content_type)]
                    if len(file_bytes) <= self.settings.inline_media_limit_bytes
                    else None,
                    metadata={"filename": filename, "content_type": content_type},
                )
            ]

        if content_type.startswith("audio/") or content_type.startswith("video/"):
            media_kind = "audio" if content_type.startswith("audio/") else "video"
            media_description = await self._describe_media(
                topic=topic,
                intent=intent.intent,
                file_bytes=file_bytes,
                mime_type=content_type,
                file_name=filename,
                media_kind=media_kind,
            )
            return [
                ContentChunk(
                    content=media_description,
                    source="user_upload",
                    topic=topic,
                    intent=intent.intent,
                    embedding_parts=[self._build_inline_part(file_bytes=file_bytes, mime_type=content_type)]
                    if len(file_bytes) <= self.settings.inline_media_limit_bytes
                    else None,
                    metadata={
                        "filename": filename,
                        "content_type": content_type,
                        "chunk_strategy": "single_inline_pass",
                        "recommended_chunk_seconds": 120,
                    },
                )
            ]

        return [
            ContentChunk(
                content=f"Uploaded file {filename} ({content_type}) could not be parsed, so only metadata was stored.",
                source="user_upload",
                topic=topic,
                intent=intent.intent,
                metadata={"filename": filename, "content_type": content_type, "warning": "unsupported_type"},
            )
        ]

    async def _process_url(
        self,
        *,
        topic: str,
        intent: IntentResponse,
        url: str,
    ) -> list[ContentChunk]:
        youtube_id = extract_youtube_video_id(url)
        if youtube_id:
            transcript = await asyncio.to_thread(self._fetch_youtube_transcript, youtube_id)
            if transcript:
                chunks = chunk_text(transcript, self.settings.max_text_chars, self.settings.text_chunk_overlap)
                return [
                    ContentChunk(
                        content=chunk,
                        source="youtube",
                        topic=topic,
                        intent=intent.intent,
                        metadata={"url": url, "video_id": youtube_id, "chunk_index": index},
                    )
                    for index, chunk in enumerate(chunks, start=1)
                ]

        try:
            scraped = await self.firecrawl_client.scrape(url)
            content = scraped.get("markdown") or scraped.get("html") or f"Scraped resource from {url}"
        except Exception as exc:
            return [
                ContentChunk(
                    content=f"Resource scraping failed for {url}: {exc}",
                    source="user_link_error",
                    topic=topic,
                    intent=intent.intent,
                    metadata={"url": url},
                )
            ]

        return [
            ContentChunk(
                content=content,
                source="user_link",
                topic=topic,
                intent=intent.intent,
                metadata={"url": url},
            )
        ]

    async def _describe_media(
        self,
        *,
        topic: str,
        intent: str,
        file_bytes: bytes,
        mime_type: str,
        file_name: str,
        media_kind: str,
    ) -> str:
        if self.settings.uses_openrouter and not self.settings.openrouter_generation_supports_multimodal:
            return (
                f"Uploaded {media_kind} asset '{file_name}' was received for the topic '{topic}'. "
                f"The current OpenRouter model is being used in text-only mode for the '{intent}' intent, "
                "so this media could not be deeply analyzed. Store or review this asset separately, "
                "or switch to a multimodal-capable model for image/audio/video understanding."
            )

        if len(file_bytes) > self.settings.inline_media_limit_bytes:
            return (
                f"{media_kind.title()} upload '{file_name}' exceeded the inline Gemini processing limit. "
                "Store this asset through an offline chunking pipeline before deep multimodal analysis."
            )

        prompt = (
            "You are a sensory agent for a presentation system. "
            f"Describe the uploaded {media_kind} in a way that is useful for slide generation and RAG retrieval. "
            f"Presentation intent: {intent}. Topic: {topic}. "
            "Focus on concrete facts, scene details, spoken claims, visual evidence, and notable timestamps if obvious."
        )
        return await self.gemini_client.describe_inline_media(
            prompt=prompt,
            file_bytes=file_bytes,
            mime_type=mime_type,
        )

    @staticmethod
    def _build_inline_part(*, file_bytes: bytes, mime_type: str) -> dict[str, dict[str, str]]:
        return {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(file_bytes).decode("utf-8"),
            }
        }

    @staticmethod
    def _fetch_youtube_transcript(video_id: str) -> str:
        transcript_entries = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
        return " ".join(entry["text"] for entry in transcript_entries)
