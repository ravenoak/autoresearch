import sys
from urllib.parse import quote_plus

import pytest
import requests

from autoresearch import distributed
from autoresearch.errors import SearchError
from autoresearch.search import Search

from .typing_helpers import make_runtime_config, make_search_config, make_storage_config


def _make_cfg(backends):
    search_cfg = make_search_config(
        backends=backends,
        hybrid_query=False,
        use_semantic_similarity=False,
        embedding_backends=[],
        context_aware_enabled=False,
        max_workers=1,
    )
    return make_runtime_config(
        search=search_cfg,
        loops=1,
        distributed=False,
        distributed_enabled=False,
        storage=make_storage_config(duckdb_path=":memory:"),
    )


def test_external_lookup_network_failure(monkeypatch):
    def failing_backend(query, max_results):
        raise requests.exceptions.RequestException("fail")

    with Search.temporary_state() as search:
        search.backends["fail"] = failing_backend
        cfg = _make_cfg(["fail"])
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
        with pytest.raises(SearchError) as exc:
            search.external_lookup("q", max_results=1)
        assert isinstance(exc.value.__cause__, requests.exceptions.RequestException)


def test_external_lookup_unknown_backend(monkeypatch):
    with Search.temporary_state() as search:
        cfg = _make_cfg(["missing"])
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
        search.backends.pop("missing", None)
        monkeypatch.setattr(
            search.cache,
            "get_cached_results",
            lambda *_, **__: (_ for _ in ()).throw(
                AssertionError("cache lookup should not occur for unknown backends")
            ),
        )
        with pytest.raises(SearchError):
            search.external_lookup("q", max_results=1)


def test_external_lookup_fallback(monkeypatch):
    cfg = _make_cfg([])
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    results = Search.external_lookup("q", max_results=2)
    assert len(results) == 2
    assert results[0]["title"] == "Result 1 for q"
    encoded = quote_plus("q")
    assert results[0]["url"] == f"https://example.invalid/search?q={encoded}&rank=1", (
        "If fallback URLs drift, how would we detect nondeterministic cache placeholders?"
    )
    assert results[0]["canonical_url"] == (
        f"https://example.invalid/search?q={encoded}&rank=1"
    ), "Canonical URLs document deterministic fallback cache entries."
    assert results[0]["backend"] == "__fallback__", (
        "When the fallback backend label changes, who will warn us about cache coverage gaps?"
    )
    repeat = Search.external_lookup("q", max_results=2)
    assert repeat == results, (
        "If deterministic placeholders vanish, what signal would alert us to fallback regressions?"
    )


def test_external_lookup_fallback_templated_query(monkeypatch):
    cfg = _make_cfg([])
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = {"text": "value {placeholder}"}
    results = Search.external_lookup(query, max_results=1)
    assert len(results) == 1
    encoded = quote_plus("value {placeholder}")
    expected_url = f"https://example.invalid/search?q={encoded}&rank=1"
    record = results[0]
    assert record["title"] == "Result 1 for value {placeholder}"
    assert record["url"] == expected_url
    assert record["canonical_url"] == expected_url
    assert record["backend"] == "__fallback__"
    repeat = Search.external_lookup(query, max_results=1)
    assert repeat == results


def test_get_message_broker_invalid():
    with pytest.raises(ValueError):
        distributed.get_message_broker("unknown")


@pytest.mark.requires_distributed
@pytest.mark.redis
def test_redis_broker_init_failure(monkeypatch):
    class DummyRedis:
        @staticmethod
        def from_url(url):
            raise ConnectionError("bad url")

    monkeypatch.setitem(sys.modules, "redis", type("RedisModule", (), {"Redis": DummyRedis}))
    with pytest.raises(ConnectionError):
        distributed.RedisBroker("redis://bad")
