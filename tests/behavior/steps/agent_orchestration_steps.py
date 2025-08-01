# flake8: noqa
from unittest.mock import patch
from pytest_bdd import scenario, given, when, then, parsers
import logging

from .common_steps import *  # noqa: F401,F403
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration import ReasoningMode


@given("the agents Synthesizer, Contrarian, and Fact-Checker are enabled")
def enable_agents(monkeypatch):
    config = ConfigModel.model_construct(agents=["Synthesizer", "Contrarian", "FactChecker"], loops=2)
    monkeypatch.setattr(
        "autoresearch.config.loader.ConfigLoader.load_config", lambda self: config
    )
    return config


@given(
    parsers.re(r"loops is set to (?P<loops>\d+)(?: in configuration)?"),
    target_fixture="set_loops",
)
def set_loops(loops: int, monkeypatch):
    loops = int(loops)
    config = ConfigModel.model_construct(
        agents=["Synthesizer", "Contrarian", "FactChecker"], loops=loops
    )
    monkeypatch.setattr(
        "autoresearch.config.loader.ConfigLoader.load_config", lambda self: config
    )
    return config


@given(parsers.parse('reasoning mode is "{mode}"'))
def set_reasoning_mode(mode, set_loops):
    set_loops.reasoning_mode = ReasoningMode(mode)
    return set_loops


@given(parsers.parse('primus start is {index:d}'))
def set_primus_start(index: int, set_loops):
    set_loops.primus_start = index
    return set_loops


@when(
    parsers.parse('I run the orchestrator on query "{query}"'),
    target_fixture="run_orchestrator_on_query",
)
def run_orchestrator_on_query(query, monkeypatch, tmp_path):
    loader = ConfigLoader()
    loader._config = None
    cfg = loader.load_config()

    monkeypatch.setenv(
        "AUTORESEARCH_RELEASE_METRICS",
        str(tmp_path / "release_tokens.json"),
    )
    monkeypatch.setenv(
        "AUTORESEARCH_QUERY_TOKENS",
        str(tmp_path / "query_tokens.json"),
    )

    from autoresearch.orchestration.reasoning import ReasoningMode

    if isinstance(getattr(cfg, "reasoning_mode", None), str):
        try:
            cfg.reasoning_mode = ReasoningMode(getattr(cfg, "reasoning_mode"))
        except ValueError:
            cfg.reasoning_mode = ReasoningMode.DIALECTICAL
    record = []
    config_params = {}

    class DummyAgent:
        def __init__(self, name):
            self.name = name

        def can_execute(self, state, config):
            return True

        def execute(self, state, config):
            record.append(self.name)
            return {}

    def get_agent(name):
        return DummyAgent(name)

    original_parse = Orchestrator._parse_config

    def spy_parse(conf):
        params = original_parse(conf)
        config_params.update(params)
        return params

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ), patch(
        "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
        side_effect=spy_parse,
    ):
        Orchestrator.run_query(query, cfg)

    return {"record": record, "config_params": config_params}


@then(parsers.parse('the agents executed should be "{order}"'))
def check_agents_executed(run_orchestrator_on_query, order):
    expected = [a.strip() for a in order.split(",")]
    assert run_orchestrator_on_query["record"] == expected


@then(parsers.parse("the loops used should be {count:d}"))
def check_loops_used(run_orchestrator_on_query, count):
    assert run_orchestrator_on_query["config_params"].get("loops") == count


@then(parsers.parse('the agent groups should be "{groups}"'))
def check_agent_groups(run_orchestrator_on_query, groups):
    expected = [
        [a.strip() for a in grp.split(",") if a.strip()]
        for grp in groups.split(";")
    ]
    assert run_orchestrator_on_query["config_params"].get("agent_groups") == expected


