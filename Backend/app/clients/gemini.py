from __future__ import annotations

import base64
import json
import mimetypes
from typing import Any

import httpx

from app.config import Settings
from app.models import IntentResponse


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://generativelanguage.googleapis.com"

    async def classify_intent(self, topic: str) -> IntentResponse:
        prompt = (
            "You are an intent router for an autonomous presentation agency.\n"
            "Return only valid JSON with this exact shape:\n"
            '{"intent":"technical|business|academic|creative","search_queries":["q1","q2","q3","q4","q5"],"tone":"...","user_goal":"..."}\n'
            "Generate exactly five search queries.\n\n"
            f"Topic: {topic}"
        )

        if self.settings.uses_openrouter:
            text = await self._openrouter_chat_text(
                model=self.settings.gemini_classifier_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You must respond with raw JSON only and no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.settings.classifier_max_tokens,
            )
        else:
            schema = {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": ["technical", "business", "academic", "creative"],
                    },
                    "search_queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 5,
                        "maxItems": 5,
                    },
                    "tone": {"type": "string"},
                    "user_goal": {"type": "string"},
                },
                "required": ["intent", "search_queries", "tone", "user_goal"],
            }

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                    "responseJsonSchema": schema,
                },
            }

            data = await self._post_json(
                f"/v1beta/models/{self.settings.gemini_classifier_model}:generateContent",
                payload,
            )
            text = self._extract_text(data)

        text = self._strip_json_fence(text)
        return IntentResponse.model_validate(json.loads(text))

    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        if self.settings.uses_openrouter:
            data = await self._openrouter_post_json(
                "/embeddings",
                {
                    "model": self.settings.gemini_embedding_model,
                    "input": text,
                },
            )
            return data["data"][0]["embedding"]

        payload = {
            "model": f"models/{self.settings.gemini_embedding_model}",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        }
        data = await self._post_json(
            f"/v1beta/models/{self.settings.gemini_embedding_model}:embedContent",
            payload,
        )
        return data["embedding"]["values"]

    async def describe_inline_media(
        self,
        *,
        prompt: str,
        file_bytes: bytes,
        mime_type: str,
    ) -> str:
        if self.settings.uses_openrouter:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        self._build_openrouter_media_part(file_bytes=file_bytes, mime_type=mime_type),
                    ],
                }
            ]
            return await self._openrouter_chat_text(
                model=self.settings.gemini_generation_model,
                messages=messages,
                max_tokens=self.settings.generation_max_tokens,
            )

        encoded = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": mime_type, "data": encoded}},
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.2},
        }
        data = await self._post_json(
            f"/v1beta/models/{self.settings.gemini_generation_model}:generateContent",
            payload,
        )
        return self._extract_text(data)

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        headers = {
            "x-goog-api-key": self.settings.gemini_api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            response = await client.post(path, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Gemini API request failed with status {response.status_code}: {response.text}"
                ) from exc
            return response.json()

    async def _openrouter_chat_text(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
    ) -> str:
        data = await self._openrouter_post_json(
            "/chat/completions",
            {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": max_tokens,
            },
        )
        return data["choices"][0]["message"]["content"].strip()

    async def _openrouter_post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = self.settings.resolved_openrouter_api_key
        if not api_key:
            raise RuntimeError("OpenRouter API key is not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if self.settings.openrouter_site_url:
            headers["HTTP-Referer"] = self.settings.openrouter_site_url
        if self.settings.openrouter_app_name:
            headers["X-Title"] = self.settings.openrouter_app_name

        async with httpx.AsyncClient(base_url=self.settings.openrouter_base_url, timeout=90.0) as client:
            response = await client.post(path, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"OpenRouter API request failed with status {response.status_code}: {response.text}"
                ) from exc
            return response.json()

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if not text_parts:
            raise RuntimeError("Gemini returned no text parts")
        return "\n".join(text_parts).strip()

    @staticmethod
    def _strip_json_fence(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```json"):
            stripped = stripped.removeprefix("```json").removesuffix("```").strip()
        elif stripped.startswith("```"):
            stripped = stripped.removeprefix("```").removesuffix("```").strip()
        return stripped

    @staticmethod
    def _build_openrouter_media_part(*, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        extension = mimetypes.guess_extension(mime_type) or ""
        if mime_type.startswith("image/"):
            return {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}}
        if mime_type.startswith("audio/"):
            return {
                "type": "input_audio",
                "input_audio": {"data": encoded, "format": extension.lstrip(".") or "wav"},
            }
        if mime_type.startswith("video/"):
            return {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{encoded}"}}
        raise RuntimeError(f"Unsupported OpenRouter media type: {mime_type}")
