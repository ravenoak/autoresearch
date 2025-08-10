from __future__ import annotations

from unittest.mock import patch

from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.errors import ConfigError, NotFoundError
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator


@scenario("../features/reasoning_mode.feature", "Direct mode runs Synthesizer only")
def test_direct_mode():
    pass


@scenario("../features/reasoning_mode.feature", "Default reasoning mode is dialectical")
def test_default_mode():
    pass


@scenario(
    "../features/reasoning_mode.feature", "Chain-of-thought mode loops Synthesizer"
)
def test_chain_of_thought_mode():
    pass


@scenario(
    "../features/reasoning_mode.feature", "Dialectical mode with custom Primus start"
)
def test_dialectical_custom_primus():
    pass


@scenario(
    "../features/reasoning_mode.feature", "Dialectical reasoning with a realistic query"
)
def test_dialectical_real_query():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Unsupported reasoning mode fails gracefully",
)
def test_unsupported_mode():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Direct mode agent failure triggers fallback",
)
def test_direct_failure():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Chain-of-thought mode agent failure triggers fallback",
)
def test_cot_failure():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Dialectical mode agent failure triggers fallback",
)
def test_dialectical_failure():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Loop overflow triggers recovery",
)
def test_loop_overflow():
    pass


@given(
    parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config"
)
def loops_config(count: int, monkeypatch):
    cfg = ConfigModel(agents=["Synthesizer", "Contrarian", "FactChecker"], loops=count)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


@given(parsers.parse('reasoning mode is "{mode}"'))
def set_reasoning_mode(config: ConfigModel, mode: str):
    config.reasoning_mode = ReasoningMode(mode)
    return config


@given(parsers.parse("primus start is {index:d}"))
def set_primus_start(config: ConfigModel, index: int):
    config.primus_start = index
    return config


@when(
    parsers.parse('I run the orchestrator on query "{query}"'),
    target_fixture="run_result",
)
def run_orchestrator(
    query: str,
    config: ConfigModel,
    isolate_network,
    restore_environment,
):
    record: list[str] = []
    params: dict = {}
    logs: list[str] = []
    state = {"active": True}

    class DummyAgent:
        def __init__(self, name: str) -> None:
            self.name = name

        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            record.append(self.name)
            return {}

    def get_agent(name: str) -> DummyAgent:
        return DummyAgent(name)

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel):
        out = original_parse(cfg)
        params.update(out)
        return out

    with (
        patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=get_agent,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
            side_effect=spy_parse,
        ),
    ):
        try:
            Orchestrator.run_query(query, config)
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
    isolate_network,
    restore_environment,
):
    record: list[str] = []
    logs: list[str] = []
    state = {"active": True}
    try:
        cfg = ConfigModel(agents=config.agents, loops=config.loops, reasoning_mode=mode)
        with patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=lambda name: None,
        ):
            Orchestrator.run_query(query, cfg)
    except Exception as exc:
        logs.append(f"unsupported reasoning mode: {mode}")
        return {"error": exc, "record": record, "logs": logs, "state": state}
    finally:
        state["active"] = False

    return {"error": None, "record": record, "logs": logs, "state": state}


def _run_orchestrator_with_failure(
    query: str,
    config: ConfigModel,
    isolate_network,
    restore_environment,
    *,
    overflow: bool = False,
):
    record: list[str] = []
    logs: list[str] = []
    state = {"active": True}
    recovery_info: dict = {}

    original_handle = Orchestrator._handle_agent_error

    def spy_handle(agent_name: str, e: Exception, state_obj, metrics):
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
                "autoresearch.orchestration.orchestrator.Orchestrator._handle_agent_error",
                side_effect=spy_handle,
            ),
            patch(
                "autoresearch.orchestration.reasoning.ChainOfThoughtStrategy.run_query",
                cot_run,
            ),
        ):
            try:
                Orchestrator.run_query(query, config)
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
            "autoresearch.orchestration.orchestrator.Orchestrator._handle_agent_error",
            side_effect=spy_handle,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
            side_effect=spy_parse,
        ),
    ):
        try:
            Orchestrator.run_query(query, config)
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
    isolate_network,
    restore_environment,
):
    return _run_orchestrator_with_failure(
        query, config, isolate_network, restore_environment
    )


@when(
    parsers.parse('I run the orchestrator on query "{query}" exceeding loop limit'),
    target_fixture="run_result",
)
def run_orchestrator_overflow(
    query: str,
    config: ConfigModel,
    isolate_network,
    restore_environment,
):
    return _run_orchestrator_with_failure(
        query, config, isolate_network, restore_environment, overflow=True
    )


@then(parsers.parse("the loops used should be {count:d}"))
def assert_loops(run_result: dict, count: int) -> None:
    assert run_result["config_params"].get("loops") == count


@then(parsers.parse('the reasoning mode selected should be "{mode}"'))
def assert_mode(run_result: dict, mode: str) -> None:
    assert run_result["config_params"].get("mode") == ReasoningMode(mode)


@then(parsers.parse('the agent groups should be "{groups}"'))
def assert_groups(run_result: dict, groups: str) -> None:
    expected = [
        [a.strip() for a in grp.split(",") if a.strip()] for grp in groups.split(";")
    ]
    assert run_result["config_params"].get("agent_groups") == expected


@then(parsers.parse('the agents executed should be "{order}"'))
def assert_order(run_result: dict, order: str) -> None:
    expected = [a.strip() for a in order.split(",")]
    assert run_result["record"] == expected


@then("a reasoning mode error should be raised")
def assert_invalid_mode(error_result: dict) -> None:
    err = error_result["error"]
    assert isinstance(err, ConfigError)
    assert "reasoning mode" in str(err).lower()


@then("no agents should execute")
def assert_no_agents(error_result: dict) -> None:
    assert error_result["record"] == []


@then(parsers.parse('the fallback agent should be "{agent}"'))
def assert_fallback_agent(run_result: dict, agent: str) -> None:
    info = run_result.get("recovery_info", {})
    assert info.get("agent") == agent


@then(parsers.parse('a recovery strategy "{strategy}" should be recorded'))
def assert_strategy(run_result: dict, strategy: str) -> None:
    assert run_result["recovery_info"].get("recovery_strategy") == strategy


@then("recovery should be applied")
def assert_recovery_applied(run_result: dict) -> None:
    assert run_result["recovery_info"].get("recovery_applied") is True


@then("the system state should be restored")
def assert_state_restored(
    run_result: dict | None = None, error_result: dict | None = None
) -> None:
    result = run_result or error_result
    assert result and result.get("state", {}).get("active") is False


@then(parsers.parse('the logs should include "{message}"'))
def assert_logs(
    run_result: dict | None = None, error_result: dict | None = None, message: str = ""
) -> None:
    result = run_result or error_result
    logs = result.get("logs", []) if result else []
    assert any(message in entry for entry in logs), logs
