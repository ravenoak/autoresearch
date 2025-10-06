from collections.abc import Mapping
from typing import Any, Dict, List

import pytest
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils, ScoutGateDecision
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState


class DummySynthesizer:
    """Minimal synthesizer stub for AUTO mode tests."""

    def __init__(self) -> None:
        self.calls: list[int] = []

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        return True

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, Any]:
        self.calls.append(state.cycle)
        return {
            "results": {"final_answer": "scout"},
            "claims": [{"type": "synthesis", "content": "scout"}],
        }


def _decision(should_debate: bool, loops: int) -> ScoutGateDecision:
    coverage = {"total_claims": 1, "audited_claims": 1, "audit_records": 1, "coverage_ratio": 1.0}
    agreement = {
        "score": 1.0,
        "mean": 1.0,
        "min": 1.0,
        "max": 1.0,
        "sample_count": 1,
        "pairwise_scores": [1.0],
        "basis": "answer_claim_tokens",
    }
    outcome = "debate" if should_debate else "scout_exit"
    return ScoutGateDecision(
        should_debate=should_debate,
        target_loops=loops,
        heuristics={
            "retrieval_overlap": 0.2,
            "nli_conflict": 0.1,
            "complexity": 0.1,
            "coverage_gap": 0.0,
            "retrieval_confidence": 1.0,
            "graph_contradiction": 0.0,
            "graph_similarity": 1.0,
            "scout_agreement": 1.0,
        },
        thresholds={
            "retrieval_overlap": 0.6,
            "nli_conflict": 0.3,
            "complexity": 0.5,
            "coverage_gap": 0.25,
            "retrieval_confidence": 0.5,
            "graph_contradiction": 0.25,
            "graph_similarity": 0.0,
            "scout_agreement": 0.7,
        },
        reason="test",  # pragma: no cover - metadata only
        tokens_saved=0,
        telemetry={
            "coverage": coverage,
            "coverage_ratio": 1.0,
            "scout_agreement": agreement,
            "decision_outcome": outcome,
        },
    )


def test_auto_mode_returns_direct_answer_when_gate_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """AUTO mode should return the scout answer when the gate exits early."""

    config = ConfigModel(reasoning_mode=ReasoningMode.AUTO, loops=2)
    orchestrator = Orchestrator()
    synth = DummySynthesizer()

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: synth)

    def fake_gate(**kwargs: Any) -> ScoutGateDecision:
        decision = _decision(False, 1)
        state = kwargs.get("state")
        assert state is not None
        state.metadata["scout_gate"] = decision.__dict__
        return decision

    monkeypatch.setattr(OrchestrationUtils, "evaluate_scout_gate_policy", fake_gate)
    monkeypatch.setattr(
        OrchestrationUtils,
        "execute_cycle",
        lambda *args, **kwargs: pytest.fail("execute_cycle should not run when gate exits"),
    )

    response = orchestrator.run_query("auto exit", config)

    assert response.answer == "scout"
    assert len(synth.calls) == config.auto_scout_samples + 1
    assert config.reasoning_mode == ReasoningMode.AUTO
    auto_meta = response.metrics.get("auto_mode", {})
    assert auto_meta.get("outcome") == "direct_exit"
    assert auto_meta.get("scout_answer") == "scout"
    samples = auto_meta.get("scout_samples")
    assert isinstance(samples, tuple)
    assert len(samples) == config.auto_scout_samples + 1
    for index, sample in enumerate(samples):
        assert isinstance(sample, Mapping)
        assert sample.get("index") == index
        assert sample.get("answer") == "scout"
        claims = sample.get("claims")
        assert isinstance(claims, tuple)
        assert claims, "scout samples must preserve non-empty claim payloads"
        first_claim = claims[0]
        assert isinstance(first_claim, Mapping)
        assert len(first_claim) > 0
        assert first_claim.get("content") == "scout"
        with pytest.raises(TypeError):
            first_claim["content"] = "mutated"  # type: ignore[index]
    assert auto_meta.get("scout_sample_count") == len(samples)
    assert auto_meta.get("scout_agreement") == 1.0
    assert response.metrics.get("scout_samples") == samples
    gate_snapshot = response.metrics.get("scout_gate", {})
    telemetry = gate_snapshot.get("telemetry", {})
    assert telemetry.get("coverage_ratio") == 1.0
    assert telemetry.get("decision_outcome") == "scout_exit"
    agreement_meta = telemetry.get("scout_agreement", {})
    assert agreement_meta.get("score") == 1.0


def test_auto_mode_escalates_to_debate_when_gate_requires_loops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AUTO mode should escalate to debate when the gate requests it."""

    config = ConfigModel(reasoning_mode=ReasoningMode.AUTO, loops=3)
    orchestrator = Orchestrator()
    synth = DummySynthesizer()

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: synth)

    decision = _decision(True, 3)

    def fake_gate(**kwargs: Any) -> ScoutGateDecision:
        state = kwargs.get("state")
        assert state is not None
        state.metadata["scout_gate"] = decision.__dict__
        return decision

    monkeypatch.setattr(OrchestrationUtils, "evaluate_scout_gate_policy", fake_gate)

    loop_calls: list[int] = []

    def fake_cycle(
        loop: int,
        loops: int,
        agents: Any,
        primus_index: int,
        max_errors: int,
        state: QueryState,
        config_obj: ConfigModel,
        metrics: OrchestrationMetrics,
        callbacks_map: Any,
        agent_factory: Any,
        storage_manager: Any,
        tracer: Any,
        cb_manager: Any,
    ) -> int:
        loop_calls.append(loop)
        state.results["final_answer"] = f"debate-{loop}"
        return primus_index

    monkeypatch.setattr(OrchestrationUtils, "execute_cycle", fake_cycle)

    response = orchestrator.run_query("auto debate", config)

    assert len(synth.calls) == config.auto_scout_samples + 1
    assert loop_calls == list(range(decision.target_loops))
    assert response.answer == f"debate-{loop_calls[-1]}"
    assert config.reasoning_mode == ReasoningMode.AUTO
    auto_meta = response.metrics.get("auto_mode", {})
    assert auto_meta.get("outcome") == "escalated"
    assert auto_meta.get("scout_answer") == "scout"
    samples = auto_meta.get("scout_samples")
    assert isinstance(samples, tuple)
    assert len(samples) == config.auto_scout_samples + 1
    for sample in samples:
        assert isinstance(sample, Mapping)
        claims = sample.get("claims")
        assert isinstance(claims, tuple)
        assert claims, "escalation path must capture non-empty claim payloads"
        for claim in claims:
            assert isinstance(claim, Mapping)
            assert len(claim) > 0
    assert auto_meta.get("scout_agreement") == 1.0
    gate_snapshot = response.metrics.get("scout_gate", {})
    telemetry = gate_snapshot.get("telemetry", {})
    assert telemetry.get("coverage_ratio") == 1.0
    assert telemetry.get("decision_outcome") == "debate"
    agreement_meta = telemetry.get("scout_agreement", {})
    assert agreement_meta.get("score") == 1.0


def test_metrics_record_gate_decision_telemetry() -> None:
    """`OrchestrationMetrics` should persist new scout gate telemetry fields."""

    metrics = OrchestrationMetrics()
    decision = _decision(True, 2)

    metrics.record_gate_decision(decision)

    assert metrics.gate_coverage_ratios == [1.0]
    assert metrics.gate_decision_outcomes == ["debate"]
    assert metrics.gate_agreement_stats[0]["score"] == 1.0
