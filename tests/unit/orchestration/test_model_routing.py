"""Regression tests for budget-aware model routing telemetry."""

from __future__ import annotations

import pytest

from autoresearch.config.models import (
    AgentConfig,
    ConfigModel,
    ModelRouteProfile,
    ModelRoutingConfig,
    RoleRoutingPolicy,
)
from autoresearch.orchestration.metrics import OrchestrationMetrics


def _configure_router() -> tuple[OrchestrationMetrics, ConfigModel, str | None]:
    config = ConfigModel()
    config.default_model = "premium"
    config.token_budget = 4000
    config.agents = ["Synthesizer"]
    config.model_routing = ModelRoutingConfig(
        enabled=True,
        budget_pressure_ratio=0.8,
        default_latency_slo_ms=1500.0,
        model_profiles={
            "premium": ModelRouteProfile(
                prompt_cost_per_1k=5.0,
                completion_cost_per_1k=5.0,
                latency_p95_ms=900.0,
                quality_rank=10,
            ),
            "efficient": ModelRouteProfile(
                prompt_cost_per_1k=1.5,
                completion_cost_per_1k=1.5,
                latency_p95_ms=1000.0,
                quality_rank=5,
            ),
        },
    )
    config.model_routing.strategy_name = "cost_saver"
    config.model_routing.role_policies = {
        "Synthesizer": RoleRoutingPolicy(
            preferred_models=["premium", "efficient"],
            token_share=0.5,
            latency_slo_ms=1200.0,
        )
    }
    config.agent_config["Synthesizer"] = AgentConfig(
        preferred_models=["premium", "efficient"],
        token_share=0.5,
        latency_slo_ms=1200.0,
        model="premium",
    )

    metrics = OrchestrationMetrics()
    metrics.record_tokens("Synthesizer", tokens_in=1800, tokens_out=900)
    metrics.record_agent_timing("Synthesizer", duration=0.82)

    selected = metrics.apply_model_routing("Synthesizer", config)
    return metrics, config, selected


def test_routing_records_constraints_without_switching() -> None:
    """Telemetry captures budgets while leaving the config untouched."""

    metrics, config, selected = _configure_router()

    assert selected == "efficient"
    assert config.agent_config["Synthesizer"].model == "premium"

    constraints = metrics.routing_agent_constraints["Synthesizer"]
    recommendation = metrics.routing_agent_recommendations["Synthesizer"]
    decision = metrics.routing_decisions[-1]

    assert recommendation == "efficient"
    assert constraints["budget_tokens"] == pytest.approx(2000.0)
    assert constraints["latency_slo_ms"] == pytest.approx(1200.0)
    assert constraints["latency_cap_ms"] == pytest.approx(1200.0)
    assert decision.metadata is not None
    assert decision.metadata["applied"] is False
    assert decision.metadata["latency_slo_ms"] == pytest.approx(1200.0)


def test_summary_reports_agent_constraints() -> None:
    """Summary output mirrors the live routing telemetry."""

    metrics, _, _ = _configure_router()

    summary = metrics.get_summary()
    constraints = summary["model_routing_agent_constraints"]["Synthesizer"]
    recommendation = summary["model_routing_recommendations"]["Synthesizer"]
    decision_meta = summary["model_routing_decisions"][-1]["metadata"]

    assert recommendation == "efficient"
    assert constraints["budget_tokens"] == pytest.approx(2000.0)
    assert constraints["latency_slo_ms"] == pytest.approx(1200.0)
    assert constraints["latency_cap_ms"] == pytest.approx(1200.0)
    assert decision_meta["applied"] is False
