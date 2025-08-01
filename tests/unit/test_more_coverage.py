from queue import Queue
from unittest.mock import MagicMock

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch import search as search_module
from autoresearch.orchestration import orchestrator as orch_mod
from autoresearch.search import Search, close_http_session, get_http_session
from autoresearch.storage import StorageManager
from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.output_format import FormatTemplate


def test_log_sources(monkeypatch):
    msgs = []
    monkeypatch.setattr(orch_mod, "log", MagicMock())
    orch_mod.log.info = lambda msg, **k: msgs.append(msg)
    Orchestrator._log_sources("A", {"sources": [{"title": "T"}]})
    assert any("provided 1 sources" in m for m in msgs)


def test_log_sources_missing(monkeypatch):
    msgs = []
    monkeypatch.setattr(orch_mod, "log", MagicMock())
    orch_mod.log.warning = lambda msg, **k: msgs.append(msg)
    Orchestrator._log_sources("A", {})
    assert any("provided no sources" in m for m in msgs)


def test_persist_claims(monkeypatch):
    calls = []
    monkeypatch.setattr(StorageManager, "persist_claim", lambda c: calls.append(c["id"]))
    result = {"claims": [{"id": "c1"}, {"id": "c2"}]}
    Orchestrator._persist_claims("A", result, StorageManager)
    assert calls == ["c1", "c2"]


def test_persist_claims_invalid(monkeypatch):
    monkeypatch.setattr(StorageManager, "persist_claim", lambda c: None)
    msgs = []
    monkeypatch.setattr(orch_mod, "log", MagicMock())
    orch_mod.log.warning = lambda msg, **k: msgs.append(msg)
    result = {"claims": ["bad", {"foo": 1}]}
    Orchestrator._persist_claims("A", result, StorageManager)
    assert any("Skipping invalid claim format" in m for m in msgs)


def test_ndcg_perfect():
    rel = [3, 2, 1]
    assert Search._ndcg(rel) == Search._ndcg(sorted(rel, reverse=True))


def test_http_session_cycle(monkeypatch):
    class Cfg:
        pass
    cfg = Cfg()
    cfg.search = type("S", (), {"http_pool_size": 1})
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    close_http_session()
    s1 = get_http_session()
    s2 = get_http_session()
    assert s1 is s2
    close_http_session()
    assert search_module._http_session is None


def test_connection_context_manager_pool():
    backend = DuckDBStorageBackend()
    conn = MagicMock()
    backend._pool = Queue()
    backend._pool.put(conn)
    with backend.connection() as c:
        assert c is conn
    assert not backend._pool.empty()


def test_connection_context_manager_single():
    backend = DuckDBStorageBackend()
    conn = MagicMock()
    backend._conn = conn
    with backend.connection() as c:
        assert c is conn


def test_formattemplate_metrics():
    tpl = FormatTemplate(name="m", template="Tokens: ${metric_tokens}")
    resp = type("R", (), {"answer": "a", "citations": [], "reasoning": [], "metrics": {"tokens": 5}})()
    assert tpl.render(resp) == "Tokens: 5"
