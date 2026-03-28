from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, UploadFile

from app.clients.firecrawl import FirecrawlClient
from app.clients.gemini import GeminiClient
from app.clients.qdrant_store import QdrantStore
from app.config import get_settings
from app.models import IntakeResponse, SpecialistContextResponse
from app.services.pipeline import PresentationPipeline
from app.services.sensory import SensoryService

settings = get_settings()
gemini_client = GeminiClient(settings)
firecrawl_client = FirecrawlClient(settings)
qdrant_store = QdrantStore(settings)
sensory_service = SensoryService(
    settings=settings,
    gemini_client=gemini_client,
    firecrawl_client=firecrawl_client,
)
pipeline = PresentationPipeline(
    gemini_client=gemini_client,
    firecrawl_client=firecrawl_client,
    qdrant_store=qdrant_store,
    sensory_service=sensory_service,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    qdrant_store.ensure_collection()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/presentations/intake", response_model=IntakeResponse)
async def intake_presentation(
    topic: Annotated[str, Form(...)],
    allow_web_search: Annotated[bool, Form(False)] = False,
    files: Annotated[list[UploadFile] | None, File(default=None)] = None,
    resource_urls: Annotated[list[str] | None, Form(default=None)] = None,
) -> IntakeResponse:
    return await pipeline.intake(
        topic=topic,
        files=files,
        resource_urls=resource_urls,
        allow_web_search=allow_web_search,
    )


@app.get("/api/presentations/specialist-context", response_model=SpecialistContextResponse)
async def specialist_context(
    query: str,
    intent: Literal["technical", "business", "academic", "creative"],
) -> SpecialistContextResponse:
    results = await pipeline.specialist_context(query=query, intent=intent)
    return SpecialistContextResponse(query=query, intent=intent, results=results)
