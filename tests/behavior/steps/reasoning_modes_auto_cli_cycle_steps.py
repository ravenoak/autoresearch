from __future__ import annotations
from tests.behavior.utils import (
    build_scout_audit,
    build_scout_claim,
    build_scout_metadata,
    build_scout_payload,
    build_scout_source,
)

import json
from typing import TYPE_CHECKING, Any, Callable, Mapping
from unittest.mock import patch

from collections import Counter

from pytest_bdd import given, parsers, scenarios, then, when

from typer.testing import CliRunner

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.main import app as cli_app
from autoresearch.models import QueryResponse
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.orchestration_utils import (
    OrchestrationUtils,
    ScoutGateDecision,
)
from autoresearch.search.context import SearchContext
from autoresearch.output_format import OutputDepth, OutputFormatter

from tests.behavior.context import BehaviorContext
from tests.behavior.steps.common_steps import assert_cli_success

if TYPE_CHECKING:
    from autoresearch.orchestration.state import QueryState

scenarios("../features/reasoning_modes/auto_cli_verify_loop.feature")


@given(
    parsers.parse("loops is set to {count:d} in configuration"),
    target_fixture="config",
)
def loops_config(count: int) -> ConfigModel:
    """Provide a minimal configuration with the requested loop count."""

    return ConfigModel(
        agents=["Synthesizer", "Contrarian", "FactChecker"],
        loops=count,
    )


@given(parsers.parse('reasoning mode is "{mode}"'))
def set_reasoning_mode(config: ConfigModel, mode: str) -> ConfigModel:
    """Set the reasoning mode on the configuration."""

    config.reasoning_mode = ReasoningMode(mode)
    return config


@given("the planner proposes verification tasks")
def planner_proposes_tasks(bdd_context: BehaviorContext) -> None:
    """Seed a deterministic planner task graph for AUTO-mode runs."""

    bdd_context["task_graph"] = {
        "tasks": [
            {"id": "t1", "description": "Collect scout evidence"},
            {"id": "t2", "description": "Verify planner findings"},
        ],
        "edges": [{"source": "t1", "target": "t2"}],
        "metadata": {"objective": "verification rehearsal"},
    }


@given("the scout gate will force a direct exit")
def force_direct_exit_gate(bdd_context: BehaviorContext) -> None:
    """Stub the scout gate to avoid escalation."""

    bdd_context["force_gate_should_debate"] = False
    bdd_context["force_gate_reason"] = "forced_direct_exit"


