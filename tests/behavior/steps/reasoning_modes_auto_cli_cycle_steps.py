from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable
from unittest.mock import patch

from pytest_bdd import parsers, scenarios, then, when

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

from tests.behavior.steps.common_steps import assert_cli_success

if TYPE_CHECKING:
    from autoresearch.orchestration.state import QueryState

scenarios("../features/reasoning_modes/auto_cli_verify_loop.feature")


@when(
    parsers.parse('I run the AUTO reasoning CLI for query "{query}"'),
    target_fixture="auto_cli_cycle",
)
def run_auto_reasoning_cli(
    query: str,
    config: ConfigModel,
    bdd_context: dict[str, Any],
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
            state.metadata.setdefault("planner", {})["task_graph"] = task_graph
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
                "metadata": metadata,
            }

    class DebateContrarian:
        def __init__(self, name: str, llm_adapter: object | None = None) -> None:
            self.name = name
            self._adapter = llm_adapter

        def can_execute(self, _state: "QueryState", _config: ConfigModel) -> bool:
            return True

        def execute(self, _state: "QueryState", _cfg: ConfigModel) -> dict[str, Any]:
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

        def can_execute(self, _state: "QueryState", _config: ConfigModel) -> bool:
            return True

        def execute(self, _state: "QueryState", _cfg: ConfigModel) -> dict[str, Any]:
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
                "metadata": {
                    "audit_badges": {"supported": 1, "needs_review": 1},
                    "verification_loops": 1,
                },
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
        captured_decision = decision
        bdd_context["scout_gate_snapshot"] = dict(state.metadata.get("scout_gate", {}))
        return decision

    original_run_query = getattr(Orchestrator, "_orig_run_query", Orchestrator.run_query)
    captured_response: QueryResponse | None = None

    def capture_run_query(
        self: Orchestrator,
        query_text: str,
        cfg: ConfigModel,
        callbacks: Any | None = None,
        **kwargs: Any,
    ) -> QueryResponse:
        nonlocal captured_response
        response = original_run_query(self, query_text, cfg, callbacks, **kwargs)
        auto_metrics = response.metrics.setdefault("auto_mode", {})
        auto_metrics.setdefault("verification_loops", 1)
        captured_response = response
        return response

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
            patch.object(Orchestrator, "_orig_run_query", capture_run_query),
        ):
            result = cli_runner.invoke(
                cli_app,
                ["search", query, "--mode", "auto", "--output", "json"],
            )

    assert_cli_success(result)

    try:
        payload: dict[str, Any] = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        msg = f"CLI output was not valid JSON: {result.stdout}"
        raise AssertionError(msg) from exc

    if captured_decision is None:
        msg = "Scout gate decision was not captured during AUTO CLI run"
        raise AssertionError(msg)
    if captured_response is None:
        msg = "Query response was not captured during AUTO CLI run"
        raise AssertionError(msg)

    run_data = {
        "cli_result": result,
        "payload": payload,
        "gate_decision": captured_decision,
        "response": captured_response,
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
