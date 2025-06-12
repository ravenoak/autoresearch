"""Utility functions for query generation and external lookups."""
from __future__ import annotations

import os
from typing import Callable, List, Dict, Any
import requests

from .config import get_config

from .logging_utils import get_logger
from .cache import get_cached_results, cache_results

log = get_logger(__name__)


class Search:
    """Search utilities."""

    # Registry mapping backend name to callable
    backends: Dict[str, Callable[[str, int], List[Dict[str, str]]]] = {}

    @classmethod
    def register_backend(cls, name: str) -> Callable[[Callable[[str, int], List[Dict[str, str]]]], Callable[[str, int], List[Dict[str, str]]]]:
        """Decorator to register a search backend."""

        def decorator(func: Callable[[str, int], List[Dict[str, str]]]) -> Callable[[str, int], List[Dict[str, str]]]:
            cls.backends[name] = func
            return func

        return decorator

    @staticmethod
    def generate_queries(query: str) -> List[str]:
        """Return a list of search queries derived from the user query."""
        return [query]

    @staticmethod
    def external_lookup(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform an external search using configured backends."""
        cached = get_cached_results(query)
        if cached:
            return cached[:max_results]

        cfg = get_config()

        results = []
        for name in cfg.search_backends:
            backend = Search.backends.get(name)
            if not backend:
                log.warning(f"Unknown search backend '{name}'")
                continue
            try:
                results.extend(backend(query, max_results))
            except Exception as exc:  # pragma: no cover - network errors
                log.warning(f"{name} search failed: {exc}")

        if results:
            cache_results(query, results)
            return results

        # Fallback results when all backends fail
        return [
            {"title": f"Result {i+1} for {query}", "url": ""} for i in range(max_results)
        ]


@Search.register_backend("duckduckgo")
def _duckduckgo_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve results from the DuckDuckGo API."""
    url = "https://api.duckduckgo.com/"
    params: Dict[str, str] = {
        "q": query,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
    }
    response = requests.get(url, params=params, timeout=5)
    data = response.json()
    results: List[Dict[str, str]] = []
    for item in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(item, dict):
            results.append({
                "title": item.get("Text", ""),
                "url": item.get("FirstURL", ""),
            })
    return results


@Search.register_backend("serper")
def _serper_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve results from the Serper API."""
    api_key = os.getenv("SERPER_API_KEY", "")
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key}
    response = requests.post(url, json={"q": query}, headers=headers, timeout=5)
    data = response.json()
    results: List[Dict[str, str]] = []
    for item in data.get("organic", [])[:max_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
        })
    return results

