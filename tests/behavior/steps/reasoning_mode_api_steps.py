from __future__ import annotations

from unittest.mock import patch

from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator


@scenario("../features/reasoning_mode_api.feature", "Direct mode via API")
def test_direct_mode_api():
    pass


@scenario("../features/reasoning_mode_api.feature", "Chain-of-thought mode via API")
def test_chain_of_thought_mode_api():
    pass


@scenario("../features/reasoning_mode_api.feature", "Dialectical mode via API")
def test_dialectical_mode_api():
    pass


@given("the API server is running", target_fixture="test_context")
def api_server_running(api_client):
    return {"client": api_client}


@given(parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config")
def loops_config(count: int, monkeypatch):
    cfg = ConfigModel(agents=["Synthesizer", "Contrarian", "FactChecker"], loops=count)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


@when(
    parsers.parse('I send a query "{query}" with reasoning mode "{mode}" to the API'),
    target_fixture="run_result",
)
def send_query(test_context: dict, query: str, mode: str, config: ConfigModel):
    record: list[str] = []
    params: dict = {}

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

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ), patch(
        "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
        side_effect=spy_parse,
    ):
        response = test_context["client"].post(
            "/query", json={"query": query, "reasoning_mode": mode}
        )

    test_context["response"] = response
    return {"record": record, "config_params": params}


@then("the response status should be 200")
def assert_status(test_context: dict) -> None:
    assert test_context["response"].status_code == 200


@then(parsers.parse("the loops used should be {count:d}"))
def assert_loops(run_result: dict, count: int) -> None:
    assert run_result["config_params"].get("loops") == count


@then(parsers.parse('the agent groups should be "{groups}"'))
def assert_groups(run_result: dict, groups: str) -> None:
    expected = [[a.strip() for a in grp.split(",") if a.strip()] for grp in groups.split(";")]
    assert run_result["config_params"].get("agent_groups") == expected


@then(parsers.parse('the agents executed should be "{order}"'))
def assert_order(run_result: dict, order: str) -> None:
    expected = [a.strip() for a in order.split(",")]
    assert run_result["record"] == expected
