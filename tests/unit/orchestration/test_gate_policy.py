"""Regression tests for the scout gate policy heuristics."""

from __future__ import annotations

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestration_utils import (
    OrchestrationUtils,
    ScoutGateDecision,
    ScoutGatePolicy,
)
from autoresearch.orchestration.state import QueryState


def _make_config(**overrides: object) -> ConfigModel:
    config = ConfigModel()
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def test_scout_gate_reduces_loops_when_signals_low() -> None:
    """High overlap and low conflict skip debate and estimate token savings."""

    config = _make_config(token_budget=120, loops=3)
    state = QueryState(query="What is the capital of France?", primus_index=0, coalitions={})
    state.metadata["scout_retrieval_sets"] = [
        ["doc1", "doc2", "doc3"],
        ["doc2", "doc3"],
        ["doc1", "doc2", "doc3"],
    ]
    state.metadata["scout_entailment_scores"] = [0.05, 0.1]
    state.metadata["scout_complexity_features"] = {"hops": 0, "entity_count": 1, "clauses": 1}

    metrics = OrchestrationMetrics()
    decision = OrchestrationUtils.evaluate_scout_gate_policy(
        query=state.query,
        config=config,
        state=state,
        loops=config.loops,
        metrics=metrics,
    )

    assert isinstance(decision, ScoutGateDecision)
    assert decision.should_debate is False
    assert decision.target_loops == 1
    assert decision.tokens_saved == 80
    assert metrics.gate_events[-1]["tokens_saved_estimate"] == 80
    assert state.metadata["scout_gate"]["should_debate"] is False


def test_scout_gate_respects_force_debate_override() -> None:
    """Explicit overrides bypass the automatic heuristics."""

    config = _make_config(
        loops=2,
        gate_user_overrides={"decision": "force_debate", "signals": {"retrieval_overlap": 0.99}},
    )
    state = QueryState(query="Summarize the theory of relativity", primus_index=0, coalitions={})
    state.metadata["scout_retrieval_sets"] = [["doc1"], ["doc1", "doc2"]]
    state.metadata["scout_entailment_scores"] = [0.05]
    state.metadata["scout_complexity_features"] = {"hops": 1, "entity_count": 1}

    metrics = OrchestrationMetrics()
    policy = ScoutGatePolicy(config)
    decision = policy.evaluate(
        query=state.query,
        state=state,
        loops=config.loops,
        metrics=metrics,
    )

    assert decision.should_debate is True
    assert decision.target_loops == config.loops
    assert decision.tokens_saved == 0
    assert metrics.gate_events[-1]["reason"] == "override_force_debate"
