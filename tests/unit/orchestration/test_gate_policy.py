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
from autoresearch.search.context import SearchContext


def _make_config(**overrides: object) -> ConfigModel:
    config = ConfigModel()
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def test_scout_gate_reduces_loops_when_signals_low() -> None:
    """High overlap and low conflict skip debate and estimate token savings."""

    config = _make_config(token_budget=120, loops=3)
    state = QueryState(query="What is the capital of France?", primus_index=0, coalitions={})
    metrics = OrchestrationMetrics()

    by_backend = {
        "duckduckgo": [
            {
                "url": "https://example.com/paris",
                "title": "Paris - Wikipedia",
                "snippet": "What is the capital of France? It is Paris, the capital of France.",
            },
            {
                "url": "https://example.com/history",
                "title": "History of Paris",
                "snippet": "Paris has long served as France's capital city.",
            },
        ],
        "serper": [
            {
                "url": "https://example.com/paris",
                "title": "Paris - Wikipedia",
                "snippet": "Paris, the capital city of France, sits on the Seine river.",
            },
            {
                "url": "https://example.com/overview",
                "title": "France Overview",
                "snippet": "France designates Paris as its capital and largest city.",
            },
        ],
    }
    ranked = [dict(doc) for docs in by_backend.values() for doc in docs]

    with SearchContext.temporary_instance() as context:
        context.record_scout_observation(state.query, ranked, by_backend=by_backend)
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
    assert state.metadata["scout_retrieval_sets"]
    assert state.metadata["scout_entailment_scores"]
    assert state.metadata["scout_complexity_features"]


def test_scout_gate_respects_force_debate_override() -> None:
    """Explicit overrides bypass the automatic heuristics."""

    config = _make_config(
        loops=2,
        gate_user_overrides={"decision": "force_debate", "signals": {"retrieval_overlap": 0.99}},
    )
    state = QueryState(query="Summarize the theory of relativity", primus_index=0, coalitions={})
    metrics = OrchestrationMetrics()
    policy = ScoutGatePolicy(config)

    by_backend = {
        "duckduckgo": [
            {
                "url": "https://example.com/relativity",
                "title": "Relativity",
                "snippet": "Relativity explores the geometry of spacetime and frames.",
            }
        ],
        "serper": [
            {
                "url": "https://example.com/relativity",
                "title": "Relativity",
                "snippet": "Relativity covers both general and special theories.",
            },
            {
                "url": "https://example.com/einstein",
                "title": "Albert Einstein",
                "snippet": "Einstein proposed the theory of relativity in the early 1900s.",
            },
        ],
    }
    ranked = [dict(doc) for docs in by_backend.values() for doc in docs]

    with SearchContext.temporary_instance() as context:
        context.record_scout_observation(state.query, ranked, by_backend=by_backend)
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
