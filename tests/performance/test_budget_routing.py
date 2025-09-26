"""Performance-focused tests for budget-aware routing heuristics."""

from __future__ import annotations

import pytest

from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.token_budget import ModelBudget


def test_role_snapshot_and_model_selection_prefers_budget() -> None:
    """Verify role snapshots drive budget-aware routing decisions."""

    metrics = OrchestrationMetrics()

    # Simulate two turns for the synthesizer role.
    metrics.begin_agent_turn("Synthesizer", "Synthesizer", "fast-large")
    metrics.record_tokens("Synthesizer", 120, 60)
    metrics.record_agent_timing("Synthesizer", 1.2)

    metrics.begin_agent_turn("Synthesizer", "Synthesizer", "fast-large")
    metrics.record_tokens("Synthesizer", 100, 50)
    metrics.record_agent_timing("Synthesizer", 0.9)

    snapshot = metrics.get_role_usage_snapshot("Synthesizer")
    assert snapshot.call_count == 2
    assert pytest.approx(snapshot.avg_prompt_tokens, rel=1e-6) == 110.0
    assert pytest.approx(snapshot.avg_completion_tokens, rel=1e-6) == 55.0

    decisions = metrics.select_model_for_role(
        "Synthesizer",
        {
            "fast-large": ModelBudget(
                name="fast-large",
                prompt_cost_per_1k=0.6,
                completion_cost_per_1k=0.6,
                latency_ms=520.0,
            ),
            "budget-small": ModelBudget(
                name="budget-small",
                prompt_cost_per_1k=0.08,
                completion_cost_per_1k=0.08,
                latency_ms=900.0,
            ),
        },
        default_model="fast-large",
        cost_budget=0.05,
        latency_budget_ms=1500.0,
    )

    assert decisions.model == "budget-small"
    assert decisions.meets_budget is True
    assert "cost" in decisions.rationale
