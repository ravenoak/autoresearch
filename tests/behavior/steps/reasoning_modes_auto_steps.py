from __future__ import annotations
from tests.behavior.utils import (
    as_payload,
    build_scout_audit,
    build_scout_claim,
    build_scout_metadata,
    build_scout_payload,
    build_scout_source,
)

import json
from typing import Any, Callable

from pytest_bdd import given, parsers, scenarios, then, when
from unittest.mock import patch

from autoresearch.agents.specialized.planner import PlannerAgent
from autoresearch.config.loader import temporary_config
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.orchestration_utils import (
    OrchestrationUtils,
    ScoutGateDecision,
)
from autoresearch.orchestration.state import QueryState
from autoresearch.search.context import SearchContext

from tests.behavior.context import BehaviorContext
from tests.helpers import ConfigModelStub, make_config_model

ConfigLike = ConfigModel | ConfigModelStub


scenarios("../features/reasoning_modes/auto_planner_cycle.feature")
scenarios("../features/reasoning_modes/planner_graph_conditioning.feature")


@given(
    parsers.parse("loops is set to {count:d} in configuration"),
    target_fixture="config",
)
def configure_loops(count: int) -> ConfigLike:
    """Provide a configurable AUTO-mode stub with deterministic agents."""

    config = make_config_model(loops=count)
    config.agents = ["Synthesizer", "Contrarian", "FactChecker"]
    config.reasoning_mode = ReasoningMode.AUTO
    return config


@given(parsers.parse('reasoning mode is "{mode}"'))
def configure_reasoning_mode(config: ConfigLike, mode: str) -> ConfigLike:
    config.reasoning_mode = ReasoningMode(mode)
    return config


@given("the planner proposes verification tasks")
def planner_verification_tasks(bdd_context: BehaviorContext) -> None:
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
    config: ConfigLike,
    bdd_context: BehaviorContext,
) -> dict[str, Any]:
    task_graph: dict[str, Any] = bdd_context["task_graph"]

    class PlannerSynthesizer:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter
            self._invocations = 0

        def can_execute(self, _state: QueryState, _config: ConfigLike) -> bool:
            return True

        def execute(self, state: QueryState, cfg: ConfigLike) -> dict[str, Any]:
            self._invocations += 1
            metadata = build_scout_metadata(
                retrieval_sets=[
                    ["src-plan", "src-verify"],
                    ["src-verify", "src-analysis"],
                ],
                complexity_features={
                    "hops": 2,
                    "entities": ["planner", "verifier"],
                    "clauses": 4,
                },
                entailment_scores=[
                    {"support": 0.32, "conflict": 0.68},
                    {"support": 0.30, "conflict": 0.70},
                ],
            )
            scout_claims = [
                build_scout_claim(
                    claim_id="c1",
                    claim_type="thesis",
                    content="Planner identifies conflicting statements to verify.",
                    audit=build_scout_audit(
                        claim_id="c1",
                        status="supported",
                        entailment=0.82,
                        sources=["src-plan"],
                    ),
                ),
                build_scout_claim(
                    claim_id="c2",
                    claim_type="antithesis",
                    content="Follow-up evidence remains unresolved.",
                ),
            ]
            scout_sources = [
                build_scout_source(
                    source_id="src-plan",
                    title="Planning memo",
                    snippet="Plan verification tasks",
                    backend="duckduckgo",
                    url="https://example.com/plan",
                ),
                build_scout_source(
                    source_id="src-verify",
                    title="Verification checklist",
                    snippet="Needs follow-up",
                    backend="serper",
                    url="https://example.com/verify",
                ),
            ]
            if cfg.reasoning_mode == ReasoningMode.DIRECT:
                return build_scout_payload(
                    claims=scout_claims,
                    sources=scout_sources,
                    metadata=metadata,
                    results={
                        "final_answer": "Initial scout summary",
                        "task_graph": task_graph,
                    },
                )
            return build_scout_payload(
                claims=[
                    build_scout_claim(
                        claim_id="c3",
                        claim_type="synthesis",
                        content="Synthesis integrates planner and verifier evidence.",
                    )
                ],
                results={
                    "final_answer": "Verified synthesis with planner context.",
                    "task_graph": task_graph,
                },
            )

    class DebateContrarian:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter

        def can_execute(self, _state: QueryState, _config: ConfigLike) -> bool:
            return True

        def execute(self, _state: QueryState, _cfg: ConfigLike) -> dict[str, Any]:
            return build_scout_payload(
                claims=[
                    build_scout_claim(
                        claim_id="c2",
                        claim_type="antithesis",
                        content="Contrarian flags remaining verification gaps.",
                        audit=build_scout_audit(
                            claim_id="c2",
                            status="needs_review",
                            entailment=0.44,
                            sources=["src-verify"],
                        ),
                    )
                ],
                results={"contrarian_note": "Verification gaps recorded"},
            )

    class VerifierFactChecker:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter

        def can_execute(self, _state: QueryState, _config: ConfigLike) -> bool:
            return True

        def execute(self, _state: QueryState, _cfg: ConfigLike) -> dict[str, Any]:
            audits = [
                build_scout_audit(
                    claim_id="c1",
                    status="supported",
                    entailment=0.82,
                    stability=0.91,
                    sources=["src-plan"],
                ),
                build_scout_audit(
                    claim_id="c2",
                    status="needs_review",
                    entailment=0.44,
                    stability=0.50,
                    sources=["src-verify"],
                ),
            ]
            metadata = build_scout_metadata(
                audit_badges={"supported": 1, "needs_review": 1}
            )
            return build_scout_payload(
                claim_audits=audits,
                metadata=metadata,
                results={"verification_summary": "Audit badges recorded"},
            )

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
        config: ConfigLike,
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


