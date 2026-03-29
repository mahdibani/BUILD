from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class IntentResponse(BaseModel):
    intent: Literal["technical", "business", "academic", "creative"]
    search_queries: list[str] = Field(min_length=5, max_length=5)
    tone: str
    user_goal: str

    @field_validator("search_queries")
    @classmethod
    def ensure_five_queries(cls, value: list[str]) -> list[str]:
        if len(value) != 5:
            raise ValueError("search_queries must contain exactly 5 strings")
        return value


class ContentChunk(BaseModel):
    content: str
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    topic: str
    intent: Literal["technical", "business", "academic", "creative"]
    embedding_parts: list[dict[str, Any]] | None = None

    @property
    def contextualized_content(self) -> str:
        return f"[Intent: {self.intent}] [Topic: {self.topic}] {self.content}"

    @property
    def embedding_content(self) -> dict[str, Any]:
        parts: list[dict[str, Any]] = [{"text": self.contextualized_content}]
        if self.embedding_parts:
            parts.extend(self.embedding_parts)
        return {"parts": parts}


class RetrievalResult(BaseModel):
    id: str
    score: float
    content: str
    source: str
    intent: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntakeResponse(BaseModel):
    scenario: Literal["topic_only_deep_research", "hybrid", "user_files_only"]
    topic: str
    intent: IntentResponse
    total_chunks: int
    stored_points: int
    source_breakdown: dict[str, int]


class SpecialistContextResponse(BaseModel):
    query: str
    intent: Literal["technical", "business", "academic", "creative"]
    results: list[RetrievalResult]


class SpecialistBrief(BaseModel):
    specialist_name: str
    point_of_view: str
    core_thesis: str
    audience_frame: str
    narrative_arc: list[str] = Field(min_length=3, max_length=6)
    evidence_priorities: list[str] = Field(min_length=3, max_length=6)
    slide_strategy: list[str] = Field(min_length=3, max_length=6)
    risks_and_gaps: list[str] = Field(default_factory=list)
    recommended_tone: str


class SlideBlueprint(BaseModel):
    slide_number: int
    title: str
    objective: str
    key_points: list[str] = Field(min_length=3, max_length=5)
    visual_type: Literal[
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
    ]
    visual_brief: str
    speaker_notes: str
    evidence_orbs: list[str] = Field(default_factory=list)


class DeckBlueprint(BaseModel):
    deck_title: str
    deck_subtitle: str
    target_audience: str
    presentation_goal: str
    design_direction: str
    slides: list[SlideBlueprint] = Field(min_length=7, max_length=10)


class ChallengerQuestion(BaseModel):
    question: str
    why_it_matters: str
    suggested_answer: str
    evidence_orbs: list[str] = Field(default_factory=list)
    severity: Literal["high", "medium", "low"]


class GeneratePresentationRequest(BaseModel):
    topic: str
    intent: Literal["technical", "business", "academic", "creative"] | None = None
    include_challenger: bool = True
    auto_research: bool = True


class GeneratedPresentationResponse(BaseModel):
    topic: str
    intent: Literal["technical", "business", "academic", "creative"]
    specialist: SpecialistBrief
    deck: DeckBlueprint
    challenger: list[ChallengerQuestion] = Field(default_factory=list)
    source_context: list[RetrievalResult]
    auto_researched: bool = False
    pptx_path: str | None = None
    download_url: str | None = None
