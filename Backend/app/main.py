from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.clients.firecrawl import FirecrawlClient
from app.clients.gemini import GeminiClient
from app.clients.qdrant_store import QdrantStore
from app.config import get_settings
from app.models import (
    GeneratePresentationRequest,
    GeneratedPresentationResponse,
    IntakeResponse,
    SpecialistContextResponse,
)
from app.services.presentation_agents import PresentationAgentService
from app.services.pipeline import PresentationPipeline
from app.services.pptx_builder import PptxDeckBuilder
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
agent_service = PresentationAgentService(gemini_client=gemini_client, settings=settings)
pptx_builder = PptxDeckBuilder(
    output_dir=Path(__file__).resolve().parents[1] / settings.generated_presentations_dir,
    backgrounds_dir=Path(__file__).resolve().parents[2] / "images",
)
pipeline = PresentationPipeline(
    gemini_client=gemini_client,
    firecrawl_client=firecrawl_client,
    qdrant_store=qdrant_store,
    sensory_service=sensory_service,
    agent_service=agent_service,
    pptx_builder=pptx_builder,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/presentations/intake", response_model=IntakeResponse)
async def intake_presentation(
    topic: Annotated[str, Form(...)],
    allow_web_search: Annotated[bool, Form()] = False,
    files: Annotated[list[UploadFile] | None, File()] = None,
    resource_urls: Annotated[list[str] | None, Form()] = None,
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
    topic: str | None = None,
) -> SpecialistContextResponse:
    results = await pipeline.specialist_context(query=query, intent=intent, topic=topic)
    return SpecialistContextResponse(query=query, intent=intent, results=results)


@app.post("/api/presentations/generate", response_model=GeneratedPresentationResponse)
async def generate_presentation(
    request: GeneratePresentationRequest,
) -> GeneratedPresentationResponse:
    return await pipeline.generate_presentation(
        topic=request.topic,
        intent=request.intent,
        include_challenger=request.include_challenger,
        auto_research=request.auto_research,
    )


@app.get("/api/presentations/download/{filename}")
async def download_presentation(filename: str) -> FileResponse:
    target = (Path(__file__).resolve().parents[1] / settings.generated_presentations_dir / filename).resolve()
    base_dir = (Path(__file__).resolve().parents[1] / settings.generated_presentations_dir).resolve()
    if base_dir not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not target.exists():
        raise HTTPException(status_code=404, detail="Presentation file not found")
    return FileResponse(target, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