@then("the AUTO metrics should record scout samples and agreement")
def assert_auto_scout_samples(auto_cycle_result: dict[str, Any]) -> None:
    response: QueryResponse = auto_cycle_result["response"]
    auto_mode = response.metrics.get("auto_mode", {})
    samples = auto_mode.get("scout_samples")
    assert isinstance(samples, list) and samples
    assert auto_mode.get("scout_sample_count") == len(samples)
    agreement = auto_mode.get("scout_agreement")
    assert agreement is not None
    heuristics = response.metrics.get("scout_stage", {}).get("heuristics", {})
    assert heuristics.get("scout_agreement") == agreement
    assert response.metrics.get("scout_samples") == samples


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
    auto_cycle_result: dict[str, Any], bdd_context: BehaviorContext
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


@given("planner graph conditioning is enabled in configuration")
def enable_planner_graph_conditioning(config: ConfigModel) -> ConfigModel:
    stub = make_config_model(
        context_overrides={"planner_graph_conditioning": True}
    )
    context_stub = stub.search.context_aware
    context_cfg = config.search.context_aware
    context_cfg.enabled = context_stub.enabled
    context_cfg.use_query_expansion = context_stub.use_query_expansion
    context_cfg.expansion_factor = context_stub.expansion_factor
    context_cfg.use_search_history = context_stub.use_search_history
    context_cfg.max_history_items = context_stub.max_history_items
    context_cfg.graph_signal_weight = context_stub.graph_signal_weight
    context_cfg.planner_graph_conditioning = (
        context_stub.planner_graph_conditioning
    )
    context_cfg.graph_pipeline_enabled = True
    config.reasoning_mode = ReasoningMode.DIRECT
    return config


@given("the knowledge graph metadata includes contradictions and neighbours")
def configure_graph_metadata(bdd_context: BehaviorContext) -> None:
    stage_metadata = {
        "contradictions": {
            "raw_score": 0.8,
            "weighted_score": 0.4,
            "items": [
                {
                    "subject": "Battery pack",
                    "predicate": "conflicts_with",
                    "objects": ["Lab stress test"],
                },
                {
                    "subject": "Battery pack",
                    "predicate": "aligns_with",
                    "objects": ["Spec sheet summary"],
                },
            ],
        },
        "neighbors": {
            "Battery pack": [
                {
                    "predicate": "supported_by",
                    "target": "Thermal audit",
                    "direction": "out",
                },
                {
                    "predicate": "contradicted_by",
                    "target": "Field report",
                    "direction": "in",
                },
            ],
            "Graph driver": [
                {
                    "predicate": "linked_to",
                    "target": "Sensor log",
                    "direction": "both",
                }
            ],
        },
        "similarity": {
            "raw_score": 0.6,
            "weighted_score": 0.3,
        },
        "paths": [["Battery pack", "Graph driver", "Sensor log"]],
    }
    summary = {
        "sources": [
            "https://example.com/thermal-audit",
            "https://example.com/field-report",
        ],
        "provenance": [
            {"subject": "Battery pack", "object": "Thermal audit"},
            {"subject": "Graph driver", "object": "Sensor log"},
        ],
    }
    bdd_context["graph_stage_metadata"] = stage_metadata
    bdd_context["graph_summary"] = summary


