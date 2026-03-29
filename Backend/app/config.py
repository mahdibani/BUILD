from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Build Presentation Backend"
    gemini_api_key: str = Field(default="")
    openrouter_api_key: str | None = Field(default=None)
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_site_url: str | None = Field(default=None)
    openrouter_app_name: str | None = Field(default="Build Presentation Backend")
    firecrawl_api_key: str = Field(default="")
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection: str = Field(default="presentation_memory")

    gemini_classifier_model: str = Field(default="gemini-2.5-flash-lite")
    gemini_generation_model: str = Field(default="gemini-2.5-flash-lite")
    gemini_embedding_model: str = Field(default="gemini-embedding-2-preview")
    gemini_embedding_dimension: int = Field(default=1536)
    classifier_max_tokens: int = Field(default=400)
    generation_max_tokens: int = Field(default=1200)

    firecrawl_search_limit: int = Field(default=3)
    max_text_chars: int = Field(default=3500)
    text_chunk_overlap: int = Field(default=400)
    pdf_pages_per_chunk: int = Field(default=6)
    inline_media_limit_bytes: int = Field(default=20_000_000)

    @field_validator("qdrant_api_key", mode="before")
    @classmethod
    def empty_qdrant_api_key_to_none(cls, value: str | None):
        if value in ("", None):
            return None
        return value

    @field_validator("openrouter_api_key", "openrouter_site_url", "openrouter_app_name", mode="before")
    @classmethod
    def empty_optional_strings_to_none(cls, value: str | None):
        if value in ("", None):
            return None
        return value

    @property
    def uses_openrouter(self) -> bool:
        return bool(self.openrouter_api_key or self.gemini_api_key.startswith("sk-or-"))

    @property
    def resolved_openrouter_api_key(self) -> str | None:
        return self.openrouter_api_key or (self.gemini_api_key if self.gemini_api_key.startswith("sk-or-") else None)

    @property
    def openrouter_generation_supports_multimodal(self) -> bool:
        model = self.gemini_generation_model.lower()
        multimodal_markers = (
            "gemini",
            "vision",
            "vl",
            "omni",
            "pixtral",
            "video",
        )
        return any(marker in model for marker in multimodal_markers)

    @property
    def uses_multimodal_gemini_embeddings(self) -> bool:
        return not self.uses_openrouter and self.gemini_embedding_model.startswith("gemini-embedding-2")

    @model_validator(mode="after")
    def normalize_openrouter_settings(self) -> "Settings":
        if not self.uses_openrouter:
            return self

        if self.gemini_classifier_model.startswith("gemini") and "/" not in self.gemini_classifier_model:
            self.gemini_classifier_model = f"google/{self.gemini_classifier_model}"

        if self.gemini_generation_model.startswith("gemini") and "/" not in self.gemini_generation_model:
            self.gemini_generation_model = f"google/{self.gemini_generation_model}"

        if self.gemini_embedding_model == "text-embedding-004":
            self.gemini_embedding_model = "openai/text-embedding-3-small"
            if self.gemini_embedding_dimension == 768:
                self.gemini_embedding_dimension = 1536

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
