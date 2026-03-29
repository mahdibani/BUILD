from __future__ import annotations

import asyncio
from typing import Sequence

from fastapi import UploadFile

from app.clients.firecrawl import FirecrawlClient
from app.clients.gemini import GeminiClient
from app.clients.qdrant_store import QdrantStore
from app.models import ContentChunk, IntakeResponse
from app.services.retrieval import get_specialist_context
from app.services.sensory import SensoryService


class PresentationPipeline:
    def __init__(
        self,
        *,
        gemini_client: GeminiClient,
        firecrawl_client: FirecrawlClient,
        qdrant_store: QdrantStore,
        sensory_service: SensoryService,
    ) -> None:
        self.gemini_client = gemini_client
        self.firecrawl_client = firecrawl_client
        self.qdrant_store = qdrant_store
        self.sensory_service = sensory_service

    async def intake(
        self,
        *,
        topic: str,
        files: Sequence[UploadFile] | None,
        resource_urls: Sequence[str] | None,
        allow_web_search: bool,
    ) -> IntakeResponse:
        intent = await self.gemini_client.classify_intent(topic)

        has_user_resources = bool(files) or bool(resource_urls)

        if not has_user_resources:
            scenario = "topic_only_deep_research"
            chunks = await self.firecrawl_client.scout_topic(topic=topic, intent=intent)
        elif allow_web_search:
            scenario = "hybrid"
            sensory_task = self.sensory_service.process_inputs(
                topic=topic,
                intent=intent,
                files=files,
                resource_urls=resource_urls,
            )
            scout_task = self.firecrawl_client.scout_topic(topic=topic, intent=intent)
            sensory_chunks, scout_chunks = await asyncio.gather(sensory_task, scout_task)
            chunks = [*sensory_chunks, *scout_chunks]
        else:
            scenario = "user_files_only"
            chunks = await self.sensory_service.process_inputs(
                topic=topic,
                intent=intent,
                files=files,
                resource_urls=resource_urls,
            )

        vectors = await asyncio.gather(
            *(self.gemini_client.embed_chunk(chunk) for chunk in chunks)
        )
        stored_points = self.qdrant_store.upsert_chunks(chunks, list(vectors))

        return IntakeResponse(
            scenario=scenario,
            topic=topic,
            intent=intent,
            total_chunks=len(chunks),
            stored_points=stored_points,
            source_breakdown=self.qdrant_store.breakdown_by_source(chunks),
        )

    async def specialist_context(self, *, query: str, intent: str):
        return await get_specialist_context(
            query,
            intent,
            gemini_client=self.gemini_client,
            qdrant_store=self.qdrant_store,
        )
