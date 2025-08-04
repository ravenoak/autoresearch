from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import AgentError, TimeoutError
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory


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
    "../features/error_recovery_extended.feature",
    "Recovery after agent timeout",
)
def test_error_recovery_timeout():
    pass


@scenario(
    "../features/error_recovery_extended.feature",
    "Recovery after agent failure",
)
def test_error_recovery_agent_failure():
    pass


@given("an agent that raises a transient error", target_fixture="config")
def flaky_agent(monkeypatch):
    cfg = ConfigModel.model_construct(agents=["Flaky"], loops=1)

    class FlakyAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise RuntimeError("temporary network issue")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(AgentFactory, "get", lambda self, name: FlakyAgent())
    return cfg


@given("an agent that times out during execution", target_fixture="config")
def timeout_agent(monkeypatch):
    cfg = ConfigModel.model_construct(agents=["Slowpoke"], loops=1)

    class TimeoutAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise TimeoutError("simulated timeout")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(AgentFactory, "get", lambda self, name: TimeoutAgent())
    return cfg


@given("an agent that fails during execution", target_fixture="config")
def failing_agent(monkeypatch):
    cfg = ConfigModel.model_construct(agents=["Faulty"], loops=1)

    class FailingAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise AgentError("agent execution failed")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(AgentFactory, "get", lambda self, name: FailingAgent())
    return cfg


@given(parsers.parse('reasoning mode is "{mode}"'))
def set_reasoning_mode(config: ConfigModel, mode: str):
    config.reasoning_mode = ReasoningMode(mode)
    return config


@pytest.fixture
def recovery_context():
    info: dict = {}
    yield info
    info.clear()


@when(parsers.parse('I run the orchestrator on query "{query}"'), target_fixture="run_result")
def run_orchestrator(query: str, config: ConfigModel, recovery_context: dict):
    original_apply = Orchestrator._apply_recovery_strategy

    def spy_apply(agent_name: str, error_category: str, e: Exception, state):
        info = original_apply(agent_name, error_category, e, state)
        recovery_context.update(info)
        return info

    with patch(
        "autoresearch.orchestration.orchestrator.Orchestrator._apply_recovery_strategy",
        side_effect=spy_apply,
    ):
        response = Orchestrator.run_query(query, config)

    # Expose metrics as metadata for test assertions
    response.metadata = response.metrics
    return {"recovery_info": dict(recovery_context), "response": response}


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
    assert any(e.get("error_type") == "TimeoutError" for e in errors), errors


@then("the response should list an agent execution error")
def assert_agent_error(run_result: dict) -> None:
    errors = run_result["response"].metadata.get("errors", [])
    assert any(e.get("error_type") == "AgentError" for e in errors), errors
