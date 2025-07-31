from __future__ import annotations

from unittest.mock import patch

from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator


@scenario("../features/reasoning_mode.feature", "Direct mode runs Synthesizer only")
def test_direct_mode():
    pass


@scenario("../features/reasoning_mode.feature", "Chain-of-thought mode loops Synthesizer")
def test_chain_of_thought_mode():
    pass


@scenario("../features/reasoning_mode.feature", "Dialectical mode with custom Primus start")
def test_dialectical_custom_primus():
    pass


@scenario("../features/reasoning_mode.feature", "Dialectical reasoning with a realistic query")
def test_dialectical_real_query():
    pass


@given(parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config")
def loops_config(count: int, monkeypatch):
    cfg = ConfigModel.model_construct(
        agents=["Synthesizer", "Contrarian", "FactChecker"], loops=count
    )
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


@when(parsers.parse('I run the orchestrator on query "{query}"'), target_fixture="run_result")
def run_orchestrator(query: str, config: ConfigModel):
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
        Orchestrator.run_query(query, config)

    return {"record": record, "config_params": params}


@then(parsers.parse('the loops used should be {count:d}'))
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