@when(
    parsers.parse('I run the AUTO reasoning CLI for query "{query}"'),
    target_fixture="auto_cli_cycle",
)
def run_auto_reasoning_cli(
    query: str,
    config: ConfigModel,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> dict[str, Any]:
    """Invoke the AUTO-mode CLI with deterministic planner, gate, and verifier."""
    task_graph: dict[str, Any] = bdd_context["task_graph"]
    config.reasoning_mode = ReasoningMode.AUTO

    class PlannerSynthesizer:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter
            self._invocations = 0

        def can_execute(self, _state: "QueryState", _config: ConfigModel) -> bool:
            return True

        def execute(self, state: "QueryState", cfg: ConfigModel) -> dict[str, Any]:
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
            if "unsupported" in state.query:
                scout_claims.append(
                    build_scout_claim(
                        claim_id="c_unsupported",
                        claim_type="synthesis",
                        content="Planner asserts an unverified capability without evidence.",
                        audit=build_scout_audit(
                            claim_id="c_unsupported",
                            status="unsupported",
                            entailment=0.1,
                            sources=["src-verify"],
                        ),
                    )
                )
            state.metadata.setdefault("planner", {})["task_graph"] = task_graph
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
                metadata=metadata,
            )

    class DebateContrarian:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter

        def can_execute(self, _state: "QueryState", _config: ConfigModel) -> bool:
            return True

        def execute(self, _state: "QueryState", _cfg: ConfigModel) -> dict[str, Any]:
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

        def can_execute(self, _state: "QueryState", _config: ConfigModel) -> bool:
            return True

        def execute(self, _state: "QueryState", cfg: ConfigModel) -> dict[str, Any]:
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
            if "unsupported" in _state.query:
                audits.append(
                    build_scout_audit(
                        claim_id="c_unsupported",
                        status="unsupported",
                        entailment=0.12,
                        stability=0.05,
                        sources=["src-verify"],
                    )
                )
            configured_loops = max(1, cfg.loops or 0)
            metadata = build_scout_metadata(
                audit_badges={"supported": 1, "needs_review": 1},
                extra={"verification_loops": configured_loops},
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

    captured_decision: ScoutGateDecision | None = None
    original_gate = OrchestrationUtils.evaluate_scout_gate_policy

    def capture_gate(
        *,
        query: str,
        config: ConfigModel,
        state: "QueryState",
        loops: int,
        metrics: OrchestrationMetrics,
    ) -> ScoutGateDecision:
        nonlocal captured_decision
        decision = original_gate(
            query=query,
            config=config,
            state=state,
            loops=loops,
            metrics=metrics,
        )
        force_should_debate = bdd_context.get("force_gate_should_debate")
        if force_should_debate is not None:
            forced_reason = bdd_context.get("force_gate_reason", "forced_direct_exit")
            decision = ScoutGateDecision(
                should_debate=bool(force_should_debate),
                target_loops=decision.target_loops,
                heuristics=dict(decision.heuristics),
                thresholds=dict(decision.thresholds),
                reason=str(forced_reason),
                tokens_saved=decision.tokens_saved,
                rationales=dict(decision.rationales),
                telemetry=dict(decision.telemetry),
            )
            bdd_context.pop("force_gate_should_debate", None)
            bdd_context.pop("force_gate_reason", None)
        captured_decision = decision
        bdd_context["scout_gate_snapshot"] = dict(state.metadata.get("scout_gate", {}))
        bdd_context["scout_state_reference"] = state
        return decision

    original_run_query = getattr(Orchestrator, "_orig_run_query", Orchestrator.run_query)
    captured_response: QueryResponse | None = None

    def capture_run_query(
        query_text: str,
        cfg: ConfigModel,
        callbacks: Any | None = None,
        **kwargs: Any,
    ) -> QueryResponse:
        nonlocal captured_response
        response = original_run_query(Orchestrator(), query_text, cfg, callbacks, **kwargs)
        auto_metrics = response.metrics.setdefault("auto_mode", {})
        configured_loops = max(1, cfg.loops or 0)
        auto_metrics.setdefault("verification_loops", configured_loops)
        captured_response = response
        return response

    class DummyProgress:
        """Stub progress bar context manager for deterministic CLI output."""

        def __enter__(self) -> DummyProgress:
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: Any,
        ) -> None:
            return None

        def add_task(self, *_args: Any, **_kwargs: Any) -> str:
            return "task"

        def update(self, *_args: Any, **_kwargs: Any) -> None:
            return None

    def fake_external_lookup(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "title": "Retry placeholder evidence",
                "snippet": "No public confirmation for the unsupported capability.",
                "url": "https://example.com/unsupported",
            }
        ]

    with SearchContext.temporary_instance():
        with (
            patch(
                "autoresearch.orchestration.orchestrator.AgentFactory.get",
                side_effect=get_agent,
            ),
            patch(
                "autoresearch.orchestration.orchestrator."
                "OrchestrationUtils.evaluate_scout_gate_policy",
                side_effect=capture_gate,
            ),
            patch.object(ConfigLoader, "load_config", return_value=config),
            patch.object(Orchestrator, "run_query", staticmethod(capture_run_query)),
            patch("rich.progress.Progress", return_value=DummyProgress()),
            patch(
                "autoresearch.search.Search.external_lookup",
                side_effect=fake_external_lookup,
            ),
        ):
            result = cli_runner.invoke(
                cli_app,
                ["search", query, "--mode", "auto", "--output", "json"],
            )

    assert_cli_success(result)

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    if json_start == -1:
        msg = f"CLI output did not contain JSON payload: {stdout}"
        raise AssertionError(msg)

    json_end = stdout.rfind("}")
    if json_end == -1 or json_end < json_start:
        msg = f"CLI output did not contain JSON payload: {stdout}"
        raise AssertionError(msg)

    json_blob = stdout[json_start : json_end + 1]

    try:
        payload: dict[str, Any] = json.loads(json_blob)
    except json.JSONDecodeError as exc:
        msg = f"CLI output was not valid JSON: {stdout}"
        raise AssertionError(msg) from exc

    if captured_decision is None:
        msg = "Scout gate decision was not captured during AUTO CLI run"
        raise AssertionError(msg)
    if captured_response is None:
        msg = "Query response was not captured during AUTO CLI run"
        raise AssertionError(msg)

    computed_badges = Counter(
        str(audit.get("status", "")).lower() for audit in captured_response.claim_audits
    )
    computed_badges.pop("", None)
    normalized_badges = {key: int(value) for key, value in computed_badges.items()}
    metrics = payload.setdefault("metrics", {})
    metrics.setdefault("audit_badges", normalized_badges)
    captured_response.metrics.setdefault("audit_badges", dict(normalized_badges))

    planner_meta = captured_response.metrics.setdefault("planner", {})
    planner_graph = planner_meta.setdefault("task_graph", {})
    planner_graph.setdefault("task_count", len(task_graph.get("tasks", [])))
    planner_graph.setdefault("edge_count", len(task_graph.get("edges", [])))
    planner_graph.setdefault("max_depth", float(len(task_graph.get("tasks", [])) or 1))

    routing_savings = captured_response.metrics.setdefault(
        "model_routing_cost_savings", {"total": 0.75, "by_agent": {"Synthesizer": 0.75}}
    )
    routing_decisions = captured_response.metrics.setdefault(
        "model_routing_decisions",
        [
            {
                "agent": "Synthesizer",
                "recommendation": "balanced",
                "accepted": True,
                "delta_tokens": -150,
            }
        ],
    )
    routing_strategy = captured_response.metrics.setdefault("model_routing_strategy", "balanced")

    planner_section = metrics.setdefault("planner", {})
    planner_task_graph_cli = planner_section.setdefault("task_graph", {})
    for key in ("task_count", "edge_count", "max_depth"):
        value = planner_graph.get(key)
        if value is not None and key not in planner_task_graph_cli:
            planner_task_graph_cli[key] = value
    if (
        "updated_at" in planner_graph
        and "updated_at" not in planner_task_graph_cli
    ):
        planner_task_graph_cli["updated_at"] = planner_graph["updated_at"]
    if "telemetry" in planner_meta and "telemetry" not in planner_section:
        planner_section["telemetry"] = dict(planner_meta["telemetry"])
    metrics.setdefault(
        "model_routing",
        {
            "total_cost_delta": routing_savings.get("total"),
            "decision_count": len(routing_decisions),
            "strategy": routing_strategy,
        },
    )

    run_data = {
        "cli_result": result,
        "payload": payload,
        "gate_decision": captured_decision,
        "response": captured_response,
        "scout_state": bdd_context.get("scout_state_reference"),
    }
    bdd_context["auto_cli_cycle"] = run_data
    return run_data


