from functools import lru_cache

from pydantic import Field, field_validator
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
    specialist_max_tokens: int = Field(default=4096)
    deck_blueprint_max_tokens: int = Field(default=5200)
    challenger_max_tokens: int = Field(default=2600)
    structured_repair_token_buffer: int = Field(default=2400)
    gemini_timeout_seconds: float = Field(default=180.0)

    firecrawl_search_limit: int = Field(default=3)
    max_text_chars: int = Field(default=3500)
    text_chunk_overlap: int = Field(default=400)
    pdf_pages_per_chunk: int = Field(default=6)
    inline_media_limit_bytes: int = Field(default=20_000_000)
    generated_presentations_dir: str = Field(default="generated_presentations")

    @field_validator("qdrant_api_key", mode="before")
    @classmethod
    def empty_qdrant_api_key_to_none(cls, value: str | None):
        if value in ("", None):
            return None
        return value

    @property
    def uses_multimodal_gemini_embeddings(self) -> bool:
        return self.gemini_embedding_model.startswith("gemini-embedding-2")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
