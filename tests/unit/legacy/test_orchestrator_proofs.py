# mypy: ignore-errors
"""Property-based proofs for orchestration invariants."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from hypothesis import given, strategies as st

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.circuit_breaker import CircuitBreakerManager
from autoresearch.orchestration.parallel import execute_parallel_query


class IdentitySynthesizer:
    """Return an empty update for aggregation."""

    def execute(self, state, config):  # pragma: no cover - simple passthrough
        return {}


class MockOrchestrator:
    """Emit a claim for each group."""

    def run_query(self, query, cfg):
        claim = {"text": " ".join(cfg.agents)}
        return QueryResponse(
            query=query,
            answer="",
            citations=[],
            reasoning=[claim],
            metrics={},
        )


@given(
    st.lists(
        st.sampled_from(["critical", "recoverable", "transient"]),
        min_size=0,
        max_size=6,
    )
)
@pytest.mark.error_recovery
def test_circuit_breaker_threshold_sequence(events):
    """Failure counts match increments and threshold controls state."""

    mgr = CircuitBreakerManager(threshold=3, cooldown=1)
    for e in events:
        mgr.update_circuit_breaker("agent", e)
    state = mgr.get_circuit_breaker_state("agent")
    expected = sum(1 if e != "transient" else 0.5 for e in events)
    simulated_state = "closed"
    count = 0.0
    for e in events:
        increment = 1.0 if e != "transient" else 0.5
        count += increment
        if increment == 1.0 and count >= 3 and simulated_state == "closed":
            simulated_state = "open"
    assert state["failure_count"] == expected
    assert state["state"] == simulated_state


@given(
    st.lists(
        st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3),
        min_size=1,
        max_size=3,
    )
)
@pytest.mark.reasoning_modes
def test_parallel_result_merging(agent_groups):
    """Result claims include exactly one entry per agent group."""

    cfg = ConfigModel(agents=[], loops=1)
    with patch("autoresearch.orchestration.orchestrator.Orchestrator", MockOrchestrator):
        with patch(
            "autoresearch.orchestration.parallel.AgentFactory.get",
            return_value=IdentitySynthesizer(),
        ):
            resp = execute_parallel_query("q", cfg, agent_groups)
    claim_texts = sorted(c["text"] for c in resp.reasoning)
    expected = sorted(" ".join(g) for g in agent_groups)
    assert claim_texts == expected
    metrics = resp.metrics["parallel_execution"]
    total = metrics["successful_groups"] + metrics["error_groups"] + metrics["timeout_groups"]
    assert total == metrics["total_groups"]
