from __future__ import annotations

from io import BytesIO
from urllib.parse import parse_qs, urlparse

from pypdf import PdfReader, PdfWriter


def chunk_text(text: str, max_chars: int, overlap: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    if len(normalized) <= max_chars:
        return [normalized]

    chunks: list[str] = []
    start = 0
    step = max(max_chars - overlap, 1)
    while start < len(normalized):
        chunks.append(normalized[start : start + max_chars])
        start += step
    return chunks


def chunk_pdf_bytes(pdf_bytes: bytes, pages_per_chunk: int) -> list[tuple[str, dict[str, int]]]:
    reader = PdfReader(BytesIO(pdf_bytes))
    chunks: list[tuple[str, dict[str, int]]] = []

    for start_page in range(0, len(reader.pages), pages_per_chunk):
        end_page = min(start_page + pages_per_chunk, len(reader.pages))
        pages_text = []
        for page_index in range(start_page, end_page):
            extracted = reader.pages[page_index].extract_text() or ""
            if extracted.strip():
                pages_text.append(f"[Page {page_index + 1}] {extracted.strip()}")

        if pages_text:
            chunks.append(
                (
                    "\n\n".join(pages_text),
                    {"page_start": start_page + 1, "page_end": end_page},
                )
            )

    return chunks


def chunk_pdf_documents(
    pdf_bytes: bytes,
    pages_per_chunk: int,
) -> list[tuple[bytes, str, dict[str, int]]]:
    reader = PdfReader(BytesIO(pdf_bytes))
    chunks: list[tuple[bytes, str, dict[str, int]]] = []

    for start_page in range(0, len(reader.pages), pages_per_chunk):
        end_page = min(start_page + pages_per_chunk, len(reader.pages))
        writer = PdfWriter()
        pages_text = []

        for page_index in range(start_page, end_page):
            writer.add_page(reader.pages[page_index])
            extracted = reader.pages[page_index].extract_text() or ""
            if extracted.strip():
                pages_text.append(f"[Page {page_index + 1}] {extracted.strip()}")

        pdf_buffer = BytesIO()
        writer.write(pdf_buffer)
        chunks.append(
            (
                pdf_buffer.getvalue(),
                "\n\n".join(pages_text) or f"PDF pages {start_page + 1}-{end_page}",
                {"page_start": start_page + 1, "page_end": end_page},
            )
        )

    return chunks


def extract_youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    hostname = parsed.netloc.lower()
    if "youtu.be" in hostname:
        return parsed.path.strip("/") or None
    if "youtube.com" in hostname:
        query = parse_qs(parsed.query)
        video_id = query.get("v", [None])[0]
        if video_id:
            return video_id
        parts = [part for part in parsed.path.split("/") if part]
        if "shorts" in parts and parts[-1]:
            return parts[-1]
    return None