@when(
    parsers.parse('I execute the planner for query "{query}"'),
    target_fixture="planner_graph_conditioning_result",
)
def execute_planner_with_graph_context(
    query: str,
    config: ConfigLike,
    bdd_context: BehaviorContext,
    monkeypatch,
) -> dict[str, Any]:
    stage_metadata = bdd_context["graph_stage_metadata"]
    graph_summary = bdd_context["graph_summary"]
    adapter_prompts: list[str] = []

    class StaticAdapter:
        def generate(self, prompt: str, model: str | None = None) -> str:
            adapter_prompts.append(prompt)
            plan_payload = {
                "objectives": [
                    "Resolve contradictory evidence",
                    "Prioritise graph-supported leads",
                ],
                "exit_criteria": [
                    "Conflicts reconciled",
                    "Neighbour review complete",
                ],
                "tasks": [
                    {
                        "id": "graph-review",
                        "question": "Compare conflicting neighbours",
                        "objectives": [
                            "List contradictory triples",
                            "Summarise supporting neighbours",
                        ],
                        "tools": ["search", "graph"],
                        "exit_criteria": ["Contradictions resolved"],
                        "explanation": "Leverage graph conditioning cues.",
                    }
                ],
                "edges": [],
                "metadata": {"version": 1, "notes": "graph conditioned plan"},
            }
            return json.dumps(plan_payload)

    adapter = StaticAdapter()
    monkeypatch.setattr(
        PlannerAgent,
        "get_adapter",
        lambda self, cfg: adapter,
    )
    monkeypatch.setattr(
        PlannerAgent,
        "get_model",
        lambda self, cfg: "test-model",
    )
    planner = PlannerAgent()
    state = QueryState(query=query)

    with temporary_config(config):
        with SearchContext.temporary_instance() as search_context:
            search_context._graph_stage_metadata = dict(stage_metadata)
            search_context._graph_summary = dict(graph_summary)
            result = planner.execute(state, config)

    trace_entries = [
        entry for entry in state.react_log if entry.get("event") == "planner.trace"
    ]
    if not trace_entries:
        msg = "Planner trace was not recorded during graph conditioning run"
        raise AssertionError(msg)
    prompt = trace_entries[-1]["payload"]["prompt"]
    telemetry = state.metadata.get("planner", {}).get("telemetry", {})

    return as_payload({
        "state": state,
        "result": result,
        "prompt": prompt,
        "telemetry": telemetry,
        "adapter_prompts": adapter_prompts,
    })


@then("the planner prompt should include contradiction and neighbour cues")
def assert_planner_prompt_cues(
    planner_graph_conditioning_result: dict[str, Any]
) -> None:
    prompt = planner_graph_conditioning_result["prompt"]
    assert "Knowledge graph signals:" in prompt
    assert "- Contradiction score: 0.40 (raw 0.80)" in prompt
    assert "Contradictory findings:" in prompt
    assert "    - Battery pack --conflicts_with--> Lab stress test" in prompt
    assert "- Representative neighbours:" in prompt
    assert "  - Battery pack → (supported_by) Thermal audit" in prompt
    assert "  - Battery pack ← (contradicted_by) Field report" in prompt
    assert "  - Graph driver ↔ (linked_to) Sensor log" in prompt


@then("the planner telemetry should record objectives and tasks")
def assert_planner_graph_telemetry(
    planner_graph_conditioning_result: dict[str, Any]
) -> None:
    telemetry = planner_graph_conditioning_result["telemetry"]
    tasks = telemetry.get("tasks", [])
    assert tasks, "Planner telemetry should record task snapshots"
    first_task = tasks[0]
    assert first_task.get("id") == "graph-review"
    assert first_task.get("explanation") == "Leverage graph conditioning cues."
    assert first_task.get("exit_criteria") == ["Contradictions resolved"]
    assert first_task.get("objectives") == [
        "List contradictory triples",
        "Summarise supporting neighbours",
    ]
