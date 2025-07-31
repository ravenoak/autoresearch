from __future__ import annotations

from unittest.mock import patch

from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.main import app as cli_app


@scenario("../features/reasoning_mode_cli.feature", "Direct mode via CLI")
def test_direct_mode_cli():
    pass


@given(parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config")
def loops_config(count: int, monkeypatch):
    cfg = ConfigModel.model_construct(agents=["Synthesizer"], loops=count)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


@when(
    parsers.parse('I run `autoresearch search "{query}" --mode {mode}`'),
    target_fixture="run_result",
)
def run_search(query: str, mode: str, config: ConfigModel, cli_runner):
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
        result = cli_runner.invoke(cli_app, ["search", query, "--mode", mode])

    return {"record": record, "config_params": params, "exit_code": result.exit_code}


@then("the CLI should exit successfully")
def cli_success(run_result):
    assert run_result["exit_code"] == 0


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
