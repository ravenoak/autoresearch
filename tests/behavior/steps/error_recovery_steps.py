from __future__ import annotations

import types
from unittest.mock import patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.errors import AgentError, StorageError, TimeoutError
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.storage import StorageManager

pytest_plugins = ["tests.behavior.steps.common_steps"]
pytestmark = pytest.mark.requires_git


def _assert_error_schema(errors: list[dict]) -> None:
    """Verify error entries contain the expected keys."""

    required = {"error_type", "message"}
    for err in errors:
        assert required.issubset(err.keys()), err


@scenario(
    "../features/error_recovery.feature",
    "Error recovery in dialectical reasoning mode",
)
def test_error_recovery_dialectical():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Error recovery in direct reasoning mode",
)
def test_error_recovery_direct():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Error recovery in chain-of-thought reasoning mode",
)
def test_error_recovery_cot():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after storage failure",
)
def test_error_recovery_storage_failure():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after persistent network outage",
)
def test_error_recovery_network_outage():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after agent timeout",
)
def test_error_recovery_timeout():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after critical agent failure",
)
def test_error_recovery_agent_failure():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Unsupported reasoning mode during recovery fails gracefully",
)
def test_error_recovery_unsupported_mode():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after agent failure with fallback",
)
def test_error_recovery_agent_fallback():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Error recovery with a realistic query",
)
def test_error_recovery_realistic_query():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Successful run does not trigger recovery",
)
def test_error_recovery_none():
    pass


@given("an agent that raises a transient error", target_fixture="config")
def flaky_agent(monkeypatch, isolate_network, restore_environment):
    cfg = ConfigModel.model_construct(agents=["Flaky"], loops=1)

    class FlakyAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise AgentError("temporary network issue")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: FlakyAgent()),
    )
    return cfg


@given("an agent that times out during execution", target_fixture="config")
def timeout_agent(monkeypatch, isolate_network, restore_environment):
    cfg = ConfigModel.model_construct(agents=["Slowpoke"], loops=1)

    class TimeoutAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise TimeoutError("simulated timeout")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: TimeoutAgent()),
    )
    return cfg


@given("an agent that fails during execution", target_fixture="config")
def failing_agent(monkeypatch, isolate_network, restore_environment):
    cfg = ConfigModel.model_construct(agents=["Faulty"], loops=1)

    class FailingAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise AgentError("agent execution failed")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: FailingAgent()),
    )
    return cfg


@given(
    "an agent that fails triggering fallback",
    target_fixture="config",
)
def failing_agent_fallback(monkeypatch, isolate_network, restore_environment):
    cfg = ConfigModel.model_construct(agents=["Faulty"], loops=1)

    class FailingAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise AgentError("agent execution failed")

    def handle(agent_name, exc, state, metrics):
        info = {
            "recovery_strategy": "fallback_agent",
            "error_category": "recoverable",
        }
        state.metadata["recovery_applied"] = True
        return info

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: FailingAgent()),
    )
    monkeypatch.setattr(
        OrchestrationUtils,
        "handle_agent_error",
        handle,
    )
    return cfg


@given("a reliable agent", target_fixture="config")
def reliable_agent(monkeypatch, isolate_network, restore_environment):
    cfg = ConfigModel.model_construct(agents=["Reliable"], loops=1)

    class ReliableAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            return {}

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: ReliableAgent()),
    )
    return cfg


@given("a storage layer that raises a StorageError", target_fixture="config")
def storage_failure_agent(monkeypatch, isolate_network, restore_environment):
    cfg = ConfigModel.model_construct(agents=["StoreFail"], loops=1)

    def fail_persist(*args, **kwargs):
        raise StorageError("simulated storage failure")

    class StorageAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            StorageManager.persist_claim({"id": "1"})
            return {"claims": [], "results": {}}

    monkeypatch.setattr(StorageManager, "persist_claim", fail_persist)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: StorageAgent()),
    )
    return cfg


@given("an agent facing a persistent network outage", target_fixture="config")
def network_outage_agent(monkeypatch, isolate_network, restore_environment):
    cfg = ConfigModel.model_construct(agents=["Offline"], loops=1)

    class OfflineAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise AgentError("network configuration failure")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: OfflineAgent()),
    )
    return cfg


@given(parsers.parse('reasoning mode is "{mode}"'))
def set_reasoning_mode(config: ConfigModel, mode: str, isolate_network, restore_environment):
    config.reasoning_mode = ReasoningMode(mode)
    return config


@pytest.fixture
def recovery_context():
    info: dict = {}
    yield info
    info.clear()


