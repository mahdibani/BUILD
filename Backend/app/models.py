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
