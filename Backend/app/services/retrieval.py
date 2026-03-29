from __future__ import annotations

from app.clients.gemini import GeminiClient
from app.clients.qdrant_store import QdrantStore
from app.models import RetrievalResult


async def get_specialist_context(
    query: str,
    intent: str,
    *,
    gemini_client: GeminiClient,
    qdrant_store: QdrantStore,
    topic: str | None = None,
) -> list[RetrievalResult]:
    vector = await gemini_client.embed_text(query, task_type="RETRIEVAL_QUERY")
    return qdrant_store.search(vector=vector, intent=intent, topic=topic, limit=10)
