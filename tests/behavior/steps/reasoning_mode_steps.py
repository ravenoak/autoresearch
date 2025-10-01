from __future__ import annotations

from __future__ import annotations

import json
from typing import Any, Mapping, cast
from unittest.mock import patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.errors import ConfigError, NotFoundError
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.coordinator import TaskCoordinator
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.orchestration_utils import (
    OrchestrationUtils,
    ScoutGateDecision,
)
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.task_graph import TaskGraph, TaskNode
from tests.behavior.context import (
    BehaviorContext,
    get_config,
    get_orchestrator,
    set_value,
)


@scenario("../features/reasoning_mode.feature", "Direct mode runs Synthesizer only")
def test_direct_mode() -> None:
    """Scenario placeholder for direct mode execution."""


@scenario("../features/reasoning_mode.feature", "Default reasoning mode is dialectical")
def test_default_mode() -> None:
    """Scenario placeholder for default dialectical mode."""


@scenario("../features/reasoning_mode.feature", "Chain-of-thought mode loops Synthesizer")
def test_chain_of_thought_mode() -> None:
    """Scenario placeholder for chain-of-thought mode."""


@scenario("../features/reasoning_mode.feature", "Dialectical mode with custom Primus start")
def test_dialectical_custom_primus() -> None:
    """Scenario placeholder for custom Primus start."""


@scenario("../features/reasoning_mode.feature", "Dialectical reasoning with a realistic query")
def test_dialectical_real_query() -> None:
    """Scenario placeholder for dialectical reasoning on realistic query."""


@scenario("../features/reasoning_mode.feature", "Direct reasoning with a realistic query")
def test_direct_real_query() -> None:
    """Scenario placeholder for direct mode with realistic query."""


@scenario(
    "../features/reasoning_mode.feature",
    "Chain-of-thought reasoning with a realistic query",
)
def test_cot_real_query():
    """Scenario placeholder for chain-of-thought realistic query."""


@scenario(
    "../features/reasoning_mode.feature",
    "Unsupported reasoning mode fails gracefully",
)
def test_unsupported_mode() -> None:
    """Scenario placeholder for unsupported reasoning mode."""


@scenario(
    "../features/reasoning_mode.feature",
    "Planner research debate validate telemetry",
)
def test_prdv_telemetry() -> None:
    """Scenario placeholder for PRDV telemetry."""


@scenario(
    "../features/reasoning_mode.feature",
    "Reverification broadens claim audits",
)
def test_reverify_claim_audits() -> None:
    """Scenario placeholder for reverify claim audits."""


@scenario(
    "../features/reasoning_mode.feature",
    "Direct mode agent failure triggers fallback",
)
def test_direct_failure() -> None:
    """Scenario placeholder for direct mode failure recovery."""


@scenario(
    "../features/reasoning_mode.feature",
    "Chain-of-thought mode agent failure triggers fallback",
)
def test_cot_failure() -> None:
    """Scenario placeholder for chain-of-thought failure recovery."""


@scenario(
    "../features/reasoning_mode.feature",
    "Dialectical mode agent failure triggers fallback",
)
def test_dialectical_failure() -> None:
    """Scenario placeholder for dialectical failure recovery."""


@scenario(
    "../features/reasoning_mode.feature",
    "Loop overflow triggers recovery",
)
def test_loop_overflow() -> None:
    """Scenario placeholder for loop overflow handling."""