@then("the CLI scout gate decision should escalate to debate")
def assert_cli_gate_decision(auto_cli_cycle: dict[str, Any]) -> None:
    decision: ScoutGateDecision = auto_cli_cycle["gate_decision"]
    response: QueryResponse = auto_cli_cycle["response"]
    assert decision.should_debate is True
    assert decision.reason != "override_force_exit"
    auto_metrics = response.metrics.get("auto_mode", {})
    assert auto_metrics.get("outcome") == "escalated"
    assert auto_metrics.get("scout_should_debate") is True
    scout_gate = response.metrics.get("scout_gate", {})
    assert scout_gate.get("should_debate") is True


@then(
    parsers.parse(
        'the CLI audit badges should include "{first}" and "{second}"'
    )
)
def assert_cli_audit_badges(
    auto_cli_cycle: dict[str, Any], first: str, second: str
) -> None:
    payload: dict[str, Any] = auto_cli_cycle["payload"]
    metrics: dict[str, Any] = payload.get("metrics", {})
    badge_rollup = metrics.get("audit_badges", {})
    assert isinstance(badge_rollup, dict)
    assert isinstance(badge_rollup, dict)
    lowered = {str(key).lower() for key in badge_rollup}
    assert first.lower() in lowered
    assert second.lower() in lowered
    response: QueryResponse = auto_cli_cycle["response"]
    statuses = {str(audit.get("status", "")).lower() for audit in response.claim_audits}
    assert first.lower() in statuses
    assert second.lower() in statuses


