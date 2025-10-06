# mypy: ignore-errors
"""Property-based test for deterministic parallel merging."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from hypothesis import given, strategies as st

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.parallel import execute_parallel_query
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.reasoning_payloads import FrozenReasoningStep


class DummyOrchestrator:
    def run_query(self, query, cfg):
        name = ",".join(cfg.agents)
        return QueryResponse(query=query, answer=name, citations=[], reasoning=[name], metrics={})


class DummySynthesizer:
    def execute(self, state, config):
        return {"answer": "s", "claims": [], "sources": []}


@given(
    st.lists(
        st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=2),
        min_size=1,
        max_size=3,
    )
)
@pytest.mark.reasoning_modes
def test_parallel_merging_is_deterministic(agent_groups):
    """Each group contributes exactly one claim regardless of completion order."""

    cfg = ConfigModel(agents=[], loops=1)

    def run_with_order(reverse: bool):
        def fake_as_completed(fs, timeout=None):
            items = list(fs)
            if reverse:
                items.reverse()
            for fut in items:
                yield fut

        with patch("concurrent.futures.as_completed", fake_as_completed):
            with patch.object(Orchestrator, "run_query", DummyOrchestrator().run_query):
                with patch(
                    "autoresearch.orchestration.parallel.AgentFactory.get",
                    return_value=DummySynthesizer(),
                ):
                    resp = execute_parallel_query("q", cfg, agent_groups)
        return resp

    resp1 = run_with_order(False)
    resp2 = run_with_order(True)

    expected = {",".join(g) for g in agent_groups}
    assert set(resp1.reasoning) == expected
    assert set(resp2.reasoning) == expected
    assert all(isinstance(step, FrozenReasoningStep) for step in resp1.reasoning)


@pytest.mark.reasoning_modes
def test_parallel_merging_deduplicates_identical_claims():
    """Parallel execution should deduplicate identical reasoning payloads."""

    agent_groups = [["A"], ["B"]]
    cfg = ConfigModel(agents=[], loops=1)

    class DuplicateOrchestrator:
        def run_query(self, query, cfg):
            del query, cfg
            return QueryResponse(
                query="q",
                answer="duplicate",
                citations=[],
                reasoning=[{"text": "shared"}],
                metrics={},
            )

    with patch.object(Orchestrator, "run_query", DuplicateOrchestrator().run_query):
        with patch(
            "autoresearch.orchestration.parallel.AgentFactory.get",
            return_value=DummySynthesizer(),
        ):
            response = execute_parallel_query("q", cfg, agent_groups)

    assert len(response.reasoning) == 1
    assert str(response.reasoning[0]) == "shared"