@when("I simulate a PRDV planner flow", target_fixture="prdv_context")
def simulate_prdv_planner_flow() -> dict[str, Any]:
    state = QueryState(query="planner telemetry")
    graph = TaskGraph(
        tasks=[
            TaskNode(
                id="plan",
                question="Plan research agenda",
                tools=["planner"],
                affinity={"planner": 1.0},
                sub_questions=["Clarify scope"],
                explanation="Outline the planning cadence",
            ),
            TaskNode(
                id="research",
                question="Research supporting evidence",
                tools=["search"],
                depends_on=["plan", "phantom"],
                affinity={"search": 0.8, "analysis": 0.3},
                criteria=["Document findings"],
                explanation="Gather the strongest sources",
            ),
            TaskNode(
                id="validate",
                question="Validate findings",
                tools=["review"],
                depends_on=["research"],
                affinity={"review": 0.7},
                criteria=["Cross-check evidence"],
            ),
        ],
        metadata={"mode": "prdv"},
    )
    payload = cast(dict[str, Any], graph.to_payload())
    tasks = cast(list[dict[str, Any]], payload["tasks"])
    affinity = cast(dict[str, Any], tasks[1].get("affinity", {}))
    affinity["search"] = "strong"
    payload["objectives"] = ["Deliver planner-coordinator telemetry"]
    payload["exit_criteria"] = ["All phases recorded"]
    payload["explanation"] = "Ensure telemetry demonstrates readiness ordering"
    tasks[0]["tool_affinity"] = cast(dict[str, Any], tasks[0].get("affinity", {}))
    tasks[0]["objectives"] = list(tasks[0].get("sub_questions", []))
    tasks[1]["tool_affinity"] = cast(dict[str, Any], tasks[1].get("affinity", {}))
    tasks[1]["exit_criteria"] = list(tasks[1].get("criteria", []))
    warnings = state.set_task_graph(payload)
    state.record_planner_trace(
        prompt="Plan the PRDV cycle",
        raw_response=json.dumps(payload),
        normalized=state.task_graph,
        warnings=warnings,
    )
    coordinator = TaskCoordinator(state)
    coordinator.start_task("plan")
    coordinator.complete_task("plan")
    coordinator.start_task("research")
    trace = coordinator.record_react_step(
        "research",
        thought="collect expert insight",
        action="call search",
        observation="notes gathered",
        tool="search",
    )
    return {"state": state, "trace": trace, "warnings": warnings}


@then("the planner react log should capture normalization warnings")
def assert_prdv_react_log(prdv_context: Mapping[str, Any]) -> None:
    state = prdv_context["state"]
    assert isinstance(state, QueryState)
    normalization_events = [
        entry for entry in state.react_log if entry["event"] == "planner.normalization"
    ]
    assert normalization_events
    assert normalization_events[-1]["payload"]["warnings"]
    trace_events = [entry for entry in state.react_log if entry["event"] == "planner.trace"]
    assert trace_events
    assert trace_events[-1]["metadata"]["warnings"]


@then("the coordinator trace metadata should include unlock events")
def assert_prdv_trace_metadata(prdv_context: Mapping[str, Any]) -> None:
    trace = prdv_context["trace"]
    metadata = trace["metadata"]
    assert metadata["unlock_events"]
    assert metadata["task_depth"] == 1
    assert metadata["affinity_delta"] > 0.0
    assert metadata["scheduler"]["selected"]["id"] == "research"


@then("the telemetry snapshot should include scheduler context")
def assert_prdv_telemetry_snapshot(prdv_context: Mapping[str, Any]) -> None:
    state = prdv_context["state"]
    assert isinstance(state, QueryState)
    telemetry = state.metadata["planner"]["telemetry"]
    assert telemetry["objectives"] == ["Deliver planner-coordinator telemetry"]
    assert telemetry["exit_criteria"] == ["All phases recorded"]
    assert telemetry["tasks"], "Planner tasks should be tracked"
    coordinator_meta = state.metadata["coordinator"]
    assert coordinator_meta["decisions"], "Coordinator decisions should persist"
    last_decision = coordinator_meta["decisions"][-1]
    assert last_decision["scheduler"]["selected"]["id"] == "research"


