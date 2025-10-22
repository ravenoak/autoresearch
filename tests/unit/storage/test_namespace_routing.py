from pathlib import Path
from typing import Any

import pytest

from autoresearch.cache import SearchCache
from autoresearch.config.models import ConfigModel
from autoresearch.errors import StorageError
from autoresearch.resources.scholarly.cache import ScholarlyCache
from autoresearch.resources.scholarly.fetchers import ScholarlyFetcher
from autoresearch.resources.scholarly.models import PaperDocument, PaperIdentifier, PaperMetadata
from autoresearch.resources.scholarly.service import ScholarlyService
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.storage_utils import (
    NamespaceTokens,
    resolve_namespace,
    validate_namespace_routes,
)


def test_resolve_namespace_prefers_project_token():
    tokens = NamespaceTokens(session="sess", workspace="work", project="proj")
    routes = {"session": "workspace", "workspace": "project"}
    assert resolve_namespace(tokens, routes, default_namespace="default") == "proj"


def test_resolve_namespace_falls_back_to_workspace():
    tokens = NamespaceTokens(session="sess", workspace="work", project=None)
    routes = {"session": "workspace", "workspace": "self"}
    assert resolve_namespace(tokens, routes, default_namespace="default") == "work"


def test_validate_namespace_routes_detects_cycle():
    with pytest.raises(StorageError):
        validate_namespace_routes({"session": "workspace", "workspace": "session"})


def test_search_initialises_namespace_from_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ConfigModel()
    search_cfg = cfg.search.model_copy(update={"cache_namespace": {"workspace": "demo"}})
    cfg = cfg.model_copy(update={"search": search_cfg})

    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    search = Search(cache=SearchCache())

    assert search._cache_namespace == "demo"
    assert getattr(search.cache, "namespace", search.cache._namespace) == "demo"  # type: ignore[attr-defined]


def test_scholarly_service_search_respects_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubFetcher(ScholarlyFetcher):
        provider = "stub"

        def __init__(self) -> None:
            self.last_namespace: str | None = None

        def search(
            self,
            query: str,
            limit: int = 10,
            *,
            namespace: str | None = None,
        ) -> tuple[PaperMetadata, ...]:
            self.last_namespace = namespace
            identifier = PaperIdentifier(provider=self.provider, value="id", namespace=namespace or "__public__")
            metadata = PaperMetadata(identifier=identifier, title="stub", abstract="stub")
            return (metadata,)

        def fetch(self, identifier: str) -> PaperDocument:
            raise NotImplementedError

    service = ScholarlyService()
    stub = StubFetcher()
    service._fetchers["stub"] = stub

    results = service.search("topic", providers=["stub"], namespace={"workspace": "audit"})

    assert stub.last_namespace == "audit"
    assert results[0].results[0].identifier.namespace == "audit"


def test_scholarly_cache_handles_namespace_tokens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(StorageManager, "setup", staticmethod(lambda: None))

    saved: list[dict[str, Any]] = []

    def _fake_save(payload: dict[str, Any]) -> dict[str, Any]:
        saved.append(payload)
        return payload

    list_calls: dict[str, Any] = {}

    def _fake_list(namespace: Any = None, provider: str | None = None) -> list[dict[str, Any]]:
        list_calls["list_namespace"] = namespace
        return list(saved)

    def _fake_get(namespace: Any, provider: str, paper_id: str) -> dict[str, Any]:
        list_calls["get_namespace"] = namespace
        return saved[0]

    monkeypatch.setattr(StorageManager, "save_scholarly_paper", staticmethod(_fake_save))
    monkeypatch.setattr(StorageManager, "list_scholarly_papers", staticmethod(_fake_list))
    monkeypatch.setattr(StorageManager, "get_scholarly_paper", staticmethod(_fake_get))

    cache = ScholarlyCache(base_dir=tmp_path)
    identifier = PaperIdentifier(provider="stub", value="id", namespace="__public__")
    metadata = PaperMetadata(identifier=identifier, title="stub", abstract="body")
    document = PaperDocument(metadata=metadata, body="full text")

    cached = cache.cache_document(document, namespace={"workspace": "audit"})

    assert cached.metadata.identifier.namespace == "audit"
    assert saved[0]["namespace"] == "audit"
    assert saved[0]["metadata"]["identifier"]["namespace"] == "audit"

    listed = cache.list_cached(namespace={"workspace": "audit"})
    assert list_calls["list_namespace"] == {"workspace": "audit"}
    assert listed[0].metadata.identifier.namespace == "audit"

    retrieved = cache.get_cached({"workspace": "audit"}, "stub", "id")
    assert list_calls["get_namespace"] == {"workspace": "audit"}
    assert retrieved.metadata.identifier.namespace == "audit"
