"""
BugLens Tavily Research Service.
Handles external technical research using Tavily Search API.
Limits results to 3-5 high quality sources and safely falls back if API key is unconfigured or search fails.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from models.schemas import ResearchSource, ResearchResult

logger = logging.getLogger(__name__)


class TavilyService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("TAVILY_API_KEY is not configured in the environment.")
            from tavily import TavilyClient
            self._client = TavilyClient(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def search_technical_context(self, query: str, max_results: int = 4) -> ResearchResult:
        """
        Executes a targeted technical search query through Tavily.
        Returns a structured ResearchResult with 3-5 extracted sources.
        """
        if not self.is_configured():
            logger.info("Tavily API key is not configured. Falling back gracefully.")
            return ResearchResult(
                queries=[query],
                sources=[],
                status="unavailable"
            )

        try:
            # Tavily python SDK search
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=False
            )

            raw_results = response.get("results", []) if isinstance(response, dict) else []
            sources: List[ResearchSource] = []

            for item in raw_results[:max_results]:
                url = item.get("url", "")
                title = item.get("title", "Technical Documentation")
                content = item.get("content", "")
                snippet = content[:300] + ("..." if len(content) > 300 else "")

                domain = "external"
                if url:
                    try:
                        domain = urlparse(url).netloc
                    except Exception:
                        domain = "external"

                sources.append(ResearchSource(
                    title=title,
                    url=url,
                    snippet=snippet,
                    domain=domain,
                    technical_relevance="Relevant documentation / resolution pattern"
                ))

            return ResearchResult(
                queries=[query],
                sources=sources,
                status="completed" if sources else "unavailable"
            )

        except Exception as e:
            logger.warning("Tavily search failed for query '%s': %s", query, str(e))
            return ResearchResult(
                queries=[query],
                sources=[],
                status="unavailable"
            )