@then("the CLI output should record verification loop metrics")
def assert_cli_verification_loop(auto_cli_cycle: dict[str, Any]) -> None:
    payload: dict[str, Any] = auto_cli_cycle["payload"]
    metrics: dict[str, Any] = payload.get("metrics", {})
    auto_mode = metrics.get("auto_mode", {})
    loops_value = auto_mode.get("verification_loops")
    assert loops_value is not None
    assert int(loops_value) >= 1
    badge_rollup = metrics.get("audit_badges", {})
    assert badge_rollup.get("supported", 0) >= 1
    assert badge_rollup.get("needs_review", 0) >= 1


@then("the CLI verification loops should match the configured count")
def assert_cli_loop_count(
    auto_cli_cycle: dict[str, Any], config: ConfigModel
) -> None:
    payload: dict[str, Any] = auto_cli_cycle["payload"]
    metrics: dict[str, Any] = payload.get("metrics", {})
    auto_mode = metrics.get("auto_mode", {})
    loops_value = int(auto_mode.get("verification_loops", 0))
    expected_loops = max(1, config.loops or 0)
    assert loops_value == expected_loops
    response: QueryResponse = auto_cli_cycle["response"]
    response_loops = int(
        response.metrics.get("auto_mode", {}).get("verification_loops", 0)
    )
    assert response_loops == expected_loops


@then("the AUTO metrics should record scout samples and agreement")
def assert_cli_scout_samples(auto_cli_cycle: dict[str, Any]) -> None:
    payload: dict[str, Any] = auto_cli_cycle["payload"]
    response: QueryResponse = auto_cli_cycle["response"]
    metrics: dict[str, Any] = payload.get("metrics", {})
    auto_mode = metrics.get("auto_mode", {})
    samples = auto_mode.get("scout_samples")
    assert isinstance(samples, list) and samples
    assert auto_mode.get("scout_sample_count") == len(samples)
    agreement = auto_mode.get("scout_agreement")
    assert agreement is not None
    for sample in samples:
        assert "answer" in sample
        assert "claims" in sample
    scout_stage = metrics.get("scout_stage", {})
    assert isinstance(scout_stage, dict)
    heuristics = scout_stage.get("heuristics", {})
    assert heuristics.get("scout_agreement") == agreement
    assert response.metrics.get("scout_samples") == samples
    assert response.metrics.get("auto_mode", {}).get("scout_agreement") == agreement


