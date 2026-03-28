from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from app.config import Settings
from app.models import IntentResponse


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://generativelanguage.googleapis.com"

    async def classify_intent(self, topic: str) -> IntentResponse:
        schema = {
            "type": "OBJECT",
            "properties": {
                "intent": {
                    "type": "STRING",
                    "enum": ["technical", "business", "academic", "creative"],
                },
                "search_queries": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "minItems": 5,
                    "maxItems": 5,
                },
                "tone": {"type": "STRING"},
                "user_goal": {"type": "STRING"},
            },
            "required": ["intent", "search_queries", "tone", "user_goal"],
        }

        prompt = (
            "You are an intent router for an autonomous presentation agency.\n"
            "Classify the topic into one presentation intent and generate exactly five web research queries.\n"
            "Return JSON only.\n\n"
            f"Topic: {topic}"
        )

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
        return IntentResponse.model_validate(json.loads(text))

    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
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
            response.raise_for_status()
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
