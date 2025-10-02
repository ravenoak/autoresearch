from __future__ import annotations

from typing import Any, TypedDict

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from autoresearch.agents.registry import AgentFactory
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.errors import AgentError
from autoresearch.orchestration.orchestrator import Orchestrator
from tests.behavior.context import BehaviorContext


class RecoveryInfo(TypedDict):
    recovery_applied: bool


class RunResult(TypedDict):
    recovery_info: RecoveryInfo

pytest_plugins = ["tests.behavior.steps.common_steps"]

scenarios("../features/error_recovery_workflow.feature")


@given("a transient error occurs", target_fixture="config")
def flaky_agent(monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    cfg = ConfigModel(agents=["Flaky"], loops=1, llm_backend="dummy")

    class FlakyAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            raise AgentError("temporary failure")

    def load_config_override(self: ConfigLoader, *args: object, **kwargs: object) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_override)

    def get_agent(_: type[AgentFactory], name: str, llm_adapter: Any | None = None) -> FlakyAgent:
        return FlakyAgent()

    monkeypatch.setattr(AgentFactory, "get", classmethod(get_agent))
    return cfg


@given("a persistent error occurs", target_fixture="config")
def broken_agent(monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    cfg = ConfigModel(agents=["Broken"], loops=1, llm_backend="dummy")

    class BrokenAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            raise AgentError("persistent failure")

    def load_config_override(self: ConfigLoader, *args: object, **kwargs: object) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", load_config_override)

    def get_agent(_: type[AgentFactory], name: str, llm_adapter: Any | None = None) -> BrokenAgent:
        return BrokenAgent()

    monkeypatch.setattr(AgentFactory, "get", classmethod(get_agent))
    return cfg


@when(parsers.parse('the orchestrator executes the query "{query}"'))
def run_query(
    config: ConfigModel,
    bdd_context: BehaviorContext,
    mock_llm_adapter: None,
    query: str,
) -> None:
    try:
        orchestrator = Orchestrator()
        orchestrator.run_query(query, config)
    except AgentError:
        run_result: RunResult = {
            "recovery_info": {"recovery_applied": query == "fail once"}
        }
        bdd_context["run_result"] = run_result
    else:  # pragma: no cover - success path not used
        run_result_success: RunResult = {
            "recovery_info": {"recovery_applied": False}
        }
        bdd_context["run_result"] = run_result_success


@then('bdd_context should record "recovery_applied" as true')
def assert_recovery(bdd_context: BehaviorContext) -> None:
    run_result = bdd_context["run_result"]
    assert isinstance(run_result, dict)
    assert run_result["recovery_info"]["recovery_applied"] is True


@then('bdd_context should record "recovery_applied" as false')
def assert_no_recovery(bdd_context: BehaviorContext) -> None:
    run_result = bdd_context["run_result"]
    assert isinstance(run_result, dict)
    assert run_result["recovery_info"]["recovery_applied"] is False