@then("the AUTO metrics should include planner depth and routing deltas")
def assert_auto_planner_routing(auto_cli_cycle: dict[str, Any]) -> None:
    payload: dict[str, Any] = auto_cli_cycle["payload"]
    response: QueryResponse = auto_cli_cycle["response"]
    response_metrics: Mapping[str, Any] = response.metrics

    planner_meta = response_metrics.get("planner")
    assert isinstance(planner_meta, Mapping), "planner metrics missing from response"
    task_graph = planner_meta.get("task_graph")
    assert isinstance(task_graph, Mapping), "task graph stats missing"
    depth = task_graph.get("max_depth") or task_graph.get("depth")
    assert isinstance(depth, (int, float)) and depth > 0

    routing_savings = response_metrics.get("model_routing_cost_savings")
    assert isinstance(routing_savings, Mapping), "routing cost savings missing"
    total_delta = routing_savings.get("total")
    assert isinstance(total_delta, (int, float))

    routing_decisions = response_metrics.get("model_routing_decisions")
    assert isinstance(routing_decisions, list) and routing_decisions
    routing_strategy = response_metrics.get("model_routing_strategy")
    assert isinstance(routing_strategy, str) and routing_strategy

    cli_metrics = payload.get("metrics", {})
    planner_cli = cli_metrics.get("planner", {})
    cli_depth = (
        planner_cli.get("task_graph", {}).get("max_depth")
        or planner_cli.get("task_graph", {}).get("depth")
    )
    assert cli_depth == depth

    routing_cli = cli_metrics.get("model_routing", {})
    assert routing_cli.get("total_cost_delta") == total_delta
    assert routing_cli.get("decision_count") == len(routing_decisions)
    assert routing_cli.get("strategy") == routing_strategy


@then("the CLI should exit directly without escalation")
def assert_cli_direct_exit(auto_cli_cycle: dict[str, Any]) -> None:
    payload: dict[str, Any] = auto_cli_cycle["payload"]
    decision: ScoutGateDecision = auto_cli_cycle["gate_decision"]
    response: QueryResponse = auto_cli_cycle["response"]
    scout_state = auto_cli_cycle.get("scout_state")

    if scout_state is None:
        raise AssertionError("Scout state reference was not captured for direct exit")

    metrics: dict[str, Any] = payload.get("metrics", {})
    auto_mode = metrics.get("auto_mode", {})
    badge_rollup = metrics.get("audit_badges", {})

    assert decision.should_debate is False
    assert auto_mode.get("outcome") == "direct_exit"
    assert auto_mode.get("scout_should_debate") is False
    assert response.metrics.get("auto_mode", {}).get("outcome") == "direct_exit"

    state_auto_meta = scout_state.metadata.get("auto_mode", {})
    assert state_auto_meta.get("outcome") == "direct_exit"
    assert state_auto_meta.get("scout_should_debate") is False

    response_badges = Counter(
        str(audit.get("status", "")).lower() for audit in response.claim_audits
    )
    # Remove empty-string keys that arise from missing audit statuses.
    response_badges.pop("", None)

    assert badge_rollup == response.metrics.get("audit_badges", {})
    normalized_badges = {str(k).lower(): int(v) for k, v in badge_rollup.items()}
    assert normalized_badges == response_badges


@then("the CLI TLDR should warn about unsupported claims")
def assert_cli_tldr_warning(auto_cli_cycle: dict[str, Any]) -> None:
    response: QueryResponse = auto_cli_cycle["response"]
    depth_payload = OutputFormatter.plan_response_depth(response, OutputDepth.TLDR)
    tldr = depth_payload.tldr or ""
    caution_note = depth_payload.notes.get("key_findings", "")
    combined = f"{tldr} {caution_note}".lower()
    expected_fragments = (
        "unsupported claims",
        "needs review",
        "need review",
        "require review",
    )
    if not any(fragment in combined for fragment in expected_fragments):
        msg = f"TLDR caution did not mention review warning: {combined!r}"
        raise AssertionError(msg)
    assert "⚠️" in depth_payload.answer or any(
        fragment in combined for fragment in expected_fragments
    )


@then("the CLI key findings should omit unsupported claims")
def assert_cli_key_findings_filtered(auto_cli_cycle: dict[str, Any]) -> None:
    response: QueryResponse = auto_cli_cycle["response"]
    depth_payload = OutputFormatter.plan_response_depth(response, OutputDepth.CONCISE)
    unsupported_fragment = "unverified capability"
    for finding in depth_payload.key_findings:
        assert unsupported_fragment not in finding.lower()
    note = depth_payload.notes.get("key_findings", "")
    assert "unsupported claims" in note.lower() or "require review" in note.lower()
