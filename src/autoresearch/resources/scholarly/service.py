"""High level orchestration for scholarly search and caching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, MutableMapping, Sequence

from ...storage import StorageManager
from ...storage_utils import NamespaceTokens
from .cache import ScholarlyCache
from .fetchers import ArxivFetcher, HuggingFacePapersFetcher, ScholarlyFetcher
from .models import CachedPaper, PaperDocument, PaperMetadata


@dataclass(frozen=True)
class SearchResult:
    """Container pairing provider labels with metadata lists."""

    provider: str
    results: tuple[PaperMetadata, ...]


class ScholarlyService:
    """Coordinate scholarly fetchers and caching utilities."""

    def __init__(self, cache: ScholarlyCache | None = None) -> None:
        self._cache = cache or ScholarlyCache()
        self._fetchers: MutableMapping[str, ScholarlyFetcher] = {}

    def _get_fetcher(self, provider: str) -> ScholarlyFetcher:
        key = provider.lower()
        if key not in self._fetchers:
            if key == "arxiv":
                self._fetchers[key] = ArxivFetcher()
            elif key in {"hf", "huggingface", "huggingface-papers"}:
                self._fetchers[key] = HuggingFacePapersFetcher()
            else:  # pragma: no cover - defensive guard
                raise ValueError(f"Unknown scholarly provider '{provider}'")
        return self._fetchers[key]

    def search(
        self,
        query: str,
        *,
        providers: Iterable[str] | None = None,
        limit: int = 10,
        namespace: NamespaceTokens | dict[str, str] | str | None = None,
    ) -> tuple[SearchResult, ...]:
        """Return results from each provider for ``query``."""

        provider_list = list(providers or ["arxiv", "huggingface"])
        results: list[SearchResult] = []
        resolved_namespace: str | None = None
        if namespace is not None:
            resolved_namespace = StorageManager._resolve_namespace_label(namespace)
        for provider in provider_list:
            fetcher = self._get_fetcher(provider)
            metadata = tuple(
                fetcher.search(query, limit=limit, namespace=resolved_namespace)
            )
            if resolved_namespace is not None:
                metadata = tuple(item.with_namespace(resolved_namespace) for item in metadata)
            results.append(SearchResult(provider=fetcher.provider, results=metadata))
        return tuple(results)

    def ingest(
        self,
        provider: str,
        identifier: str,
        *,
        namespace: NamespaceTokens | dict[str, str] | str,
        embedding: Sequence[float] | None = None,
        content_type: str = "text/plain",
    ) -> CachedPaper:
        """Fetch and cache a scholarly paper."""

        fetcher = self._get_fetcher(provider)
        document: PaperDocument = fetcher.fetch(identifier)
        if embedding is not None:
            document.embedding = embedding
        return self._cache.cache_document(document, namespace=namespace, content_type=content_type)

    def list_cached(
        self,
        *,
        namespace: str | None = None,
        provider: str | None = None,
    ) -> list[CachedPaper]:
        """Return cached papers filtered by optional parameters."""

        return self._cache.list_cached(namespace=namespace, provider=provider)

    def get_cached(self, namespace: str, provider: str, paper_id: str) -> CachedPaper:
        """Return a cached paper for downstream use."""

        return self._cache.get_cached(namespace, provider, paper_id)


__all__ = ["ScholarlyService", "SearchResult"]
