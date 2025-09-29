from typing import Any, Dict, List

import pytest

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils, ScoutGateDecision
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.reasoning import ReasoningMode


class DummySynthesizer:
    """Minimal synthesizer stub for AUTO mode tests."""

    def __init__(self) -> None:
        self.calls: List[int] = []

    def can_execute(self, state, config) -> bool:  # noqa: ANN001 - signature mirrors agent API
        return True

    def execute(self, state, config) -> Dict[str, Any]:  # noqa: ANN001 - signature mirrors agent API
        self.calls.append(state.cycle)
        return {
            "results": {"final_answer": "scout"},
            "claims": [{"type": "synthesis", "content": "scout"}],
        }


def _decision(should_debate: bool, loops: int) -> ScoutGateDecision:
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
    )


def test_auto_mode_returns_direct_answer_when_gate_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """AUTO mode should return the scout answer when the gate exits early."""

    config = ConfigModel(reasoning_mode=ReasoningMode.AUTO, loops=2)
    orchestrator = Orchestrator()
    synth = DummySynthesizer()

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: synth)

    def fake_gate(**kwargs):  # noqa: ANN001 - matches evaluate_scout_gate_policy kwargs
        decision = _decision(False, 1)
        kwargs["state"].metadata["scout_gate"] = decision.__dict__
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
    assert isinstance(samples, list)
    assert len(samples) == config.auto_scout_samples + 1
    for index, sample in enumerate(samples):
        assert sample.get("index") == index
        assert sample.get("answer") == "scout"
        claims = sample.get("claims", [])
        assert isinstance(claims, list)
        assert claims and claims[0].get("content") == "scout"
    assert auto_meta.get("scout_sample_count") == len(samples)
    assert auto_meta.get("scout_agreement") == 1.0
    assert response.metrics.get("scout_samples") == samples


def test_auto_mode_escalates_to_debate_when_gate_requires_loops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AUTO mode should escalate to debate when the gate requests it."""

    config = ConfigModel(reasoning_mode=ReasoningMode.AUTO, loops=3)
    orchestrator = Orchestrator()
    synth = DummySynthesizer()

    monkeypatch.setattr(AgentFactory, "get", lambda name, llm_adapter=None: synth)

    decision = _decision(True, 3)

    def fake_gate(**kwargs):  # noqa: ANN001 - matches evaluate_scout_gate_policy kwargs
        kwargs["state"].metadata["scout_gate"] = decision.__dict__
        return decision

    monkeypatch.setattr(OrchestrationUtils, "evaluate_scout_gate_policy", fake_gate)

    loop_calls: List[int] = []

    def fake_cycle(
        loop: int,
        loops: int,
        agents,
        primus_index: int,
        max_errors: int,
        state,
        config_obj,
        metrics,
        callbacks_map,
        agent_factory,
        storage_manager,
        tracer,
        cb_manager,
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
    assert isinstance(samples, list)
    assert len(samples) == config.auto_scout_samples + 1
    assert auto_meta.get("scout_agreement") == 1.0
