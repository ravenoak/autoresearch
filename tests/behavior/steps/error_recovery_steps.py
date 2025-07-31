from __future__ import annotations

from unittest.mock import patch

from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory


@scenario("../features/error_recovery.feature", "Transient error triggers recovery")
def test_transient_error_recovery():
    pass


@given("an agent that raises a transient error", target_fixture="config")
def flaky_agent(monkeypatch):
    cfg = ConfigModel.model_construct(agents=["Flaky"], loops=1)

    class FlakyAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise RuntimeError("temporary network issue")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(AgentFactory, "get", lambda self, name: FlakyAgent())
    return cfg


@when(parsers.parse('I run the orchestrator on query "{query}"'), target_fixture="run_result")
def run_orchestrator(query: str, config: ConfigModel):
    recovery_info: dict = {}
    original_apply = Orchestrator._apply_recovery_strategy

    def spy_apply(agent_name: str, error_category: str, e: Exception, state):
        info = original_apply(agent_name, error_category, e, state)
        recovery_info.update(info)
        return info

    with patch(
        "autoresearch.orchestration.orchestrator.Orchestrator._apply_recovery_strategy",
        side_effect=spy_apply,
    ):
        Orchestrator.run_query(query, config)

    return {"recovery_info": recovery_info}


@then(parsers.parse('a recovery strategy "{strategy}" should be recorded'))
def assert_strategy(run_result: dict, strategy: str) -> None:
    assert run_result["recovery_info"].get("recovery_strategy") == strategy


@then("recovery should be applied")
def assert_recovery_applied(run_result: dict) -> None:
    assert run_result["recovery_info"].get("recovery_applied") is True
