from __future__ import annotations

from typing import Any

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
            search_results = await self.search(query)
            for result in search_results[: self.settings.firecrawl_search_limit]:
                url = result.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                scraped = await self.scrape(url)
                content = scraped.get("markdown") or result.get("description") or result.get("title")
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
        data = await self._post_json(
            "/v1/scrape",
            {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "parsePDF": True,
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
            response.raise_for_status()
            return response.json()
