from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import Settings
from app.models import ContentChunk, IntentResponse


class FirecrawlClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://api.firecrawl.dev"

    async def scout_topic(self, *, topic: str, intent: IntentResponse) -> list[ContentChunk]:
        discovered: list[ContentChunk] = []
        seen_urls: set[str] = set()

        for query in intent.search_queries:
            try:
                search_results = await self.search(query)
            except Exception as exc:
                discovered.append(
                    ContentChunk(
                        content=f"Firecrawl search failed for query '{query}': {exc}",
                        source="firecrawl_error",
                        topic=topic,
                        intent=intent.intent,
                        metadata={"query": query, "stage": "search"},
                    )
                )
                continue

            for result in search_results[: self.settings.firecrawl_search_limit]:
                url = self._normalize_url(result.get("url"))
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                try:
                    scraped = await self.scrape(url)
                    content = (
                        scraped.get("markdown")
                        or scraped.get("summary")
                        or result.get("description")
                        or result.get("title")
                    )
                except Exception as exc:
                    fallback = result.get("description") or result.get("title")
                    if fallback:
                        discovered.append(
                            ContentChunk(
                                content=fallback,
                                source="firecrawl_search_fallback",
                                topic=topic,
                                intent=intent.intent,
                                metadata={
                                    "query": query,
                                    "url": url,
                                    "title": result.get("title"),
                                    "stage": "scrape_fallback",
                                    "warning": str(exc),
                                },
                            )
                        )
                    else:
                        discovered.append(
                            ContentChunk(
                                content=f"Firecrawl scrape failed for {url}: {exc}",
                                source="firecrawl_error",
                                topic=topic,
                                intent=intent.intent,
                                metadata={
                                    "query": query,
                                    "url": url,
                                    "title": result.get("title"),
                                    "stage": "scrape",
                                },
                            )
                        )
                    continue

                if not content:
                    continue
                discovered.append(
                    ContentChunk(
                        content=content,
                        source="firecrawl",
                        topic=topic,
                        intent=intent.intent,
                        metadata={
                            "query": query,
                            "url": url,
                            "title": result.get("title"),
                        },
                    )
                )

        return discovered

    async def search(self, query: str) -> list[dict[str, Any]]:
        data = await self._post_json(
            "/v2/search",
            {
                "query": query,
                "limit": self.settings.firecrawl_search_limit,
                "sources": [{"type": "web"}],
            },
        )
        results = data.get("data") or data.get("results") or []
        if isinstance(results, dict):
            return results.get("web", [])
        return results

    async def scrape(self, url: str) -> dict[str, Any]:
        normalized_url = self._normalize_url(url)
        data = await self._post_json(
            "/v1/scrape",
            {
                "url": normalized_url,
                "formats": ["markdown"],
            },
        )
        return data.get("data", data)

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.firecrawl_api_key:
            raise RuntimeError("FIRECRAWL_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {self.settings.firecrawl_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=90.0) as client:
            response = await client.post(path, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Firecrawl request failed with status {response.status_code}: {response.text}"
                ) from exc
            return response.json()

    @staticmethod
    def _normalize_url(url: str | None) -> str | None:
        if not url:
            return None
        if urlparse(url).scheme:
            return url
        return f"https://{url.lstrip('/')}"
