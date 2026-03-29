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
    try:
        vector = await gemini_client.embed_text(query, task_type="RETRIEVAL_QUERY")
        return qdrant_store.search(vector=vector, intent=intent, topic=topic, limit=10)
    except RuntimeError as exc:
        if topic and _is_quota_error(exc):
            return qdrant_store.list_topic_memories(topic=topic, intent=intent, limit=10)
        raise


def _is_quota_error(error: RuntimeError) -> bool:
    message = str(error)
    return "429" in message or "RESOURCE_EXHAUSTED" in message
