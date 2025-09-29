from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from pytest_bdd import given, parsers, scenarios, then, when
from unittest.mock import patch

from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.orchestration_utils import (
    OrchestrationUtils,
    ScoutGateDecision,
)
from autoresearch.search.context import SearchContext

if TYPE_CHECKING:
    from autoresearch.orchestration.state import QueryState


scenarios("../features/reasoning_modes/auto_planner_cycle.feature")


@given("the planner proposes verification tasks")
def planner_verification_tasks(bdd_context: dict[str, Any]) -> None:
    bdd_context["task_graph"] = {
        "tasks": [
            {
                "id": "plan",
                "question": "Outline verification agenda",
                "tools": ["planner"],
            },
            {
                "id": "verify",
                "question": "Verify conflicting statements",
                "tools": ["fact_checker"],
            },
        ],
        "edges": [
            {"source": "plan", "target": "verify"},
        ],
        "objectives": ["Document audit outcomes"],
        "exit_criteria": ["Badges recorded"],
    }


@when(
    parsers.parse('I run the auto planner cycle for query "{query}"'),
    target_fixture="auto_cycle_result",
)
def run_auto_planner_cycle(
    query: str,
    config: ConfigModel,
    bdd_context: dict[str, Any],
) -> dict[str, Any]:
    task_graph: dict[str, Any] = bdd_context["task_graph"]

    class PlannerSynthesizer:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter
            self._invocations = 0

        def can_execute(self, _state: QueryState, _config: ConfigModel) -> bool:
            return True

        def execute(self, state: QueryState, cfg: ConfigModel) -> dict[str, Any]:
            self._invocations += 1
            metadata = {
                "scout_retrieval_sets": [
                    ["src-plan", "src-verify"],
                    ["src-verify", "src-analysis"],
                ],
                "scout_complexity_features": {
                    "hops": 2,
                    "entities": ["planner", "verifier"],
                    "clauses": 4,
                },
                "scout_entailment_scores": [
                    {"support": 0.32, "conflict": 0.68},
                    {"support": 0.30, "conflict": 0.70},
                ],
            }
            scout_claims = [
                {
                    "id": "c1",
                    "type": "thesis",
                    "content": "Planner identifies conflicting statements to verify.",
                    "audit": {
                        "claim_id": "c1",
                        "status": "supported",
                        "entailment": 0.82,
                        "sources": ["src-plan"],
                    },
                },
                {
                    "id": "c2",
                    "type": "antithesis",
                    "content": "Follow-up evidence remains unresolved.",
                },
            ]
            scout_sources = [
                {
                    "source_id": "src-plan",
                    "title": "Planning memo",
                    "snippet": "Plan verification tasks",
                    "backend": "duckduckgo",
                    "url": "https://example.com/plan",
                },
                {
                    "source_id": "src-verify",
                    "title": "Verification checklist",
                    "snippet": "Needs follow-up",
                    "backend": "serper",
                    "url": "https://example.com/verify",
                },
            ]
            if cfg.reasoning_mode == ReasoningMode.DIRECT:
                return {
                    "claims": scout_claims,
                    "sources": scout_sources,
                    "metadata": metadata,
                    "results": {
                        "final_answer": "Initial scout summary",
                        "task_graph": task_graph,
                    },
                }
            return {
                "claims": [
                    {
                        "id": "c3",
                        "type": "synthesis",
                        "content": "Synthesis integrates planner and verifier evidence.",
                    }
                ],
                "results": {
                    "final_answer": "Verified synthesis with planner context.",
                    "task_graph": task_graph,
                },
            }

    class DebateContrarian:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter

        def can_execute(self, _state: QueryState, _config: ConfigModel) -> bool:
            return True

        def execute(self, _state: QueryState, _cfg: ConfigModel) -> dict[str, Any]:
            return {
                "claims": [
                    {
                        "id": "c2",
                        "type": "antithesis",
                        "content": "Contrarian flags remaining verification gaps.",
                        "audit": {
                            "claim_id": "c2",
                            "status": "needs_review",
                            "entailment": 0.44,
                            "sources": ["src-verify"],
                        },
                    }
                ],
                "results": {"contrarian_note": "Verification gaps recorded"},
            }

    class VerifierFactChecker:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter

        def can_execute(self, _state: QueryState, _config: ConfigModel) -> bool:
            return True

        def execute(self, _state: QueryState, _cfg: ConfigModel) -> dict[str, Any]:
            audits = [
                {
                    "claim_id": "c1",
                    "status": "supported",
                    "entailment": 0.82,
                    "stability": 0.91,
                    "sources": ["src-plan"],
                },
                {
                    "claim_id": "c2",
                    "status": "needs_review",
                    "entailment": 0.44,
                    "stability": 0.50,
                    "sources": ["src-verify"],
                },
            ]
            return {
                "claim_audits": audits,
                "metadata": {"audit_badges": {"supported": 1, "needs_review": 1}},
                "results": {"verification_summary": "Audit badges recorded"},
            }

    agent_builders: dict[str, Callable[[str, object | None], object]] = {
        "Synthesizer": lambda name, adapter: PlannerSynthesizer(name, adapter),
        "Contrarian": lambda name, adapter: DebateContrarian(name, adapter),
        "FactChecker": lambda name, adapter: VerifierFactChecker(name, adapter),
    }
    agent_instances: dict[str, object] = {}

    def get_agent(name: str, llm_adapter: object | None = None) -> object:
        if name not in agent_builders:
            msg = f"Unexpected agent requested: {name}"
            raise ValueError(msg)
        if name not in agent_instances:
            agent_instances[name] = agent_builders[name](name, llm_adapter)
        return agent_instances[name]

    gate_decisions: list[ScoutGateDecision] = []
    original_gate = OrchestrationUtils.evaluate_scout_gate_policy

    def capture_gate(
        *,
        query: str,
        config: ConfigModel,
        state: QueryState,
        loops: int,
        metrics: OrchestrationMetrics,
    ) -> ScoutGateDecision:
        decision = original_gate(
            query=query,
            config=config,
            state=state,
            loops=loops,
            metrics=metrics,
        )
        gate_decisions.append(decision)
        bdd_context["scout_gate_snapshot"] = dict(state.metadata.get("scout_gate", {}))
        return decision

    with SearchContext.temporary_instance():
        with patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=get_agent,
        ), patch(
            "autoresearch.orchestration.orchestrator.OrchestrationUtils.evaluate_scout_gate_policy",
            side_effect=capture_gate,
        ):
            response: QueryResponse = Orchestrator.run_query(query, config)

    if not gate_decisions:
        msg = "Scout gate decision was not captured during AUTO run"
        raise AssertionError(msg)

    result: dict[str, Any] = {
        "response": response,
        "gate_decision": gate_decisions[-1],
    }
    bdd_context["auto_cycle"] = result
    return result


