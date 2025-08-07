from __future__ import annotations

from unittest.mock import patch
import json

from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.main import app as cli_app


@scenario("../features/reasoning_mode_cli.feature", "Direct mode via CLI")
def test_direct_mode_cli():
    pass


@scenario("../features/reasoning_mode_cli.feature", "Dialectical mode via CLI")
def test_dialectical_mode_cli():
    pass


@scenario("../features/reasoning_mode_cli.feature", "Chain-of-thought mode via CLI")
def test_chain_of_thought_mode_cli():
    pass


@scenario(
    "../features/reasoning_mode_cli.feature",
    "Mode switching within a session via CLI",
)
def test_mode_switch_cli():
    pass


@scenario(
    "../features/reasoning_mode_cli.feature",
    "Invalid reasoning mode via CLI",
)
def test_invalid_mode_cli():
    pass


@given(parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config")
def loops_config(count: int, monkeypatch):
    cfg = ConfigModel.model_construct(
        agents=["Synthesizer", "Contrarian", "FactChecker"],
        loops=count,
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


@when(
    parsers.parse('I run `autoresearch search "{query}" --mode {mode}`'),
    target_fixture="run_result",
)
def run_search(query: str, mode: str, config: ConfigModel, cli_runner):
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
            step = len(record) + 1
            record.append(self.name)
            content = f"{self.name}-{step}"
            return {
                "claims": [
                    {
                        "id": str(step),
                        "type": "thought",
                        "content": content,
                    }
                ],
                "results": {"final_answer": content},
            }

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
        result = cli_runner.invoke(
            cli_app, ["search", query, "--mode", mode, "--output", "json"]
        )
        if result.exit_code != 0:
            logs.append("unsupported reasoning mode")
    state["active"] = False

    data = {}
    try:
        data = json.loads(result.stdout)
    except Exception:
        lines = result.stdout.splitlines()
        start_idx = None
        for idx, line in enumerate(lines):
            if '"answer"' in line:
                start_idx = idx - 1 if idx > 0 else idx
                break
        if start_idx is not None:
            try:
                data = json.loads("\n".join(lines[start_idx:]))
            except Exception:
                data = {}
    return {
        "record": record,
        "config_params": params,
        "exit_code": result.exit_code,
        "data": data,
        "output": result.stdout,
        "stderr": result.stderr,
        "logs": logs,
        "state": state,
    }


@then("the CLI should exit successfully")
def cli_success(run_result):
    assert run_result["exit_code"] == 0
    assert run_result.get("stderr", "") == ""


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


@then(parsers.parse('the reasoning steps should be "{steps}"'))
def assert_reasoning(run_result: dict, steps: str) -> None:
    expected = [s.strip() for s in steps.split(";") if s.strip()]
    actual = [c.get("content") for c in run_result["data"].get("reasoning", [])]
    assert actual == expected


@then(parsers.parse("the metrics should record {count:d} cycles"))
def assert_metrics_cycles(run_result: dict, count: int) -> None:
    metrics = run_result["data"].get("metrics", {}).get("execution_metrics", {})
    assert metrics.get("cycles_completed") == count


@then(parsers.parse('the metrics should list agents "{agents}"'))
def assert_metrics_agents(run_result: dict, agents: str) -> None:
    expected = [a.strip() for a in agents.split(",") if a.strip()]
    metrics = run_result["data"].get("metrics", {}).get("execution_metrics", {})
    actual = list(metrics.get("agent_timings", {}).keys())
    assert actual == expected


@then("the CLI should exit with an error")
def cli_error(run_result: dict) -> None:
    assert run_result["exit_code"] != 0
    assert "mode" in run_result["output"].lower()
    assert run_result.get("stderr") not in (None, "")


@then("no agents should execute")
def assert_no_agents(run_result: dict) -> None:
    assert run_result["record"] == []