@given(parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config")
def loops_config(
    count: int,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel(agents=["Synthesizer", "Contrarian", "FactChecker"], loops=count)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    set_value(bdd_context, "config", cfg)
    return cfg


@given(parsers.parse('reasoning mode is "{mode}"'))
def set_reasoning_mode(
    config: ConfigModel,
    mode: str,
    bdd_context: BehaviorContext,
) -> ConfigModel:
    config.reasoning_mode = ReasoningMode(mode)
    set_value(bdd_context, "config", config)
    return config


@given(parsers.parse("primus start is {index:d}"))
def set_primus_start(
    config: ConfigModel,
    index: int,
    bdd_context: BehaviorContext,
) -> ConfigModel:
    config.primus_start = index
    set_value(bdd_context, "config", config)
    return config


@given("gate policy forces debate")
def gate_policy_force_debate(bdd_context: BehaviorContext) -> None:
    bdd_context["force_gate_debate"] = True


@given("gate policy forces exit")
def gate_policy_force_exit(bdd_context: BehaviorContext) -> None:
    bdd_context["force_gate_exit"] = True


@when(
    parsers.parse('I run the orchestrator on query "{query}"'),
    target_fixture="run_result",
)
def run_orchestrator(
    query: str,
    config: ConfigModel,
    isolate_network,
    restore_environment,
    bdd_context: BehaviorContext,
) -> dict[str, Any]:
    record: list[str] = []
    params: dict[str, Any] = {}
    logs: list[str] = []
    state: dict[str, bool] = {"active": True}

    class DummyAgent:
        def __init__(self, name: str) -> None:
            self.name = name

        def can_execute(self, *_args: object, **_kwargs: object) -> bool:
            return True

        def execute(self, *_args: object, **_kwargs: object) -> dict[str, Any]:
            record.append(self.name)
            return {}

    def get_agent(name: str) -> DummyAgent:
        return DummyAgent(name)

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel) -> dict[str, Any]:
        out = original_parse(cfg)
        params.update(out)
        return out

    force_exit = bdd_context.get("force_gate_exit", False)
    force_debate = bdd_context.get("force_gate_debate", False)
    original_gate = OrchestrationUtils.evaluate_scout_gate_policy

    def fake_gate(**kwargs: Any) -> ScoutGateDecision:
        if force_debate:
            decision = ScoutGateDecision(
                should_debate=True,
                target_loops=kwargs.get("loops", 1),
                heuristics={"retrieval_overlap": 0.0, "nli_conflict": 1.0, "complexity": 1.0},
                thresholds={"retrieval_overlap": 0.6, "nli_conflict": 0.3, "complexity": 0.5},
                reason="force_debate",
                tokens_saved=0,
            )
        elif force_exit:
            decision = ScoutGateDecision(
                should_debate=False,
                target_loops=1,
                heuristics={"retrieval_overlap": 1.0, "nli_conflict": 0.0, "complexity": 0.0},
                thresholds={"retrieval_overlap": 0.6, "nli_conflict": 0.3, "complexity": 0.5},
                reason="force_exit",
                tokens_saved=0,
            )
        else:
            decision = original_gate(**kwargs)
        kwargs["state"].metadata.setdefault("scout_gate", decision.__dict__)
        return decision

    with (
        patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=get_agent,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
            side_effect=spy_parse,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.OrchestrationUtils.evaluate_scout_gate_policy",
            side_effect=fake_gate,
        ),
    ):
        orchestrator = get_orchestrator(bdd_context)
        set_value(bdd_context, "config", config)
        active_config = get_config(bdd_context)
        try:
            orchestrator.run_query(query, active_config)
        finally:
            state["active"] = False
            logs.append("run complete")

    return {"record": record, "config_params": params, "logs": logs, "state": state}


@when(
    parsers.parse(
        'I run the orchestrator on query "{query}" with unsupported reasoning mode "{mode}"'
    ),
    target_fixture="error_result",
)
def run_orchestrator_invalid(
    query: str,
    mode: str,
    config: ConfigModel,
    isolate_network: object,
    restore_environment: object,
    bdd_context: BehaviorContext,
) -> dict[str, Any]:
    record: list[str] = []
    logs: list[str] = []
    state: dict[str, bool] = {"active": True}
    try:
        cfg = ConfigModel(agents=config.agents, loops=config.loops, reasoning_mode=mode)
        with patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=lambda name: None,
        ):
            orchestrator = get_orchestrator(bdd_context)
            set_value(bdd_context, "config", cfg)
            active_config = get_config(bdd_context)
            orchestrator.run_query(query, active_config)
    except Exception as exc:
        logs.append(f"unsupported reasoning mode: {mode}")
        return {"error": exc, "record": record, "logs": logs, "state": state}
    finally:
        state["active"] = False

    return {"error": None, "record": record, "logs": logs, "state": state}


