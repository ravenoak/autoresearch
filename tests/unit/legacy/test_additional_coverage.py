# mypy: ignore-errors
import json
import types
from collections import OrderedDict
from pathlib import Path
from typing import Protocol, TypeAlias, TypeVar
from unittest.mock import MagicMock

import pytest

from autoresearch import cli_utils, search
from autoresearch.cli_utils import format_success, render_evaluation_summary
from autoresearch.evaluation.summary import EvaluationSummary
from autoresearch.llm import pool as llm_pool
from autoresearch.orchestration import metrics
from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager
from autoresearch.output_format import OutputFormatter
from autoresearch.storage import StorageManager, get_delegate, set_delegate
from autoresearch.streamlit_app import collect_system_metrics, orch_metrics
from autoresearch.streamlit_app import psutil as streamlit_psutil
from autoresearch.streamlit_app import st as streamlit_st
from autoresearch.streamlit_app import track_agent_performance
from autoresearch.typing.http import HTTPAdapter

from .typing_helpers import (
    build_summary_fixture,
    make_llm_pool_config,
    make_psutil_stub,
    make_runtime_config,
    make_search_config,
    make_streamlit_stub,
)


RowT = TypeVar("RowT", bound=tuple[object, ...])
TableRow: TypeAlias = tuple[object, ...]


class DummyTable(Protocol[RowT]):
    """Minimal protocol capturing the rendering surface exercised in tests."""

    rows: list[RowT]

    def add_column(self, *_args: object, **_kwargs: object) -> None:
        """Add a column definition to the underlying table."""
        ...

    def add_row(self, *row: object) -> None:
        """Append a row of objects to the table."""
        ...


def test_log_release_tokens_invalid_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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


def test_circuit_breaker_transitions(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_circuit_breaker_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_circuit_breaker_success_decrements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = CircuitBreakerManager()
    for _ in range(2):
        manager.update_circuit_breaker("Y", "recoverable")
    manager.handle_agent_success("Y")
    state = manager.get_circuit_breaker_state("Y")
    assert state["failure_count"] == 1


def test_http_session_reuse_and_close(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = make_runtime_config(search=make_search_config(http_pool_size=1))
    monkeypatch.setattr("autoresearch.search.http.get_config", lambda: cfg)
    search.close_http_session()
    s1 = search.get_http_session()
    s2 = search.get_http_session()
    assert s1 is s2
    search.close_http_session()
    assert search._http_session is None


def test_llm_pool_session_reuse(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = make_llm_pool_config(2)
    monkeypatch.setattr("autoresearch.llm.pool.get_config", lambda: cfg)
    llm_pool.close_session()
    session = llm_pool.get_session()
    adapter = session.get_adapter("https://example.org")
    assert isinstance(adapter, HTTPAdapter)
    assert llm_pool.get_session() is session
    llm_pool.close_session()


def test_llm_pool_adapter_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = make_llm_pool_config(1)
    monkeypatch.setattr("autoresearch.llm.pool.get_config", lambda: cfg)
    llm_pool.close_session()

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("llm adapter failure")

    monkeypatch.setattr(llm_pool, "_build_llm_adapter", boom)

    with pytest.raises(RuntimeError, match="llm adapter failure"):
        llm_pool.get_session()

    assert llm_pool._session is None


def test_set_get_delegate() -> None:
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


def test_pop_low_score_missing_confidence(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = MagicMock()
    graph.nodes = {"a": {}, "b": {"confidence": 0.1}}
    lru = OrderedDict([("a", 0), ("b", 0)])
    monkeypatch.setattr(StorageManager.context, "graph", graph)
    monkeypatch.setattr(StorageManager.state, "lru", lru)
    node = StorageManager._pop_low_score()
    assert node == "a"
    assert "a" not in lru


def test_output_formatter_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(Exception):
        OutputFormatter.format({"foo": "bar"}, "json")


def test_streamlit_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = make_streamlit_stub()
    monkeypatch.setattr(streamlit_st, "session_state", fake_st.session_state, False)
    track_agent_performance("A", 1.0, 5)
    assert fake_st.session_state["agent_performance"]["A"]["executions"] == 1
    fake_psutil = make_psutil_stub(
        cpu_percent=10.0,
        memory_percent=20.0,
        memory_used=1024**3,
        memory_total=2 * 1024**3,
        process_rss=50 * 1024**2,
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


@pytest.fixture
def dummy_table(monkeypatch: pytest.MonkeyPatch) -> list[DummyTable[TableRow]]:
    created_tables: list[DummyTable[TableRow]] = []

    class _RecordingDummyTable(DummyTable[TableRow]):
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.rows: list[TableRow] = []
            created_tables.append(self)

        def add_column(self, *_args: object, **_kwargs: object) -> None:
            return None

        def add_row(self, *row: object) -> None:
            self.rows.append(tuple(row))

    monkeypatch.setattr(cli_utils, "Table", _RecordingDummyTable)
    monkeypatch.setattr(cli_utils.console, "print", lambda *_args, **_kwargs: None)
    return created_tables


@pytest.fixture
def populated_summary() -> EvaluationSummary:
    return build_summary_fixture(
        total_examples=2,
        example_csv=Path("artifacts/examples.csv"),
        summary_csv=Path("artifacts/summary.csv"),
    )


def test_render_evaluation_summary_joins_artifacts(
    dummy_table: list[DummyTable[TableRow]],
) -> None:
    summary = build_summary_fixture(
        total_examples=1,
        duckdb_path=Path("artifacts/run.duckdb"),
        example_parquet=Path("artifacts/examples.parquet"),
        summary_parquet=Path("artifacts/summary.parquet"),
        example_csv=Path("artifacts/examples.csv"),
        summary_csv=Path("artifacts/summary.csv"),
        avg_planner_depth=None,
        avg_routing_delta=None,
        total_routing_delta=None,
        avg_routing_decisions=None,
        routing_strategy=None,
    )

    render_evaluation_summary([summary])

    assert dummy_table
    row = dummy_table[0].rows[0]
    artifacts_cell = row[-1]
    expected = ", ".join(
        [
            "duckdb: artifacts/run.duckdb",
            "examples: artifacts/examples.parquet",
            "summary: artifacts/summary.parquet",
            "examples.csv: artifacts/examples.csv",
            "summary.csv: artifacts/summary.csv",
        ]
    )
    assert artifacts_cell == expected
    assert row[4] == "—"
    assert row[5] == "—"


def test_render_evaluation_summary_formats_planner_and_routing(
    dummy_table: list[DummyTable[TableRow]],
    populated_summary: EvaluationSummary,
) -> None:
    render_evaluation_summary([populated_summary])

    assert dummy_table
    row = dummy_table[0].rows[0]
    assert row[4] == "2.5"
    assert row[5] == "1.75/3.50 (avg 1.5 routes)"


def test_format_percentage_variants() -> None:
    assert cli_utils._format_percentage(None) == "—"
    assert cli_utils._format_percentage(0.1234, precision=1) == "12.3%"
    assert cli_utils._format_percentage(-0.0, precision=1) == "0.0%"


def test_cli_utils_format_helpers_importable() -> None:
    assert format_success("Completed") == "[bold green]✓[/bold green] Completed"
    assert format_success("Completed", symbol=False) == "[bold green]Completed[/bold green]"

    # Rendering helper should be importable and callable. Rendering side-effects are
    # exercised in ``test_render_evaluation_summary_joins_artifacts``; here we simply
    # ensure the symbol resolves via direct import to guard against syntax regressions.
    assert render_evaluation_summary is cli_utils.render_evaluation_summary
