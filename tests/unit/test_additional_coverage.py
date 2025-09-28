import json
import types
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from autoresearch import cli_utils, search
from autoresearch.cli_utils import format_success, render_evaluation_summary
from autoresearch.orchestration import metrics
from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager
from autoresearch.output_format import OutputFormatter
from autoresearch.storage import StorageManager, get_delegate, set_delegate
from autoresearch.evaluation.harness import EvaluationSummary
from autoresearch.streamlit_app import collect_system_metrics, orch_metrics
from autoresearch.streamlit_app import psutil as streamlit_psutil
from autoresearch.streamlit_app import st as streamlit_st
from autoresearch.streamlit_app import track_agent_performance


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
    manager = CircuitBreakerManager()
    t = {"v": 0}
    monkeypatch.setattr(
        "autoresearch.orchestration.circuit_breaker.time",
        types.SimpleNamespace(time=lambda: t.setdefault("v", t["v"] + 10)),
    )
    for _ in range(3):
        manager.update_circuit_breaker("X", "recoverable")
    state = manager.get_circuit_breaker_state("X")
    assert state["state"] == "open"
    # advance time beyond cooling period
    t["v"] += 40
    manager.circuit_breakers["X"]["last_failure_time"] = 0
    manager.update_circuit_breaker("X", "noop")
    state = manager.get_circuit_breaker_state("X")
    assert state["state"] == "half-open"


def test_circuit_breaker_recovery(monkeypatch):
    manager = CircuitBreakerManager()
    t = {"v": 0}
    monkeypatch.setattr(
        "autoresearch.orchestration.circuit_breaker.time",
        types.SimpleNamespace(time=lambda: t.setdefault("v", t["v"] + 10)),
    )
    for _ in range(3):
        manager.update_circuit_breaker("X", "recoverable")
    # Advance time so breaker moves to half-open
    t["v"] += 40
    manager.circuit_breakers["X"]["last_failure_time"] = 0
    manager.update_circuit_breaker("X", "noop")
    manager.handle_agent_success("X")
    state = manager.get_circuit_breaker_state("X")
    assert state["state"] == "closed"
    assert state["failure_count"] == 0


def test_circuit_breaker_success_decrements(monkeypatch):
    manager = CircuitBreakerManager()
    for _ in range(2):
        manager.update_circuit_breaker("Y", "recoverable")
    manager.handle_agent_success("Y")
    state = manager.get_circuit_breaker_state("Y")
    assert state["failure_count"] == 1


def test_http_session_reuse_and_close(monkeypatch):
    cfg = types.SimpleNamespace(search=types.SimpleNamespace(http_pool_size=1))
    monkeypatch.setattr("autoresearch.search.http.get_config", lambda: cfg)
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
        def setup(cls, db_path=None, context=None):
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
    monkeypatch.setattr(StorageManager.context, "graph", graph)
    monkeypatch.setattr(StorageManager.state, "lru", lru)
    node = StorageManager._pop_low_score()
    assert node == "a"
    assert "a" not in lru


def test_output_formatter_invalid(monkeypatch):
    with pytest.raises(Exception):
        OutputFormatter.format({"foo": "bar"}, "json")


def test_streamlit_metrics(monkeypatch):
    class SS(dict):
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__

    fake_st = types.SimpleNamespace(session_state=SS(), markdown=lambda *a, **k: None)
    monkeypatch.setattr(streamlit_st, "session_state", fake_st.session_state, False)
    track_agent_performance("A", 1.0, 5)
    assert fake_st.session_state["agent_performance"]["A"]["executions"] == 1
    fake_psutil = types.SimpleNamespace(
        cpu_percent=lambda interval=None: 10.0,
        virtual_memory=lambda: types.SimpleNamespace(
            percent=20.0, used=1024**3, total=2 * 1024**3
        ),
        Process=lambda pid=None: types.SimpleNamespace(
            memory_info=lambda: types.SimpleNamespace(rss=50 * 1024**2)
        ),
    )
    monkeypatch.setattr(streamlit_psutil, "cpu_percent", fake_psutil.cpu_percent)
    monkeypatch.setattr(streamlit_psutil, "virtual_memory", fake_psutil.virtual_memory)
    monkeypatch.setattr(streamlit_psutil, "Process", fake_psutil.Process)

    def make_counter(v: int) -> types.SimpleNamespace:
        ns = types.SimpleNamespace(value=v)
        ns.get = lambda ns=ns: ns.value
        ns.set = lambda val, ns=ns: setattr(ns, "value", val)
        return ns

    monkeypatch.setattr(orch_metrics.TOKENS_IN_COUNTER, "_value", make_counter(1))
    monkeypatch.setattr(orch_metrics.TOKENS_OUT_COUNTER, "_value", make_counter(2))
    metrics_data = collect_system_metrics()
    assert metrics_data["cpu_percent"] == 10.0
    assert metrics_data["tokens_in_total"] == 1
    assert metrics_data["tokens_out_total"] == 2


def test_render_evaluation_summary_joins_artifacts(monkeypatch):
    now = datetime.now(timezone.utc)
    summary = EvaluationSummary(
        dataset="truthfulqa",
        run_id="run-123",
        started_at=now,
        completed_at=now,
        total_examples=1,
        accuracy=0.5,
        citation_coverage=1.0,
        contradiction_rate=0.0,
        avg_latency_seconds=2.5,
        avg_tokens_input=100.0,
        avg_tokens_output=50.0,
        avg_tokens_total=150.0,
        avg_cycles_completed=1.0,
        gate_debate_rate=0.0,
        gate_exit_rate=0.25,
        gated_example_ratio=None,
        config_signature="cfg",
        duckdb_path=Path("artifacts/run.duckdb"),
        example_parquet=Path("artifacts/examples.parquet"),
        summary_parquet=Path("artifacts/summary.parquet"),
    )

    created_tables: list["DummyTable"] = []

    class DummyTable:
        def __init__(self, *args, **kwargs):
            created_tables.append(self)
            self.rows: list[tuple[object, ...]] = []

        def add_column(self, *args, **kwargs) -> None:  # pragma: no cover - interface stub
            return None

        def add_row(self, *args) -> None:
            self.rows.append(args)

    def fake_print(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(cli_utils, "Table", DummyTable)
    monkeypatch.setattr(cli_utils.console, "print", fake_print)

    cli_utils.render_evaluation_summary([summary])

    assert created_tables
    artifacts_cell = created_tables[0].rows[0][-1]
    expected = ", ".join(
        [
            "duckdb: artifacts/run.duckdb",
            "examples: artifacts/examples.parquet",
            "summary: artifacts/summary.parquet",
        ]
    )
    assert artifacts_cell == expected


def test_cli_utils_format_helpers_importable():
    assert format_success("Completed") == "[bold green]✓[/bold green] Completed"
    assert format_success("Completed", symbol=False) == "[bold green]Completed[/bold green]"

    # Rendering helper should be importable and callable. Rendering side-effects are
    # exercised in ``test_render_evaluation_summary_joins_artifacts``; here we simply
    # ensure the symbol resolves via direct import to guard against syntax regressions.
    assert render_evaluation_summary is cli_utils.render_evaluation_summary
