import sys
import types
import pytest
import requests

from autoresearch.errors import SearchError
from autoresearch.search import Search
from autoresearch import distributed


def _make_cfg(backends):
    search_cfg = types.SimpleNamespace(
        backends=backends,
        hybrid_query=False,
        context_aware=types.SimpleNamespace(enabled=False),
        max_workers=1,
    )
    return types.SimpleNamespace(search=search_cfg, loops=1, distributed=False, distributed_config=types.SimpleNamespace(enabled=False), storage=types.SimpleNamespace(duckdb_path=':memory:'))


def test_external_lookup_network_failure(monkeypatch):
    def failing_backend(query, max_results):
        raise requests.exceptions.RequestException('fail')

    Search.backends['fail'] = failing_backend
    cfg = _make_cfg(['fail'])
    monkeypatch.setattr('autoresearch.search.core.get_config', lambda: cfg)
    with pytest.raises(SearchError) as exc:
        Search.external_lookup('q', max_results=1)
    assert isinstance(exc.value.__cause__, requests.exceptions.RequestException)
    Search.backends.pop('fail')


def test_external_lookup_unknown_backend(monkeypatch):
    cfg = _make_cfg(['missing'])
    monkeypatch.setattr('autoresearch.search.core.get_config', lambda: cfg)
    Search.backends.pop('missing', None)
    orig = sys.modules.pop('pytest', None)
    try:
        with pytest.raises(SearchError):
            Search.external_lookup('q', max_results=1)
    finally:
        if orig is not None:
            sys.modules['pytest'] = orig


def test_external_lookup_fallback(monkeypatch):
    cfg = _make_cfg([])
    monkeypatch.setattr('autoresearch.search.core.get_config', lambda: cfg)
    results = Search.external_lookup('q', max_results=2)
    assert len(results) == 2
    assert results[0]['title'] == 'Result 1 for q'


def test_get_message_broker_invalid():
    with pytest.raises(ValueError):
        distributed.get_message_broker('unknown')


def test_redis_broker_init_failure(monkeypatch):
    class DummyRedis:
        @staticmethod
        def from_url(url):
            raise ConnectionError('bad url')
    monkeypatch.setitem(sys.modules, 'redis', types.SimpleNamespace(Redis=DummyRedis))
    with pytest.raises(ConnectionError):
        distributed.RedisBroker('redis://bad')
