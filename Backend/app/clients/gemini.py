from __future__ import annotations

import asyncio
import base64
import json
from math import sqrt
from typing import Any

import httpx

from app.config import Settings
from app.models import ContentChunk, IntentResponse


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://generativelanguage.googleapis.com"

    async def classify_intent(self, topic: str) -> IntentResponse:
        prompt = (
            "You are an intent router for an autonomous presentation agency.\n"
            "Classify based on the audience goal and presentation job, not just the subject matter.\n"
            "If the topic is technical but framed for investors, executives, ROI, market timing, or business decisions, choose business.\n"
            "If the topic is framed around a thesis, literature review, methodology, or citations, choose academic.\n"
            "If the topic is framed around storytelling, campaign framing, narrative, or emotional resonance, choose creative.\n"
            "Only choose technical when the presentation primarily serves engineering understanding, implementation, architecture, or system design.\n"
            "Return only valid JSON with this exact shape:\n"
            '{"intent":"technical|business|academic|creative","search_queries":["q1","q2","q3","q4","q5"],"tone":"...","user_goal":"..."}\n'
            "Generate exactly five search queries.\n\n"
            f"Topic: {topic}"
        )

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

        text = await self.generate_structured_text(
            prompt=prompt,
            schema=schema,
            model=self.settings.gemini_classifier_model,
            max_tokens=self.settings.classifier_max_tokens,
        )
        classified = IntentResponse.model_validate(json.loads(text))
        heuristic_intent = self._infer_intent_from_topic(topic)
        if (
            heuristic_intent
            and heuristic_intent != classified.intent
            and classified.intent == "technical"
        ):
            return IntentResponse(
                intent=heuristic_intent,
                search_queries=self._fallback_search_queries(topic, heuristic_intent),
                tone=self._fallback_tone(heuristic_intent),
                user_goal=self._fallback_user_goal(topic, heuristic_intent),
            )
        return classified

    async def generate_structured_json(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        text = await self.generate_structured_text(
            prompt=prompt,
            schema=schema,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            repair_prompt = (
                f"{prompt}\n\n"
                "The previous attempt was invalid or truncated JSON. "
                "Return only one valid JSON object that matches the schema exactly. "
                "Keep string fields concise. Do not include markdown fences, commentary, or trailing text."
            )
            repaired_text = await self.generate_structured_text(
                prompt=repair_prompt,
                schema=schema,
                model=model,
                max_tokens=(
                    max_tokens + self.settings.structured_repair_token_buffer
                    if max_tokens is not None
                    else None
                ),
                temperature=0.1,
            )
            return json.loads(repaired_text)

    async def generate_structured_text(
        self,
        *,
        prompt: str,
        schema: dict[str, Any],
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
    ) -> str:
        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
            "responseJsonSchema": schema,
        }
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }

        data = await self._post_json(
            f"/v1beta/models/{model or self.settings.gemini_generation_model}:generateContent",
            payload,
        )
        return self._strip_json_fence(self._extract_text(data))

    async def generate_text(
        self,
        *,
        prompt: str,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
    ) -> str:
        generation_config: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }

        data = await self._post_json(
            f"/v1beta/models/{model or self.settings.gemini_generation_model}:generateContent",
            payload,
        )
        return self._extract_text(data)

    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        payload: dict[str, Any] = {
            "model": f"models/{self.settings.gemini_embedding_model}",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        }
        if self.settings.gemini_embedding_dimension:
            payload["outputDimensionality"] = self.settings.gemini_embedding_dimension

        data = await self._post_json(
            f"/v1beta/models/{self.settings.gemini_embedding_model}:embedContent",
            payload,
        )
        return self._normalize_vector(data["embedding"]["values"])

    async def embed_chunk(self, chunk: ContentChunk) -> list[float]:
        if self.settings.uses_multimodal_gemini_embeddings:
            payload: dict[str, Any] = {
                "model": f"models/{self.settings.gemini_embedding_model}",
                "content": chunk.embedding_content,
                "outputDimensionality": self.settings.gemini_embedding_dimension,
                "taskType": "RETRIEVAL_DOCUMENT",
            }
            data = await self._post_json(
                f"/v1beta/models/{self.settings.gemini_embedding_model}:embedContent",
                payload,
            )
            return self._normalize_vector(data["embedding"]["values"])

        return await self.embed_text(chunk.contextualized_content)

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

        timeout = httpx.Timeout(
            timeout=self.settings.gemini_timeout_seconds,
            connect=min(self.settings.gemini_timeout_seconds, 30.0),
        )

        async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout) as client:
            max_attempts = 4
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await client.post(path, headers=headers, json=payload)
                    response.raise_for_status()
                    return response.json()
                except httpx.ReadTimeout as exc:
                    if attempt < max_attempts:
                        await asyncio.sleep(float(2 ** (attempt - 1)))
                        continue
                    raise RuntimeError(
                        f"Gemini API request timed out after {self.settings.gemini_timeout_seconds} seconds."
                    ) from exc
                except httpx.HTTPStatusError as exc:
                    if attempt < max_attempts and self._should_retry(response.status_code):
                        retry_after = self._retry_after_seconds(response)
                        delay = retry_after if retry_after is not None else float(2 ** (attempt - 1))
                        await asyncio.sleep(delay)
                        continue
                    raise RuntimeError(
                        f"Gemini API request failed with status {response.status_code}: {response.text}"
                    ) from exc

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
    def _normalize_vector(vector: list[float]) -> list[float]:
        magnitude = sqrt(sum(v * v for v in vector))
        if not magnitude:
            return vector
        return [v / magnitude for v in vector]

    @staticmethod
    def _should_retry(status_code: int) -> bool:
        return status_code in {429, 500, 502, 503, 504}

    @staticmethod
    def _retry_after_seconds(response: httpx.Response) -> float | None:
        raw_value = response.headers.get("retry-after")
        if not raw_value:
            return None
        try:
            return float(raw_value)
        except ValueError:
            return None

    @staticmethod
    def _infer_intent_from_topic(topic: str) -> str | None:
        lowered = topic.lower()
        keyword_groups = {
            "business": (
                "investor",
                "investment",
                "roi",
                "revenue",
                "market",
                "pricing",
                "customer",
                "go-to-market",
                "sales",
                "executive",
                "board",
                "startup",
                "pitch",
                "commercial",
                "competition",
            ),
            "academic": (
                "thesis",
                "dissertation",
                "paper",
                "research",
                "literature review",
                "methodology",
                "citation",
                "journal",
                "study",
                "seminar",
                "defense",
                "hypothesis",
            ),
            "creative": (
                "story",
                "storytelling",
                "narrative",
                "brand",
                "campaign",
                "creative",
                "visual identity",
                "moodboard",
                "emotion",
                "hook",
                "film",
                "launch",
            ),
        }
        scored = {
            intent: sum(1 for keyword in keywords if keyword in lowered)
            for intent, keywords in keyword_groups.items()
        }
        top_intent = max(scored, key=scored.get)
        return top_intent if scored[top_intent] >= 2 else None

    @staticmethod
    def _fallback_search_queries(topic: str, intent: str) -> list[str]:
        templates = {
            "technical": [
                "{topic} architecture and implementation tradeoffs",
                "{topic} benchmarks and performance constraints",
                "{topic} technical risks and integration challenges",
                "{topic} system design best practices",
                "{topic} current state of technology and roadmap",
            ],
            "business": [
                "{topic} market outlook and competitive landscape",
                "{topic} ROI business case and value proposition",
                "{topic} customer adoption and commercialization trends",
                "{topic} executive risks and strategic opportunities",
                "{topic} 2026 market forecast and industry momentum",
            ],
            "academic": [
                "{topic} recent peer reviewed research findings",
                "{topic} methodology evidence and limitations",
                "{topic} literature review and citation sources",
                "{topic} academic debates and open questions",
                "{topic} current research consensus and future work",
            ],
            "creative": [
                "{topic} narrative hooks and audience resonance",
                "{topic} visual inspiration and storytelling angles",
                "{topic} memorable framing examples and campaigns",
                "{topic} emotional positioning and audience insight",
                "{topic} creative direction references and motifs",
            ],
        }
        return [template.format(topic=topic) for template in templates[intent]]

    @staticmethod
    def _fallback_tone(intent: str) -> str:
        return {
            "technical": "clear, precise, and engineering-forward",
            "business": "confident, strategic, and executive-ready",
            "academic": "rigorous, measured, and citation-minded",
            "creative": "vivid, engaging, and story-led",
        }[intent]

    @staticmethod
    def _fallback_user_goal(topic: str, intent: str) -> str:
        return {
            "technical": f"Explain {topic} with implementation clarity and technical credibility.",
            "business": f"Position {topic} as a business opportunity with market and decision relevance.",
            "academic": f"Present {topic} with research rigor, evidence quality, and methodological clarity.",
            "creative": f"Turn {topic} into a memorable narrative with strong visual and emotional framing.",
        }[intent]
