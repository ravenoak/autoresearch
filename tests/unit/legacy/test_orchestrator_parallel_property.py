# mypy: ignore-errors
"""Property-based checks for parallel query execution."""

from unittest.mock import patch

import pytest
from hypothesis import given, strategies as st

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.parallel import execute_parallel_query


class DummySynthesizer:
    def execute(self, state, config):
        return {"answer": "synth"}


class DummyOrchestrator:
    def run_query(self, query, cfg):
        return QueryResponse(query=query, answer="x", citations=[], reasoning=[], metrics={})


@given(
    st.lists(
        st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3),
        min_size=1,
        max_size=3,
    )
)
@pytest.mark.reasoning_modes
def test_parallel_groups_merge_metrics(agent_groups):
    """Metrics reflect total and successful group counts.

    Assumes each group returns a static response and synthesizer echoes a fixed
    answer. Randomized groupings exercise parallel scheduling.
    """

    cfg = ConfigModel(agents=[], loops=1)

    with patch("autoresearch.orchestration.orchestrator.Orchestrator", DummyOrchestrator):
        with patch(
            "autoresearch.orchestration.parallel.AgentFactory.get",
            return_value=DummySynthesizer(),
        ):
            resp = execute_parallel_query("q", cfg, agent_groups)
    metrics = resp.metrics["parallel_execution"]
    assert metrics["total_groups"] == len(agent_groups)
    assert metrics["successful_groups"] == len(agent_groups)
    assert resp.answer == "synth"
