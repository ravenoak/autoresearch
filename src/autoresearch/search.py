"""Utility functions for query generation and external lookups."""
from typing import List, Dict
import requests

from .logging_utils import get_logger

log = get_logger(__name__)


class Search:
    """Search utilities."""

    @staticmethod
    def generate_queries(query: str) -> List[str]:
        """Return a list of search queries derived from the user query."""
        return [query]

    @staticmethod
    def external_lookup(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Perform an external search and return simplified results."""
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            results = []
            for item in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(item, dict):
                    results.append({
                        "title": item.get("Text", ""),
                        "url": item.get("FirstURL", ""),
                    })
            if results:
                return results
        except Exception as exc:  # pragma: no cover - network errors
            log.warning(f"External search failed: {exc}")
        return [
            {"title": f"Result {i+1} for {query}", "url": ""} for i in range(max_results)
        ]

