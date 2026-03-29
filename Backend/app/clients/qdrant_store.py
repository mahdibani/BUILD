from __future__ import annotations

from collections import Counter
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.config import Settings
from app.models import ContentChunk, RetrievalResult


class QdrantStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )

    def ensure_collection(self) -> None:
        existing = {collection.name for collection in self.client.get_collections().collections}
        if self.settings.qdrant_collection in existing:
            collection_info = self.client.get_collection(self.settings.qdrant_collection)
            vectors_config = collection_info.config.params.vectors
            current_size = getattr(vectors_config, "size", None)
            if current_size and current_size != self.settings.gemini_embedding_dimension:
                raise RuntimeError(
                    "Qdrant collection vector size does not match the configured embedding dimension. "
                    f"Collection '{self.settings.qdrant_collection}' is size {current_size}, "
                    f"but the backend is configured for {self.settings.gemini_embedding_dimension}. "
                    "Delete and recreate the collection or reset local Qdrant storage."
                )
            return

        self.client.create_collection(
            collection_name=self.settings.qdrant_collection,
            vectors_config=qdrant_models.VectorParams(
                size=self.settings.gemini_embedding_dimension,
                distance=qdrant_models.Distance.COSINE,
            ),
        )

    def upsert_chunks(self, chunks: list[ContentChunk], vectors: list[list[float]]) -> int:
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            points.append(
                qdrant_models.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={
                        "content": chunk.content,
                        "source": chunk.source,
                        "intent": chunk.intent,
                        "metadata": chunk.metadata,
                        "topic": chunk.topic,
                    },
                )
            )

        if not points:
            return 0

        self.client.upsert(collection_name=self.settings.qdrant_collection, points=points)
        return len(points)

    def breakdown_by_source(self, chunks: list[ContentChunk]) -> dict[str, int]:
        return dict(Counter(chunk.source for chunk in chunks))

    def search(
        self,
        vector: list[float],
        intent: str,
        limit: int = 10,
        topic: str | None = None,
    ) -> list[RetrievalResult]:
        must_conditions = [
            qdrant_models.FieldCondition(
                key="intent",
                match=qdrant_models.MatchValue(value=intent),
            )
        ]
        if topic:
            must_conditions.append(
                qdrant_models.FieldCondition(
                    key="topic",
                    match=qdrant_models.MatchValue(value=topic),
                )
            )

        results = self.client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=vector,
            query_filter=qdrant_models.Filter(must=must_conditions),
            limit=limit,
            with_payload=True,
        )

        return [
            RetrievalResult(
                id=str(point.id),
                score=point.score,
                content=point.payload.get("content", ""),
                source=point.payload.get("source", ""),
                intent=point.payload.get("intent", ""),
                metadata=point.payload.get("metadata", {}),
            )
            for point in results
        ]

    def list_topic_memories(
        self,
        *,
        topic: str,
        intent: str,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        records, _ = self.client.scroll(
            collection_name=self.settings.qdrant_collection,
            scroll_filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="intent",
                        match=qdrant_models.MatchValue(value=intent),
                    ),
                    qdrant_models.FieldCondition(
                        key="topic",
                        match=qdrant_models.MatchValue(value=topic),
                    ),
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return [
            RetrievalResult(
                id=str(record.id),
                score=float(limit - index),
                content=(record.payload or {}).get("content", ""),
                source=(record.payload or {}).get("source", ""),
                intent=(record.payload or {}).get("intent", ""),
                metadata=(record.payload or {}).get("metadata", {}),
            )
            for index, record in enumerate(records, start=1)
        ]
