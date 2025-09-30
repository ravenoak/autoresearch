"""Regression tests for the scout gate policy heuristics."""

from __future__ import annotations

from typing import Any, cast

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestration_utils import (
    OrchestrationUtils,
    ScoutGateDecision,
    ScoutGatePolicy,
)
from autoresearch.orchestration.state import QueryState
from autoresearch.search.context import SearchContext
from tests.typing_helpers import (
    GraphStageMetadata,
    GraphSummaryMetadata,
    SearchContextGraphAttributes,
)


def _make_config(**overrides: object) -> ConfigModel:
    config = ConfigModel()
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def test_scout_gate_reduces_loops_when_signals_low() -> None:
    """High overlap and low conflict skip debate and estimate token savings."""

    config = _make_config(
        token_budget=120,
        loops=3,
        gate_retrieval_overlap_threshold=0.0,
        gate_retrieval_confidence_threshold=0.0,
        gate_nli_conflict_threshold=1.0,
        gate_complexity_threshold=1.0,
        gate_coverage_gap_threshold=1.0,
    )
    state = QueryState(query="What is the capital of France?", primus_index=0, coalitions={})
    state.sources.extend(
        [
            {
                "title": "Paris - Wikipedia",
                "snippet": "Paris remains France's capital city.",
                "source_id": "src-paris",
            },
            {
                "title": "History of Paris",
                "snippet": "Historical records document Paris as the capital.",
                "source_id": "src-history",
            },
        ]
    )
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
    assert "coverage_gap" in decision.heuristics
    assert "retrieval_confidence" in decision.heuristics
    assert "graph_contradiction" in decision.heuristics
    assert "graph_similarity" in decision.heuristics
    assert decision.heuristics.get("scout_agreement") == 1.0
    scout_stage = state.metadata.get("scout_stage", {})
    assert scout_stage.get("heuristics") == decision.heuristics
    assert scout_stage.get("rationales") == decision.rationales
    agreement = scout_stage.get("agreement", {})
    assert agreement.get("sample_count") == 0
    assert scout_stage.get("snippets"), "scout snippets should be persisted"
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
    assert decision.rationales["retrieval_overlap"]["override"] == 0.99


def test_scout_gate_flags_coverage_gap_and_confidence() -> None:
    """Coverage deltas and low confidence should trigger debate."""

    config = _make_config(
        loops=3,
        gate_coverage_gap_threshold=0.2,
        gate_retrieval_confidence_threshold=0.6,
        gate_scout_agreement_threshold=0.9,
    )
    state = QueryState(
        query="Evaluate conflicting climate claims",
        primus_index=0,
        coalitions={},
        claims=[
            {"id": "c1", "content": "Claim one"},
            {"id": "c2", "content": "Claim two"},
            {"id": "c3", "content": "Claim three"},
        ],
        claim_audits=[{"claim_id": "c1"}],
    )
    state.metadata["scout_entailment_scores"] = [
        {"score": 0.3, "support": 0.2, "conflict": 0.8},
        {"score": 0.4, "support": 0.35, "conflict": 0.7},
    ]
    state.metadata["scout_samples"] = [
        {
            "index": 0,
            "answer": "Claim one is credible based on current data.",
            "claims": [
                {"id": "c1", "content": "Claim one is credible."},
                {"id": "c2", "content": "Claim two lacks support."},
            ],
        },
        {
            "index": 1,
            "answer": "Claim one is refuted and claim two is verified.",
            "claims": [
                {"id": "c1", "content": "Claim one is refuted."},
                {"id": "c2", "content": "Claim two is verified."},
            ],
        },
    ]
    metrics = OrchestrationMetrics()
    policy = ScoutGatePolicy(config)

    decision = policy.evaluate(
        query=state.query,
        state=state,
        loops=config.loops,
        metrics=metrics,
    )

    assert decision.should_debate is True
    assert decision.heuristics["coverage_gap"] > 0.0
    assert decision.heuristics["retrieval_confidence"] < 0.6
    assert decision.heuristics["scout_agreement"] < config.gate_scout_agreement_threshold
    assert decision.rationales["coverage_gap"]["triggered"] is True
    assert decision.rationales["retrieval_confidence"]["triggered"] is True
    assert decision.rationales["scout_agreement"]["triggered"] is True
    assert metrics.gate_events[-1]["coverage"]["total_claims"] == 3


def test_scout_gate_applies_graph_thresholds() -> None:
    """Graph contradictions and similarity thresholds influence debate choice."""

    config = _make_config(
        loops=2,
        gate_retrieval_overlap_threshold=0.0,
        gate_nli_conflict_threshold=1.0,
        gate_complexity_threshold=1.0,
        gate_coverage_gap_threshold=1.0,
        gate_retrieval_confidence_threshold=0.0,
        gate_graph_contradiction_threshold=0.2,
        gate_graph_similarity_threshold=0.3,
    )
    state = QueryState(query="Graph reasoning", primus_index=0, coalitions={})
    metrics = OrchestrationMetrics()
    policy = ScoutGatePolicy(config)

    with SearchContext.temporary_instance() as context:
        typed_context = cast(SearchContextGraphAttributes, context)
        graph_metadata: GraphStageMetadata = {
            "contradictions": {
                "raw_score": 0.8,
                "weighted_score": 0.28,
                "weight": config.search.context_aware.graph_contradiction_weight,
                "items": [
                    {
                        "subject": "Policy A",
                        "predicate": "conflicts_with",
                        "objects": ["Policy B", "Policy C"],
                    }
                ],
            },
            "similarity": {
                "raw_score": 0.2,
                "weighted_score": 0.1,
                "weight": config.search.context_aware.graph_signal_weight,
                "entity_count": 5.0,
                "relation_count": 1.0,
            },
            "neighbors": {
                "Policy A": [
                    {
                        "predicate": "relates_to",
                        "target": "Policy D",
                        "direction": "out",
                    }
                ]
            },
            "paths": [["Policy A", "Policy B", "Policy E"]],
        }
        graph_summary: GraphSummaryMetadata = {
            "sources": [
                "https://example.com/policy-a",
                "https://example.com/policy-b",
            ],
            "provenance": [{"source": "https://example.com/policy-a"}],
            "relation_count": 4,
            "entity_count": 3,
        }
        typed_context._graph_stage_metadata = graph_metadata
        typed_context._graph_summary = graph_summary
        decision = policy.evaluate(
            query=state.query,
            state=state,
            loops=config.loops,
            metrics=metrics,
        )

    assert decision.should_debate is True
    assert decision.heuristics["graph_contradiction"] == pytest.approx(0.28)
    assert decision.heuristics["graph_similarity"] == pytest.approx(0.1)
    assert decision.rationales["graph_contradiction"]["triggered"] is True
    assert decision.rationales["graph_similarity"]["triggered"] is True
    graph_payload = cast(dict[str, object], decision.telemetry.get("graph") or {})
    contradictions = cast(dict[str, float], graph_payload.get("contradictions", {}))
    similarity = cast(dict[str, float], graph_payload.get("similarity", {}))
    sources = cast(list[str], graph_payload.get("sources", []))
    assert contradictions.get("weighted_score") == pytest.approx(0.28)
    assert similarity.get("weighted_score") == pytest.approx(0.1)
    assert sources[0] == "https://example.com/policy-a"
    scout_stage = cast(dict[str, Any], state.metadata.get("scout_stage", {}))
    assert scout_stage.get("graph_context") == graph_payload
