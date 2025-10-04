"""Performance-oriented tests for budget-aware model routing heuristics."""

from __future__ import annotations

import json

from autoresearch.config.models import (
    AgentConfig,
    ConfigModel,
    ModelRouteProfile,
    ModelRoutingConfig,
    RoleRoutingPolicy,
)
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.model_routing import evaluate_gate_confidence_escalations
from autoresearch.orchestration.state import QueryState


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
    config.model_routing.strategy_name = "cost_saver"
    config.model_routing.role_policies = {
        "Synthesizer": RoleRoutingPolicy(
            preferred_models=["premium", "efficient"],
            token_share=0.5,
            confidence_threshold=0.6,
            escalation_model="premium",
        ),
        "Contrarian": RoleRoutingPolicy(
            preferred_models=["premium", "efficient"],
            token_share=0.5,
        ),
    }
    return config


def test_budget_router_prefers_cost_efficient_model_when_budget_constrained() -> None:
    """High token consumption forces the router onto a cheaper profile."""

    config = _make_base_config()
    config.agent_config["Synthesizer"] = AgentConfig(
        preferred_models=["premium", "efficient"],
        token_share=0.5,
        latency_slo_ms=1200.0,
        model="premium",
    )

    metrics = OrchestrationMetrics()
    metrics.record_tokens("Synthesizer", tokens_in=1800, tokens_out=900)
    metrics.record_agent_timing("Synthesizer", duration=0.8)

    selected = metrics.apply_model_routing("Synthesizer", config)

    assert selected == "efficient"
    assert config.agent_config["Synthesizer"].model == "premium"
    assert metrics.routing_agent_recommendations["Synthesizer"] == "efficient"
    assert (
        metrics.routing_decisions[-1].metadata is not None
        and metrics.routing_decisions[-1].metadata.get("applied") is False
    )


def test_budget_router_retains_preferred_model_when_within_budget() -> None:
    """Low token usage leaves the preferred premium profile in place."""

    config = _make_base_config()
    config.agent_config["Contrarian"] = AgentConfig(
        preferred_models=["premium", "efficient"],
        token_share=0.5,
        latency_slo_ms=1200.0,
        model="premium",
    )

    metrics = OrchestrationMetrics()
    metrics.record_tokens("Contrarian", tokens_in=200, tokens_out=150)
    metrics.record_agent_timing("Contrarian", duration=0.4)

    selected = metrics.apply_model_routing("Contrarian", config)

    assert selected == "premium"
    assert config.agent_config["Contrarian"].model == "premium"
    assert metrics.routing_agent_recommendations["Contrarian"] == "premium"


def test_metrics_summary_reports_cost_and_latency() -> None:
    """Summaries expose latency, token averages, and routing savings."""

    config = _make_base_config()
    config.agent_config["Synthesizer"] = AgentConfig(
        preferred_models=["premium", "efficient"],
        token_share=0.5,
        latency_slo_ms=1200.0,
        model="premium",
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
    constraints = summary["model_routing_agent_constraints"]["Synthesizer"]
    recommendations = summary["model_routing_recommendations"]

    assert latency_ms >= 900.0
    assert avg_tokens >= 2600.0
    assert decisions[-1]["selected_model"] == "efficient"
    assert savings["total"] > 0
    assert summary["model_routing_strategy"] == "cost_saver"
    assert decisions[-1]["metadata"]["strategy"] == "cost_saver"
    assert "token_share" in decisions[-1]["metadata"]
    assert decisions[-1]["metadata"]["applied"] is False
    assert constraints["budget_tokens"] >= 2000.0
    assert constraints["latency_slo_ms"] == 1200.0
    assert recommendations["Synthesizer"] == "efficient"


def test_gate_confidence_escalation_registers_override() -> None:
    """Gate heuristics should surface routing overrides for low confidence."""

    config = _make_base_config()
    metrics = OrchestrationMetrics()

    overrides = evaluate_gate_confidence_escalations(
        config=config,
        metrics=metrics,
        heuristics={"retrieval_confidence": 0.4},
    )

    assert overrides
    assert metrics.routing_override_requests
    assert overrides[0].agent == "Synthesizer"
    assert metrics.routing_override_requests[-1].source == "scout_gate"


def test_state_override_consumed_by_metrics(tmp_path) -> None:
    """Planner-provided overrides propagate through metrics into decisions."""

    config = _make_base_config()
    metrics = OrchestrationMetrics()
    state = QueryState(query="planner override")
    state.metadata["routing_overrides"] = [
        {
            "agent": "Synthesizer",
            "model": "premium",
            "reason": "planner_low_confidence",
            "source": "planner",
            "confidence": 0.3,
            "threshold": 0.6,
        }
    ]

    metrics.record_tokens("Synthesizer", tokens_in=250, tokens_out=140)
    metrics.apply_model_routing("Synthesizer", config, state)

    overrides = [
        override
        for override in metrics.routing_override_requests
        if override.source == "planner"
    ]
    assert overrides
    assert overrides[0].requested_model == "premium"


def test_persist_model_routing_metrics(tmp_path) -> None:
    """Routing telemetry is appended to disk for dashboard ingestion."""

    config = _make_base_config()
    metrics = OrchestrationMetrics()
    metrics.record_tokens("Synthesizer", tokens_in=500, tokens_out=250)
    metrics.apply_model_routing("Synthesizer", config)

    output = tmp_path / "routing.jsonl"
    metrics.persist_model_routing_metrics(output)

    lines = output.read_text().strip().splitlines()
    assert lines
    payload = json.loads(lines[-1])
    assert payload["strategy"] == "cost_saver"
    assert payload["decisions"]