@then("the scout gate decision should escalate to debate")
def assert_gate_escalation(auto_cycle_result: dict[str, Any]) -> None:
    response: QueryResponse = auto_cycle_result["response"]
    decision: ScoutGateDecision = auto_cycle_result["gate_decision"]
    assert decision.should_debate is True
    assert decision.reason != "override_force_exit"
    auto_meta = response.metrics.get("auto_mode", {})
    assert auto_meta.get("outcome") == "escalated"
    assert auto_meta.get("scout_should_debate") is True
    scout_gate = response.metrics.get("scout_gate", {})
    assert scout_gate.get("should_debate") is True
    heuristics = response.metrics.get("scout_stage", {}).get("heuristics", {})
    assert float(heuristics.get("coverage_gap", 0.0)) >= 0.25


@then(
    parsers.parse(
        'the auto mode audit badges should include "{first}" and "{second}"'
    )
)
def assert_audit_badges(
    auto_cycle_result: dict[str, Any], first: str, second: str
) -> None:
    response: QueryResponse = auto_cycle_result["response"]
    statuses = {str(audit.get("status", "")).lower() for audit in response.claim_audits}
    assert first.lower() in statuses
    assert second.lower() in statuses
    badge_rollup = response.metrics.get("audit_badges")
    assert isinstance(badge_rollup, dict)
    assert first.lower() in {key.lower() for key in badge_rollup}
    assert second.lower() in {key.lower() for key in badge_rollup}


@then("the planner task graph snapshot should include verification goals")
def assert_planner_snapshot(
    auto_cycle_result: dict[str, Any], bdd_context: dict[str, Any]
) -> None:
    response: QueryResponse = auto_cycle_result["response"]
    assert response.task_graph is not None
    tasks = response.task_graph.get("tasks", [])
    task_ids = {str(task.get("id")) for task in tasks if isinstance(task, dict)}
    assert {"plan", "verify"}.issubset(task_ids)
    planner_meta = response.metrics.get("planner", {})
    telemetry = planner_meta.get("telemetry", {})
    expected_objectives = bdd_context["task_graph"].get("objectives")
    assert telemetry.get("objectives") == expected_objectives
