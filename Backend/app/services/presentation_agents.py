from __future__ import annotations

from textwrap import shorten
from typing import Any

from app.clients.gemini import GeminiClient
from app.config import Settings
from app.models import (
    ChallengerQuestion,
    DeckBlueprint,
    RetrievalResult,
    SpecialistBrief,
)


INTENT_PROFILES: dict[str, dict[str, str]] = {
    "technical": {
        "name": "The Architect",
        "retrieval_query": "technical architecture, engineering tradeoffs, benchmarks, implementation constraints, specifications",
        "stance": "Focus on systems thinking, technical credibility, tradeoffs, integration risks, and evidence-backed feasibility.",
    },
    "business": {
        "name": "The Strategist",
        "retrieval_query": "market outlook, ROI, competition, customer value, commercialization, revenue implications",
        "stance": "Focus on market timing, value creation, business risk, commercial adoption, and executive clarity.",
    },
    "academic": {
        "name": "The Scholar",
        "retrieval_query": "research findings, methodology, citations, literature review, evidence quality, limitations",
        "stance": "Focus on rigor, methodology, evidence quality, caveats, and precise citation-minded reasoning.",
    },
    "creative": {
        "name": "The Storyteller",
        "retrieval_query": "narrative hooks, audience emotion, memorable framing, contrasts, visuals, storytelling",
        "stance": "Focus on narrative momentum, memorable framing, human stakes, and presentation impact.",
    },
}


