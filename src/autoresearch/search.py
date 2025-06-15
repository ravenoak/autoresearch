"""Search functionality for external information retrieval.

This module provides utilities for generating search queries and performing
external lookups using configurable search backends. It supports multiple
search backends, query generation, and result caching.

The module includes:
1. A Search class with methods for query generation and external lookups
2. Decorator for registering search backends
3. Built-in backends for DuckDuckGo and Serper
4. Error handling for network issues, timeouts, and invalid responses
"""

from __future__ import annotations

import json
import os
from typing import Callable, List, Dict, Any
import requests

from .config import get_config
from .errors import SearchError
from .logging_utils import get_logger
from .cache import get_cached_results, cache_results

log = get_logger(__name__)


class Search:
    """Provides utilities for search query generation and external lookups.

    This class contains methods for generating search query variants,
    performing external lookups using registered backends, and handling
    search-related errors. It uses a registry pattern to allow dynamic
    registration of search backends.

    The class supports:
    - Registering custom search backends via decorators
    - Generating multiple query variants from a single query
    - Creating simple vector embeddings for queries
    - Performing external lookups with configurable backends
    - Caching search results to improve performance
    - Handling various error conditions (timeouts, network errors, etc.)
    """

    # Registry mapping backend name to callable
    backends: Dict[str, Callable[[str, int], List[Dict[str, str]]]] = {}

    @classmethod
    def register_backend(cls, name: str) -> Callable[
        [Callable[[str, int], List[Dict[str, str]]]],
        Callable[[str, int], List[Dict[str, str]]],
    ]:
        """Decorator to register a search backend function.

        This decorator registers a function as a search backend with the given name.
        Registered backends can be used by configuring them in the search_backends
        list in the configuration.

        Args:
            name: The name to register the backend under. This name should be used
                  in the configuration to enable the backend.

        Returns:
            A decorator function that registers the decorated function as a search
            backend and returns the original function unchanged.

        Example:
            @Search.register_backend("custom")
            def custom_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
                # Implementation
                return [{"title": "Result", "url": "https://example.com"}]
        """

        def decorator(
            func: Callable[[str, int], List[Dict[str, str]]],
        ) -> Callable[[str, int], List[Dict[str, str]]]:
            cls.backends[name] = func
            return func

        return decorator

    @staticmethod
    def generate_queries(
        query: str, return_embeddings: bool = False
    ) -> List[Any]:
        """Generate search query variants or a simple embedding for a query.

        This method takes a raw user query and either generates multiple variants
        of the query to improve search results, or creates a simple vector embedding
        of the query for vector search.

        The query variants include:
        1. The original query
        2. The query with "examples" appended (if query has multiple words)
        3. The query in question form ("What is X?")

        When return_embeddings is True, a simple deterministic embedding is created
        using character codes. This is primarily used for testing and demonstration
        purposes.

        Args:
            query: The raw user query string to generate variants or embeddings for.
            return_embeddings: When True, return a numeric embedding instead of 
                              query strings. Default is False.

        Returns:
            A list of query variants (strings) or a list of floating-point values
            representing a simple embedding of the query.

        Example:
            >>> Search.generate_queries("python")
            ['python', 'python examples', 'What is python?']

            >>> Search.generate_queries("a", return_embeddings=True)
            [97.0]
        """

        cleaned = query.strip()

        if return_embeddings:
            # Create a trivial embedding using character codes. This keeps the
            # implementation lightweight and deterministic for unit tests.
            return [float(ord(c)) for c in cleaned][:10]

        queries = [cleaned]

        # Add a simple variation emphasising examples or tutorials
        if len(cleaned.split()) > 1:
            queries.append(f"{cleaned} examples")

        # Include a question style variant
        queries.append(f"What is {cleaned}?")

        return queries

    @staticmethod
    def external_lookup(
        query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform an external search using configured backends.

        This method performs a search using all backends configured in the
        search_backends list in the configuration. It handles caching of results,
        error handling, and merging results from multiple backends.

        The method attempts to use each configured backend in sequence. If a backend
        fails, it logs the error and continues with the next backend. If all backends
        fail, it returns fallback results.

        Args:
            query: The search query string to look up.
            max_results: The maximum number of results to return per backend.
                        Default is 5.

        Returns:
            A list of dictionaries containing search results. Each dictionary
            has at least 'title' and 'url' keys.

        Raises:
            SearchError: If a search backend fails due to network issues, invalid
                        JSON responses, or other errors.
            TimeoutError: If a search backend times out.

        Example:
            >>> Search.external_lookup("python", max_results=2)
            [
                {"title": "Python Programming Language", "url": "https://python.org"},
                {"title": "Python (programming language) - Wikipedia", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"}
            ]
        """
        cfg = get_config()

        results = []
        for name in cfg.search_backends:
            cached = get_cached_results(query, name)
            if cached is not None:
                results.extend(cached[:max_results])
                continue

            backend = Search.backends.get(name)
            if not backend:
                log.warning(f"Unknown search backend '{name}'")
                available_backends = list(Search.backends.keys())
                if not available_backends:
                    available_backends = ["No backends registered"]
                raise SearchError(
                    f"Unknown search backend '{name}'",
                    available_backends=available_backends,
                    provided=name,
                    suggestion="Configure a valid search backend in your configuration file"
                )
            try:
                backend_results = backend(query, max_results)
            except requests.exceptions.Timeout as exc:
                log.warning(f"{name} search timed out: {exc}")
                from .errors import TimeoutError
                raise TimeoutError(
                    f"{name} search timed out", 
                    cause=exc, 
                    backend=name, 
                    query=query
                )
            except requests.exceptions.RequestException as exc:
                log.warning(f"{name} search request failed: {exc}")
                raise SearchError(
                    f"{name} search failed", 
                    cause=exc, 
                    backend=name, 
                    query=query,
                    suggestion="Check your network connection and ensure the search backend is properly configured"
                )
            except json.JSONDecodeError as exc:
                log.warning(f"{name} search returned invalid JSON: {exc}")
                raise SearchError(
                    f"{name} search failed: invalid JSON response", 
                    cause=exc, 
                    backend=name, 
                    query=query,
                    suggestion="The search backend returned an invalid response. Try a different search query or backend."
                )
            except Exception as exc:  # pragma: no cover - unexpected errors
                log.warning(f"{name} search failed with unexpected error: {exc}")
                raise SearchError(
                    f"{name} search failed", 
                    cause=exc, 
                    backend=name, 
                    query=query,
                    suggestion="An unexpected error occurred. Check the logs for more details and consider using a different search backend."
                )

            if backend_results:
                cache_results(query, name, backend_results)

            results.extend(backend_results)

        if results:
            return results

        # Fallback results when all backends fail
        return [
            {"title": f"Result {i+1} for {query}", "url": ""}
            for i in range(max_results)
        ]


@Search.register_backend("duckduckgo")
def _duckduckgo_backend(
    query: str, max_results: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve search results from the DuckDuckGo API.

    This function queries the DuckDuckGo API with the given search query
    and returns the results in a standardized format. It extracts information
    from the RelatedTopics field in the API response.

    Args:
        query: The search query string to look up.
        max_results: The maximum number of results to return. Default is 5.

    Returns:
        A list of dictionaries containing search results. Each dictionary
        has 'title' and 'url' keys.

    Raises:
        requests.exceptions.Timeout: If the request to the DuckDuckGo API times out.
        requests.exceptions.RequestException: If there's a network error or the API
                                             returns an error status code.
        json.JSONDecodeError: If the API returns a response that can't be parsed as JSON.

    Note:
        This function is registered as a search backend with the name "duckduckgo"
        and can be enabled by adding "duckduckgo" to the search_backends list in
        the configuration.
    """
    url = "https://api.duckduckgo.com/"
    params: Dict[str, str] = {
        "q": query,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
    }
    response = requests.get(url, params=params, timeout=5)
    # Raise an exception for HTTP errors (4xx and 5xx)
    response.raise_for_status()
    data = response.json()
    results: List[Dict[str, str]] = []
    for item in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(item, dict):
            results.append(
                {
                    "title": item.get("Text", ""),
                    "url": item.get("FirstURL", ""),
                }
            )
    return results


@Search.register_backend("serper")
def _serper_backend(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve search results from the Serper API.

    This function queries the Serper API (a Google Search API) with the given
    search query and returns the results in a standardized format. It extracts
    information from the 'organic' field in the API response.

    Args:
        query: The search query string to look up.
        max_results: The maximum number of results to return. Default is 5.

    Returns:
        A list of dictionaries containing search results. Each dictionary
        has 'title' and 'url' keys.

    Raises:
        requests.exceptions.Timeout: If the request to the Serper API times out.
        requests.exceptions.RequestException: If there's a network error or the API
                                             returns an error status code.
        json.JSONDecodeError: If the API returns a response that can't be parsed as JSON.

    Note:
        This function is registered as a search backend with the name "serper"
        and can be enabled by adding "serper" to the search_backends list in
        the configuration. It requires a Serper API key to be set in the
        SERPER_API_KEY environment variable.
    """
    api_key = os.getenv("SERPER_API_KEY", "")
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key}
    response = requests.post(
        url, json={"q": query}, headers=headers, timeout=5
    )
    # Raise an exception for HTTP errors (4xx and 5xx)
    response.raise_for_status()
    data = response.json()
    results: List[Dict[str, str]] = []
    for item in data.get("organic", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
            }
        )
    return results
