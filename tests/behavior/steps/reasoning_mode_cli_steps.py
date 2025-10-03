from __future__ import annotations
import json
from typing import cast
from unittest.mock import patch

import pytest
from click import Command
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.main import app as cli_app
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator
from tests.behavior.utils import PayloadDict, as_payload


@scenario("../features/reasoning_mode_cli.feature", "Direct mode via CLI")
def test_direct_mode_cli() -> None:
    pass


@scenario("../features/reasoning_mode_cli.feature", "Dialectical mode via CLI")
def test_dialectical_mode_cli() -> None:
    pass


@scenario("../features/reasoning_mode_cli.feature", "Chain-of-thought mode via CLI")
def test_chain_of_thought_mode_cli() -> None:
    pass


@scenario(
    "../features/reasoning_mode_cli.feature",
    "Mode switching within a session via CLI",
)
def test_mode_switch_cli() -> None:
    pass


@scenario(
    "../features/reasoning_mode_cli.feature",
    "Invalid reasoning mode via CLI",
)
def test_invalid_mode_cli() -> None:
    pass


@scenario(
    "../features/reasoning_mode_cli.feature",
    "Invalid reasoning mode via SPARQL CLI",
)
def test_invalid_mode_sparql_cli() -> None:
    pass


@given(
    parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config"
)
def loops_config(count: int, monkeypatch: pytest.MonkeyPatch) -> ConfigModel:
    cfg = ConfigModel(agents=["Synthesizer", "Contrarian", "FactChecker"], loops=count)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


@when(
    parsers.parse('I run `autoresearch search "{query}" --mode {mode}`'),
    target_fixture="run_result",
)
def run_search(
    query: str, mode: str, config: ConfigModel, cli_runner: CliRunner
) -> PayloadDict:
    record: list[str] = []
    params: PayloadDict = {}
    logs: list[str] = []
    state: dict[str, bool] = {"active": True}

    class DummyAgent:
        def __init__(self, name: str) -> None:
            self.name = name

        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> PayloadDict:
            step = len(record) + 1
            record.append(self.name)
            content = f"{self.name}-{step}"
            return as_payload({
                "claims": [
                    {
                        "id": str(step),
                        "type": "thought",
                        "content": content,
                    }
                ],
                "results": {"final_answer": content},
            })

    def get_agent(name: str) -> DummyAgent:
        return DummyAgent(name)

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel) -> PayloadDict:
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
        command = cast(Command, cli_app)
        result = cli_runner.invoke(
            command, ["search", query, "--mode", mode, "--output", "json"]
        )
        if result.exit_code != 0:
            logs.append("unsupported reasoning mode")
    state["active"] = False

    data: PayloadDict = {}
    try:
        data = as_payload(json.loads(result.stdout))
    except Exception:
        lines = result.stdout.splitlines()
        start_idx = None
        for idx, line in enumerate(lines):
            if '"answer"' in line:
                start_idx = idx - 1 if idx > 0 else idx
                break
        if start_idx is not None:
            try:
                data = as_payload(json.loads("\n".join(lines[start_idx:])))
            except Exception:
                data = {}
    return as_payload({
        "record": record,
        "config_params": params,
        "exit_code": result.exit_code,
        "data": data,
        "output": result.stdout,
        "stderr": result.stderr,
        "logs": logs,
        "state": state,
    })


@when(
    parsers.parse('I run `autoresearch sparql "{query}" --mode {mode}`'),
    target_fixture="run_result",
)
def run_sparql(
    query: str, mode: str, config: ConfigModel, cli_runner: CliRunner
) -> PayloadDict:
    record: list[str] = []
    params: PayloadDict = {}
    logs: list[str] = []
    state: dict[str, bool] = {"active": True}

    def get_agent(name: str) -> object:
        class DummyAgent:
            def __init__(self, n: str) -> None:
                self.name = n

            def can_execute(self, *args: object, **kwargs: object) -> bool:
                return True

            def execute(self, *args: object, **kwargs: object) -> PayloadDict:
                record.append(self.name)
                return as_payload({"claims": [], "results": {"final_answer": ""}})

        return DummyAgent(name)

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel) -> PayloadDict:
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
        command = cast(Command, cli_app)
        result = cli_runner.invoke(
            command, ["sparql", query, "--mode", mode, "--output", "json"]
        )
        if result.exit_code != 0:
            logs.append("unsupported reasoning mode")
    state["active"] = False
    data: PayloadDict = {}
    try:
        data = as_payload(json.loads(result.stdout))
    except Exception:
        pass
    return as_payload({
        "record": record,
        "config_params": params,
        "exit_code": result.exit_code,
        "data": data,
        "output": result.stdout,
        "stderr": result.stderr,
        "logs": logs,
        "state": state,
    })


@then("the CLI should exit successfully")
def cli_success(run_result: PayloadDict) -> None:
    assert run_result["exit_code"] == 0
    assert run_result.get("stderr", "") == ""


@then(parsers.parse("the loops used should be {count:d}"))
def assert_loops(run_result: PayloadDict, count: int) -> None:
    assert run_result["config_params"].get("loops") == count


@then(parsers.parse('the reasoning mode selected should be "{mode}"'))
def assert_mode(run_result: PayloadDict, mode: str) -> None:
    assert run_result["config_params"].get("mode") == ReasoningMode(mode)


@then(parsers.parse('the agent groups should be "{groups}"'))
def assert_groups(run_result: PayloadDict, groups: str) -> None:
    expected = [
        [a.strip() for a in grp.split(",") if a.strip()] for grp in groups.split(";")
    ]
    assert run_result["config_params"].get("agent_groups") == expected


@then(parsers.parse('the agents executed should be "{order}"'))
def assert_order(run_result: PayloadDict, order: str) -> None:
    expected = [a.strip() for a in order.split(",")]
    assert run_result["record"] == expected


@then(parsers.parse('the reasoning steps should be "{steps}"'))
def assert_reasoning(run_result: PayloadDict, steps: str) -> None:
    expected = [s.strip() for s in steps.split(";") if s.strip()]
    actual = [c.get("content") for c in run_result["data"].get("reasoning", [])]
    assert actual == expected


@then(parsers.parse("the metrics should record {count:d} cycles"))
def assert_metrics_cycles(run_result: PayloadDict, count: int) -> None:
    metrics = run_result["data"].get("metrics", {}).get("execution_metrics", {})
    assert metrics.get("cycles_completed") == count


@then(parsers.parse('the metrics should list agents "{agents}"'))
def assert_metrics_agents(run_result: PayloadDict, agents: str) -> None:
    expected = [a.strip() for a in agents.split(",") if a.strip()]
    metrics = run_result["data"].get("metrics", {}).get("execution_metrics", {})
    actual = list(metrics.get("agent_timings", {}).keys())
    assert actual == expected


@then("the CLI should exit with an error")
def cli_error(run_result: PayloadDict) -> None:
    assert run_result["exit_code"] != 0
    assert "mode" in run_result["output"].lower()
    assert run_result.get("stderr") not in (None, "")


@then("no agents should execute")
def assert_no_agents(run_result: PayloadDict) -> None:
    assert run_result["record"] == []