class PresentationAgentService:
    def __init__(self, gemini_client: GeminiClient, settings: Settings) -> None:
        self.gemini_client = gemini_client
        self.settings = settings

    def build_retrieval_query(self, *, topic: str, intent: str) -> str:
        profile = INTENT_PROFILES[intent]
        return (
            f"Topic: {topic}. Retrieve the most useful material for {profile['name']} with emphasis on "
            f"{profile['retrieval_query']}."
        )

    async def build_specialist_brief(
        self,
        *,
        topic: str,
        intent: str,
        context: list[RetrievalResult],
    ) -> SpecialistBrief:
        profile = INTENT_PROFILES[intent]
        prompt = (
            f"You are {profile['name']} inside an autonomous presentation agency.\n"
            f"{profile['stance']}\n\n"
            f"Topic: {topic}\n"
            f"Intent: {intent}\n\n"
            "Create a strategic presentation brief using only the supplied memory orbs. "
            "Ignore weak or noisy source fragments when better evidence exists. "
            "Be concise and concrete.\n\n"
            f"Memory orbs:\n{self._format_context(context, max_items=6, max_chars=420)}"
        )
        schema = {
            "type": "object",
            "properties": {
                "specialist_name": {"type": "string"},
                "point_of_view": {"type": "string"},
                "core_thesis": {"type": "string"},
                "audience_frame": {"type": "string"},
                "narrative_arc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 4,
                },
                "evidence_priorities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 4,
                },
                "slide_strategy": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 4,
                },
                "risks_and_gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 4,
                },
                "recommended_tone": {"type": "string"},
            },
            "required": [
                "specialist_name",
                "point_of_view",
                "core_thesis",
                "audience_frame",
                "narrative_arc",
                "evidence_priorities",
                "slide_strategy",
                "risks_and_gaps",
                "recommended_tone",
            ],
        }
        data = await self.gemini_client.generate_structured_json(
            prompt=prompt,
            schema=schema,
            max_tokens=self.settings.specialist_max_tokens,
        )
        return SpecialistBrief.model_validate(data)

    async def build_deck_blueprint(
        self,
        *,
        topic: str,
        intent: str,
        brief: SpecialistBrief,
        context: list[RetrievalResult],
    ) -> DeckBlueprint:
        prompt = (
            "You are The Producer for an autonomous presentation agency.\n"
            "Turn the specialist brief into a polished deck blueprint. "
            "Keep the flow persuasive, specific, and grounded in the supplied memory orbs.\n\n"
            f"Topic: {topic}\n"
            f"Intent: {intent}\n"
            f"Specialist brief:\n{brief.model_dump_json(indent=2)}\n\n"
            f"Memory orbs:\n{self._format_context(context, max_items=8, max_chars=620)}\n\n"
            "Create 8 slides. Keep titles sharp and objectives to one sentence, but make the slide body richer. "
            "Each slide needs a summary_paragraph of 2 to 4 sentences that explains the point in human language. "
            "Key points should be concrete and informative, not fragments. "
            "Speaker notes can be 3 concise sentences when useful. "
            "Include evidence_orbs using the ORB ids whenever a slide is supported by source material."
        )
        schema = {
            "type": "object",
            "properties": {
                "deck_title": {"type": "string"},
                "deck_subtitle": {"type": "string"},
                "target_audience": {"type": "string"},
                "presentation_goal": {"type": "string"},
                "design_direction": {"type": "string"},
                "slides": {
                    "type": "array",
                    "minItems": 8,
                    "maxItems": 8,
                    "items": {
                        "type": "object",
                        "properties": {
                            "slide_number": {"type": "integer"},
                            "title": {"type": "string"},
                            "objective": {"type": "string"},
                            "summary_paragraph": {"type": "string"},
                            "key_points": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 4,
                                "maxItems": 5,
                            },
                            "visual_type": {
                                "type": "string",
                                "enum": [
                                    "title",
                                    "agenda",
                                    "timeline",
                                    "comparison",
                                    "architecture",
                                    "chart",
                                    "table",
                                    "case_study",
                                    "process",
                                    "quote",
                                    "closing",
                                ],
                            },
                            "visual_brief": {"type": "string"},
                            "speaker_notes": {"type": "string"},
                            "evidence_orbs": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "slide_number",
                            "title",
                            "objective",
                            "summary_paragraph",
                            "key_points",
                            "visual_type",
                            "visual_brief",
                            "speaker_notes",
                            "evidence_orbs",
                        ],
                    },
                },
            },
            "required": [
                "deck_title",
                "deck_subtitle",
                "target_audience",
                "presentation_goal",
                "design_direction",
                "slides",
            ],
        }
        data = await self.gemini_client.generate_structured_json(
            prompt=prompt,
            schema=schema,
            max_tokens=self.settings.deck_blueprint_max_tokens,
        )
        return DeckBlueprint.model_validate(data)

    async def build_challenger_questions(
        self,
        *,
        topic: str,
        intent: str,
        deck: DeckBlueprint,
        context: list[RetrievalResult],
    ) -> list[ChallengerQuestion]:
        prompt = (
            "You are The Challenger, a post-presentation mock Q&A agent.\n"
            "Generate the hardest audience questions that could expose weaknesses, missing evidence, or overclaims.\n\n"
            f"Topic: {topic}\n"
            f"Intent: {intent}\n"
            f"Deck blueprint:\n{deck.model_dump_json(indent=2)}\n\n"
            f"Memory orbs:\n{self._format_context(context, max_items=8, max_chars=480)}\n\n"
            "Return 6 questions ranked by practical importance. Reuse ORB ids in evidence_orbs when possible."
        )
        schema = {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "minItems": 6,
                    "maxItems": 6,
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "why_it_matters": {"type": "string"},
                            "suggested_answer": {"type": "string"},
                            "evidence_orbs": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                            },
                        },
                        "required": [
                            "question",
                            "why_it_matters",
                            "suggested_answer",
                            "evidence_orbs",
                            "severity",
                        ],
                    },
                }
            },
            "required": ["questions"],
        }
        data = await self.gemini_client.generate_structured_json(
            prompt=prompt,
            schema=schema,
            max_tokens=self.settings.challenger_max_tokens,
        )
        return [ChallengerQuestion.model_validate(item) for item in data["questions"]]

    def _format_context(
        self,
        context: list[RetrievalResult],
        *,
        max_items: int = 8,
        max_chars: int = 700,
    ) -> str:
        filtered = [item for item in context if not self._is_low_signal(item)]
        chosen = (filtered or context)[:max_items]
        formatted = []
        for item in chosen:
            orb_id = self._orb_id(item)
            source_label = item.metadata.get("url") or item.source
            excerpt = shorten(" ".join(item.content.split()), width=max_chars, placeholder="...")
            formatted.append(
                f"{orb_id}\n"
                f"source={item.source}\n"
                f"reference={source_label}\n"
                f"score={item.score:.3f}\n"
                f"content={excerpt}"
            )
        return "\n\n".join(formatted)

    @staticmethod
    def _orb_id(item: RetrievalResult) -> str:
        return f"ORB-{item.id[-8:]}"

    @staticmethod
    def _is_low_signal(item: RetrievalResult) -> bool:
        lowered = item.content.lower()
        noisy_markers = (
            "oops, something went wrong",
            "error 403",
            "forbidden",
            "base64-image-removed",
            "skip to navigation",
            "skip to main content",
        )
        return any(marker in lowered for marker in noisy_markers)