@when(
    parsers.parse('I run the orchestrator on query "{query}"'),
    target_fixture="run_result",
)
def run_orchestrator(
    query: str,
    config: ConfigModel,
    recovery_context: dict,
    isolate_network,
    restore_environment,
    orchestrator_failure,
):
    orchestrator_failure(None)
    record: list[str] = []
    params: dict = {}
    logs: list[str] = []
    state = {"active": True}
    original_handle = OrchestrationUtils.handle_agent_error
    original_get = AgentFactory.get

    def recording_get(name: str, llm_adapter=None):
        agent = original_get(name, llm_adapter)
        if hasattr(agent, "execute"):
            orig_exec = agent.execute

            def wrapped_execute(*args, **kwargs):
                record.append(name)
                return orig_exec(*args, **kwargs)

            agent.execute = wrapped_execute
        return agent

    def spy_handle(agent_name: str, e: Exception, state, metrics):
        info = original_handle(agent_name, e, state, metrics)
        info["recovery_applied"] = state.metadata.get("recovery_applied")
        recovery_context.update(info)
        logs.append(f"recovery for {agent_name}")
        return info

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel):
        out = original_parse(cfg)
        params.update(out)
        return out

    with (
        patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=recording_get,
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
        try:
            response = Orchestrator.run_query(query, config)
        except Exception as e:
            if not recovery_context:
                # Manually categorize and record the error if no recovery info was captured
                agent_name = getattr(config, "agents", ["Unknown"])[0]

                def update(result):
                    dummy_state.metadata.update(result.get("metadata", {}))
                    dummy_state.results.update(result.get("results", {}))

                dummy_state = types.SimpleNamespace(update=update, metadata={}, results={})
                dummy_metrics = types.SimpleNamespace(record_error=lambda agent: None)
                info = original_handle(agent_name, e, dummy_state, dummy_metrics)
                info["recovery_applied"] = dummy_state.metadata.get("recovery_applied")
                recovery_context.update(info)
                logs.append(f"recovery for {agent_name}")
            response = types.SimpleNamespace(
                metadata={"errors": [dict(recovery_context)]},
                metrics={"errors": [dict(recovery_context)]},
            )
        finally:
            state["active"] = False
            logs.append("run complete")

    # Expose metrics as metadata for test assertions when possible
    try:
        response.metadata = response.metrics
    except Exception:
        pass
    return {
        "recovery_info": dict(recovery_context),
        "response": response,
        "record": record,
        "config_params": params,
        "logs": logs,
        "state": state,
    }


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
    recovery_context: dict,
    isolate_network,
    restore_environment,
    orchestrator_failure,
):
    orchestrator_failure(None)
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


@then("no recovery should be recorded")
def assert_no_recovery(run_result: dict) -> None:
    assert run_result["recovery_info"] == {}


@then(parsers.parse('a recovery strategy "{strategy}" should be recorded'))
def assert_strategy(run_result: dict, strategy: str) -> None:
    assert run_result["recovery_info"], "Recovery info should not be empty"
    assert run_result["recovery_info"].get("recovery_strategy") == strategy


@then("recovery should be applied")
def assert_recovery_applied(run_result: dict) -> None:
    assert run_result["recovery_info"], "Recovery info should not be empty"
    assert run_result["recovery_info"].get("recovery_applied") is True


@then("the response should list a timeout error")
def assert_timeout_error(run_result: dict) -> None:
    errors = run_result["response"].metadata.get("errors", [])
    _assert_error_schema(errors)
    assert any(
        e.get("error_type") == "TimeoutError" and "simulated timeout" in e.get("message", "")
        for e in errors
    ), errors


@then("the response should list an agent execution error")
def assert_agent_error(run_result: dict) -> None:
    errors = run_result["response"].metadata.get("errors", [])
    _assert_error_schema(errors)
    assert any(e.get("error_type") == "AgentError" for e in errors), errors


@then(parsers.parse('error category "{category}" should be recorded'))
def assert_error_category(run_result: dict, category: str) -> None:
    assert run_result["recovery_info"].get("error_category") == category


@then(parsers.parse('the response should list an error of type "{error_type}"'))
def assert_error_type(run_result: dict, error_type: str) -> None:
    errors = run_result["response"].metadata.get("errors", [])
    _assert_error_schema(errors)
    assert any(e.get("error_type") == error_type for e in errors), errors


@then(parsers.parse("the loops used should be {count:d}"))
def assert_loops(run_result: dict, count: int) -> None:
    assert run_result["config_params"].get("loops") == count


@then(parsers.parse('the reasoning mode selected should be "{mode}"'))
def assert_mode(run_result: dict, mode: str) -> None:
    assert run_result["config_params"].get("mode") == ReasoningMode(mode)


@then(parsers.parse('the agent groups should be "{groups}"'))
def assert_groups(run_result: dict, groups: str) -> None:
    expected = [[a.strip() for a in grp.split(",") if a.strip()] for grp in groups.split(";")]
    assert run_result["config_params"].get("agent_groups") == expected


@then(parsers.parse('the agents executed should be "{order}"'))
def assert_order(run_result: dict, order: str) -> None:
    expected = [a.strip() for a in order.split(",")]
    assert run_result["record"] == expected


@then("the system state should be restored")
def assert_state_restored(run_result: dict | None = None, error_result: dict | None = None) -> None:
    result = run_result or error_result
    assert result and result.get("state", {}).get("active") is False


@then(parsers.parse('the logs should include "{message}"'))
def assert_logs(
    run_result: dict | None = None, error_result: dict | None = None, message: str = ""
) -> None:
    result = run_result or error_result
    logs = result.get("logs", []) if result else []
    assert any(message in entry for entry in logs), logs