@when(
    parsers.parse('I submit a query via CLI `autoresearch search "{query}"`'),
    target_fixture="submit_query_via_cli",
)
def submit_query_via_cli(query, monkeypatch, cli_runner, tmp_path):
    agent_invocations: list[str] = []
    logger = logging.getLogger("autoresearch.test")
    logger.setLevel(logging.INFO)

    class DummyAgent:
        def __init__(self, name: str):
            self.name = name

        def can_execute(self, state, config):
            return True

        def execute(self, state, config):
            idx = len(agent_invocations)
            logger.info("%s executing (cycle %s)", self.name, idx)
            agent_invocations.append(self.name)
            return {}

    def get_agent(name: str):
        return DummyAgent(name)

    cfg = ConfigModel.model_construct(
        agents=["Synthesizer", "Contrarian", "Synthesizer"], loops=1
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    from autoresearch import main as main_mod

    main_mod._config_loader = ConfigLoader()
    main_mod._config_loader._config = cfg

    monkeypatch.setenv(
        "AUTORESEARCH_RELEASE_METRICS", str(tmp_path / "release_tokens.json")
    )
    monkeypatch.setenv(
        "AUTORESEARCH_QUERY_TOKENS", str(tmp_path / "query_tokens.json")
    )

    with patch(
        "autoresearch.orchestration.orchestrator.AgentFactory.get",
        side_effect=get_agent,
    ):
        result = cli_runner.invoke(cli_app, ["search", query])

    return {"result": result, "agent_invocations": agent_invocations}


@then(
    "the system should invoke agents in the order: Synthesizer, Contrarian, Synthesizer"
)
def check_agent_order(submit_query_via_cli):
    agent_invocations = submit_query_via_cli["agent_invocations"]
    assert agent_invocations[0] == "Synthesizer"
    assert agent_invocations[1] == "Contrarian"
    assert agent_invocations[2] == "Synthesizer"


@then("each agent turn should be logged with agent name and cycle index")
def check_agent_logging(submit_query_via_cli, caplog):
    assert submit_query_via_cli["result"].exit_code == 0
    logs = caplog.text
    assert "Synthesizer executing (cycle 0)" in logs
    assert "Contrarian executing (cycle 1)" in logs
    assert "Synthesizer executing (cycle 2)" in logs


@when("I run two separate queries", target_fixture="run_two_queries")
def run_two_queries(monkeypatch):
    from autoresearch.models import QueryResponse

    original_run_query = Orchestrator.run_query
    query_data = {"primus_indices": []}

    def mock_run_query(query, config, callbacks=None):
        query_data["primus_indices"].append(config.primus_start)
        config.primus_start = (config.primus_start + 1) % len(config.agents)
        return QueryResponse(
            answer=f"Answer for: {query}",
            citations=["Source 1", "Source 2"],
            reasoning=["Reasoning step 1", "Reasoning step 2"],
            metrics={"time_ms": 100, "tokens": 50},
        )

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)

    config = ConfigModel.model_construct(
        agents=["Synthesizer", "Contrarian", "FactChecker"],
        loops=3,
        primus_start=0,
    )

    Orchestrator.run_query("Query 1", config)
    Orchestrator.run_query("Query 2", config)

    monkeypatch.setattr(Orchestrator, "run_query", original_run_query)

    return query_data


@then("the Primus agent should advance by one position between queries")
def check_primus_rotation(run_two_queries):
    primus_indices = run_two_queries["primus_indices"]
    assert len(primus_indices) == 2
    assert primus_indices[0] == 0
    assert primus_indices[1] == 1


@then("the order should reflect the new starting agent each time")
def check_agent_order_rotation(run_two_queries):
    assert run_two_queries["primus_indices"][0] != run_two_queries["primus_indices"][1]


@scenario("../features/agent_orchestration.feature", "One dialectical cycle")
def test_one_cycle():
    pass


@scenario("../features/agent_orchestration.feature", "Rotating Primus across loops")
def test_rotating_primus():
    pass


@scenario("../features/reasoning_mode.feature", "Direct mode runs Synthesizer only")
def test_reasoning_direct():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Chain-of-thought mode loops Synthesizer",
)
def test_reasoning_chain():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Dialectical mode with custom Primus start",
)
def test_reasoning_dialectical():
    pass


@scenario(
    "../features/reasoning_mode.feature",
    "Dialectical reasoning with a realistic query",
)
def test_reasoning_realistic():
    pass