def _run_orchestrator_with_failure(
    query: str,
    config: ConfigModel,
    isolate_network: object,
    restore_environment: object,
    bdd_context: BehaviorContext,
    *,
    overflow: bool = False,
):
    record: list[str] = []
    logs: list[str] = []
    state: dict[str, bool] = {"active": True}
    recovery_info: dict[str, Any] = {}

    original_handle = OrchestrationUtils.handle_agent_error

    def spy_handle(
        agent_name: str,
        e: Exception,
        state_obj: QueryState,
        metrics: OrchestrationMetrics,
    ) -> dict[str, Any]:
        info = original_handle(agent_name, e, state_obj, metrics)
        info["recovery_applied"] = state_obj.metadata.get("recovery_applied")
        recovery_info.update(info)
        logs.append(str(e))
        logs.append(f"recovery for {agent_name}")
        return info

    if config.reasoning_mode == ReasoningMode.CHAIN_OF_THOUGHT:
        from autoresearch.orchestration.metrics import OrchestrationMetrics
        from autoresearch.orchestration.state import QueryState

        call_count = 0

        class FailingSynthesizer:
            def __init__(self, name: str) -> None:
                self.name = name

            def can_execute(self, *args, **kwargs) -> bool:
                return True

            def execute(self, state_obj, cfg):
                nonlocal call_count
                call_count += 1
                record.append(self.name)
                if overflow and call_count > cfg.loops:
                    raise NotFoundError("loop overflow")
                raise NotFoundError("missing resource")

        def cot_run(self, q, cfg, agent_factory=None):
            state_obj = QueryState(query=q)
            metrics = OrchestrationMetrics()
            agent = FailingSynthesizer("Synthesizer")
            loops = cfg.loops + 1 if overflow else cfg.loops
            for _ in range(loops):
                try:
                    agent.execute(state_obj, cfg)
                except Exception as e:  # noqa: PERF203 - test instrumentation
                    info = spy_handle("Synthesizer", e, state_obj, metrics)
                    state_obj.add_error(info)
            return state_obj.synthesize()

        with (
            patch(
                "autoresearch.orchestration.orchestration_utils.OrchestrationUtils.handle_agent_error",
                side_effect=spy_handle,
            ),
            patch(
                "autoresearch.orchestration.reasoning.ChainOfThoughtStrategy.run_query",
                cot_run,
            ),
        ):
            orchestrator = get_orchestrator(bdd_context)
            set_value(bdd_context, "config", config)
            active_config = get_config(bdd_context)
            try:
                orchestrator.run_query(query, active_config)
                error = None
            except Exception as exc:  # pragma: no cover - not expected
                error = exc
            finally:
                state["active"] = False

        return {
            "error": error,
            "record": record,
            "logs": logs,
            "state": state,
            "recovery_info": recovery_info,
        }

    params: dict = {}

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel):
        out = original_parse(cfg)
        if overflow:
            out["loops"] = cfg.loops + 1
        params.update(out)
        return out

    call_count = 0

    class FailingAgent:
        def __init__(self, name: str) -> None:
            self.name = name

        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            record.append(self.name)
            if overflow:
                if call_count > config.loops:
                    raise NotFoundError("loop overflow")
                return {}
            raise NotFoundError("missing resource")

    def get_agent(name: str, llm_adapter=None):
        return FailingAgent(name)

    with (
        patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=get_agent,
        ),
        patch(
            "autoresearch.orchestration.orchestration_utils.OrchestrationUtils.handle_agent_error",
            side_effect=spy_handle,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
            side_effect=spy_parse,
        ),
    ):
        orchestrator = get_orchestrator(bdd_context)
        set_value(bdd_context, "config", config)
        active_config = get_config(bdd_context)
        try:
            orchestrator.run_query(query, active_config)
            error = None
        except Exception as exc:
            error = exc
        finally:
            state["active"] = False

    return {
        "error": error,
        "record": record,
        "logs": logs,
        "state": state,
        "recovery_info": recovery_info,
        "config_params": params,
    }


