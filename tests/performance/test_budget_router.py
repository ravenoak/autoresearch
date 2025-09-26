"""Performance-oriented tests for budget-aware model routing heuristics."""

from __future__ import annotations

from autoresearch.config.models import (
    AgentConfig,
    ConfigModel,
    ModelRouteProfile,
    ModelRoutingConfig,
)
from autoresearch.orchestration.metrics import OrchestrationMetrics


def _make_base_config() -> ConfigModel:
    config = ConfigModel()
    config.default_model = "premium"
    config.token_budget = 4000
    config.agents = ["Synthesizer", "Contrarian"]
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
    return config


def test_budget_router_prefers_cost_efficient_model_when_budget_constrained() -> None:
    """High token consumption forces the router onto a cheaper profile."""

    config = _make_base_config()
    config.agent_config["Synthesizer"] = AgentConfig(
        preferred_models=["premium", "efficient"],
        token_share=0.5,
        latency_slo_ms=1200.0,
    )

    metrics = OrchestrationMetrics()
    metrics.record_tokens("Synthesizer", tokens_in=1800, tokens_out=900)
    metrics.record_agent_timing("Synthesizer", duration=0.8)

    selected = metrics.apply_model_routing("Synthesizer", config)

    assert selected == "efficient"
    assert config.agent_config["Synthesizer"].model == "efficient"


def test_budget_router_retains_preferred_model_when_within_budget() -> None:
    """Low token usage leaves the preferred premium profile in place."""

    config = _make_base_config()
    config.agent_config["Contrarian"] = AgentConfig(
        preferred_models=["premium", "efficient"],
        token_share=0.5,
        latency_slo_ms=1200.0,
    )

    metrics = OrchestrationMetrics()
    metrics.record_tokens("Contrarian", tokens_in=200, tokens_out=150)
    metrics.record_agent_timing("Contrarian", duration=0.4)

    selected = metrics.apply_model_routing("Contrarian", config)

    assert selected == "premium"
    assert config.agent_config["Contrarian"].model == "premium"


def test_metrics_summary_reports_cost_and_latency() -> None:
    """Summaries expose latency, token averages, and routing savings."""

    config = _make_base_config()
    config.agent_config["Synthesizer"] = AgentConfig(
        preferred_models=["premium", "efficient"],
        token_share=0.5,
        latency_slo_ms=1200.0,
    )

    metrics = OrchestrationMetrics()
    metrics.record_tokens("Synthesizer", tokens_in=1800, tokens_out=900)
    metrics.record_agent_timing("Synthesizer", duration=0.95)

    selected = metrics.apply_model_routing("Synthesizer", config)
    assert selected == "efficient"

    summary = metrics.get_summary()
    latency_ms = summary["agent_latency_p95_ms"]["Synthesizer"]
    avg_tokens = summary["agent_avg_tokens"]["Synthesizer"]
    decisions = summary["model_routing_decisions"]
    savings = summary["model_routing_cost_savings"]

    assert latency_ms >= 900.0
    assert avg_tokens >= 2600.0
    assert decisions[-1]["selected_model"] == "efficient"
    assert savings["total"] > 0
