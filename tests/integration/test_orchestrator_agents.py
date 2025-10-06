# mypy: ignore-errors
from __future__ import annotations

from collections.abc import Callable, Iterable
import time
from unittest.mock import MagicMock

import pytest

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.types import CallbackMap
from autoresearch.storage import StorageManager
from tests.integration._orchestrator_stubs import AgentDouble, PersistClaimCall
from tests.integration.conftest import AgentGetter, PersistCallable
from tests.typing_helpers import TypedFixture


# ---------------------------------------------------------------------------
# run_query: agent lists and coalitions
# ---------------------------------------------------------------------------


def test_run_query_with_coalitions(
    stub_agent_factory: TypedFixture[Callable[[Iterable[AgentDouble]], AgentGetter]],
    stub_storage_persist: TypedFixture[
        Callable[[list[PersistClaimCall] | None], PersistCallable]
    ],
) -> None:
    calls: list[str] = []
    seen: dict[str, dict[str, list[str]]] = {}

    stub_storage_persist(None)
    stub_agent_factory(
        [
            AgentDouble(name="FactChecker", call_log=calls, seen_coalitions=seen),
            AgentDouble(name="Contrarian", call_log=calls, seen_coalitions=seen),
            AgentDouble(
                name="Synthesizer",
                call_log=calls,
                seen_coalitions=seen,
                answer_on_execute=True,
            ),
        ]
    )

    cfg = ConfigModel(
        agents=["FactChecker", "Contrarian", "Synthesizer"],
        loops=1,
        coalitions={"Team": ["FactChecker", "Contrarian"]},
    )

    orch = Orchestrator()
    response = orch.run_query("q", cfg)

    assert response.answer == "FactChecker, Contrarian, Synthesizer"
    assert calls == ["FactChecker", "Contrarian", "Synthesizer"]
    reasoning_segments = [str(segment) for segment in response.reasoning]
    assert any("claim FactChecker" in segment for segment in reasoning_segments)
    assert any("claim Contrarian" in segment for segment in reasoning_segments)
    assert seen["FactChecker"] == {"Team": ["FactChecker", "Contrarian"]}
    assert seen["Contrarian"] == {"Team": ["FactChecker", "Contrarian"]}


# ---------------------------------------------------------------------------
# run_parallel_query: aggregation of multiple groups
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_run_parallel_query_aggregates_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = ConfigModel(agents=[], loops=1)

    def mock_run_query(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        *,
        agent_factory: type[AgentFactory] | None = None,
        storage_manager: type[StorageManager] | None = None,
    ) -> QueryResponse:
        if config.agents == ["A"]:
            return QueryResponse(
                answer="a", citations=[], reasoning=["claim A"], metrics={}
            )
        return QueryResponse(
            answer="b", citations=[], reasoning=["claim B"], metrics={}
        )

    synthesizer = MagicMock()
    synthesizer.execute.return_value = {"answer": "final"}

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        lambda name: synthesizer,
    )

    resp = Orchestrator.run_parallel_query("q", cfg, [["A"], ["B"]])

    assert resp.answer == "final"
    assert "claim A" in resp.reasoning
    assert "claim B" in resp.reasoning
    assert resp.metrics["parallel_execution"]["total_groups"] == 2


# ---------------------------------------------------------------------------
# Failure cases: circuit breaker and timeout handling
# ---------------------------------------------------------------------------


def test_circuit_breaker_opens(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingAgent:
        def __init__(self) -> None:
            self.name = "Bad"

        def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
            return True

        def execute(
            self, state: QueryState, config: ConfigModel, **kwargs: object
        ) -> dict[str, object]:
            raise RuntimeError("boom")

    monkeypatch.setattr(
        StorageManager, "persist_claim", lambda claim, partial_update=False: None
    )
    synthesizer = AgentDouble(name="Synthesizer")

    def _noop_recovery(
        agent_name: str, error_category: str, exc: Exception, state: QueryState
    ) -> dict[str, object]:
        return {"recovery_strategy": "fail_gracefully", "suggestion": "noop"}

    monkeypatch.setattr(
        "autoresearch.orchestration.error_handling._apply_recovery_strategy",
        _noop_recovery,
    )

    monkeypatch.setattr(
        AgentFactory,
        "get",
        lambda name: FailingAgent() if name == "Bad" else synthesizer,
    )

    cfg = ConfigModel(
        agents=["Bad", "Synthesizer"], loops=1, circuit_breaker_threshold=1
    )

    orch = Orchestrator()
    with pytest.raises(Exception):
        orch.run_query("q", cfg)

    state = orch.get_circuit_breaker_state("Bad")
    assert state["state"] == "half-open"


def test_parallel_query_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ConfigModel(agents=[], loops=1)

    def slow_run_query(query: str, config: ConfigModel) -> QueryResponse:
        time.sleep(0.2)
        return QueryResponse(answer="slow", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", slow_run_query)

    with pytest.raises(Exception):
        Orchestrator.run_parallel_query("q", cfg, [["slow"]], timeout=0)
