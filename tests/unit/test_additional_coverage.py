import types
import json
from collections import OrderedDict
from unittest.mock import MagicMock

import pytest

from autoresearch.orchestration import metrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch import search
from autoresearch.storage import StorageManager, set_delegate, get_delegate
from autoresearch.output_format import OutputFormatter
from autoresearch.streamlit_app import track_agent_performance, collect_system_metrics, psutil as streamlit_psutil, orch_metrics, st as streamlit_st


def test_log_release_tokens_invalid_json(tmp_path, monkeypatch):
    path = tmp_path / "rel.json"
    path.write_text("not json")
    monkeypatch.setenv("AUTORESEARCH_RELEASE_METRICS", str(path))
    m = metrics.OrchestrationMetrics()
    m.release = "test"
    m.record_tokens("A", 1, 2)
    m.get_summary()  # triggers _log_release_tokens
    data = json.loads(path.read_text())
    assert data["test"]["A"]["in"] == 1
    assert data["test"]["A"]["out"] == 2


def test_circuit_breaker_transitions(monkeypatch):
    Orchestrator._circuit_breakers.clear()
    t = {"v": 0}
    monkeypatch.setattr(Orchestrator, "time", types.SimpleNamespace(time=lambda: t.setdefault("v", t["v"] + 10)))
    for _ in range(3):
        Orchestrator._update_circuit_breaker("X", "recoverable")
    state = Orchestrator.get_circuit_breaker_state("X")
    assert state["state"] == "open"
    # advance time beyond cooling period
    t["v"] += 40
    Orchestrator._update_circuit_breaker("X", "transient")
    state = Orchestrator.get_circuit_breaker_state("X")
    assert state["state"] == "half-open"


def test_http_session_reuse_and_close(monkeypatch):
    class Cfg:
        pass

    cfg = Cfg()
    cfg.search = types.SimpleNamespace(http_pool_size=1)
    monkeypatch.setattr(search, "get_config", lambda: cfg)
    search.close_http_session()
    s1 = search.get_http_session()
    s2 = search.get_http_session()
    assert s1 is s2
    search.close_http_session()
    assert search._http_session is None


def test_set_get_delegate():
    class Dummy(StorageManager):
        called = False

        @classmethod
        def setup(cls, db_path=None):
            cls.called = True
    set_delegate(Dummy)
    StorageManager.setup(db_path=None)
    assert Dummy.called
    assert get_delegate() is Dummy
    set_delegate(None)


def test_pop_low_score_missing_confidence(monkeypatch):
    graph = MagicMock()
    graph.nodes = {"a": {}, "b": {"confidence": 0.1}}
    lru = OrderedDict([("a", 0), ("b", 0)])
    monkeypatch.setattr("autoresearch.storage._graph", graph)
    monkeypatch.setattr("autoresearch.storage._lru", lru)
    node = StorageManager._pop_low_score()
    assert node == "a"
    assert "a" not in lru


def test_output_formatter_invalid(monkeypatch):
    with pytest.raises(Exception):
        OutputFormatter.format({"foo": "bar"}, "json")


def test_streamlit_metrics(monkeypatch):
    fake_st = types.SimpleNamespace(session_state={}, markdown=lambda *a, **k: None)
    monkeypatch.setattr(streamlit_st, "session_state", fake_st.session_state, False)
    track_agent_performance("A", 1.0, 5)
    assert fake_st.session_state["agent_performance"]["A"]["executions"] == 1
    fake_psutil = types.SimpleNamespace(
        cpu_percent=lambda interval=None: 10.0,
        virtual_memory=lambda: types.SimpleNamespace(percent=20.0, used=1024**3, total=2*1024**3),
        Process=lambda pid=None: types.SimpleNamespace(memory_info=lambda: types.SimpleNamespace(rss=50*1024**2))
    )
    monkeypatch.setattr(streamlit_psutil, "cpu_percent", fake_psutil.cpu_percent)
    monkeypatch.setattr(streamlit_psutil, "virtual_memory", fake_psutil.virtual_memory)
    monkeypatch.setattr(streamlit_psutil, "Process", fake_psutil.Process)
    monkeypatch.setattr(orch_metrics.TOKENS_IN_COUNTER, "_value", types.SimpleNamespace(get=lambda: 1))
    monkeypatch.setattr(orch_metrics.TOKENS_OUT_COUNTER, "_value", types.SimpleNamespace(get=lambda: 2))
    metrics_data = collect_system_metrics()
    assert metrics_data["cpu_percent"] == 10.0
    assert metrics_data["tokens_in_total"] == 1
    assert metrics_data["tokens_out_total"] == 2