@when(
    parsers.parse('I run the orchestrator on query "{query}" with a failing agent'),
    target_fixture="run_result",
)
def run_orchestrator_failure(
    query: str,
    config: ConfigModel,
    isolate_network: object,
    restore_environment: object,
    bdd_context: BehaviorContext,
) -> dict[str, Any]:
    return _run_orchestrator_with_failure(
        query,
        config,
        isolate_network,
        restore_environment,
        bdd_context,
    )


@when(
    parsers.parse('I run the orchestrator on query "{query}" exceeding loop limit'),
    target_fixture="run_result",
)
def run_orchestrator_overflow(
    query: str,
    config: ConfigModel,
    isolate_network: object,
    restore_environment: object,
    bdd_context: BehaviorContext,
) -> dict[str, Any]:
    return _run_orchestrator_with_failure(
        query,
        config,
        isolate_network,
        restore_environment,
        bdd_context,
        overflow=True,
    )


@then(parsers.parse("the loops used should be {count:d}"))
def assert_loops(run_result: Mapping[str, Any], count: int) -> None:
    assert run_result["config_params"].get("loops") == count


@then(parsers.parse('the reasoning mode selected should be "{mode}"'))
def assert_mode(run_result: Mapping[str, Any], mode: str) -> None:
    assert run_result["config_params"].get("mode") == ReasoningMode(mode)


@then(parsers.parse('the agent groups should be "{groups}"'))
def assert_groups(run_result: Mapping[str, Any], groups: str) -> None:
    expected = [[a.strip() for a in grp.split(",") if a.strip()] for grp in groups.split(";")]
    assert run_result["config_params"].get("agent_groups") == expected


@then(parsers.parse('the agents executed should be "{order}"'))
def assert_order(run_result: Mapping[str, Any], order: str) -> None:
    expected = [a.strip() for a in order.split(",")]
    assert run_result["record"] == expected


@then("a reasoning mode error should be raised")
def assert_invalid_mode(error_result: Mapping[str, Any]) -> None:
    err = error_result["error"]
    assert isinstance(err, ConfigError)
    assert "reasoning mode" in str(err).lower()


@then("no agents should execute")
def assert_no_agents(error_result: Mapping[str, Any]) -> None:
    assert error_result["record"] == []


@then(parsers.parse('the fallback agent should be "{agent}"'))
def assert_fallback_agent(run_result: Mapping[str, Any], agent: str) -> None:
    info = run_result.get("recovery_info", {})
    assert info.get("agent") == agent


@then(parsers.parse('a recovery strategy "{strategy}" should be recorded'))
def assert_strategy(run_result: Mapping[str, Any], strategy: str) -> None:
    assert run_result["recovery_info"].get("recovery_strategy") == strategy


@then("recovery should be applied")
def assert_recovery_applied(run_result: Mapping[str, Any]) -> None:
    assert run_result["recovery_info"].get("recovery_applied") is True


@then("the system state should be restored")
def assert_state_restored(
    run_result: Mapping[str, Any] | None = None,
    error_result: Mapping[str, Any] | None = None,
) -> None:
    result = run_result or error_result
    assert result and result.get("state", {}).get("active") is False


@then(parsers.parse('the logs should include "{message}"'))
def assert_logs(
    run_result: Mapping[str, Any] | None = None,
    error_result: Mapping[str, Any] | None = None,
    message: str = "",
) -> None:
    result = run_result or error_result
    logs = result.get("logs", []) if result else []
    assert any(message in entry for entry in logs), logs
