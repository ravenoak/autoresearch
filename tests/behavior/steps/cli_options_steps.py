# flake8: noqa
import json
import pytest
from pytest_bdd import scenario, when, then, parsers

from .common_steps import app_running, app_running_with_default, application_running, cli_app
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


@scenario("../features/cli_options.feature", "Set loops and token budget via CLI")
def test_token_budget_loops(bdd_context):
    pass


@scenario("../features/cli_options.feature", "Choose specific agents via CLI")
def test_choose_agents(bdd_context):
    pass


@scenario("../features/cli_options.feature", "Run agent groups in parallel via CLI")
def test_parallel_groups(bdd_context):
    pass


@scenario("../features/cli_options.feature", "Override reasoning mode via CLI")
def test_cli_reasoning_mode(bdd_context):
    pass


@scenario("../features/cli_options.feature", "Override primus start via CLI")
def test_cli_primus_start(bdd_context):
    pass


@when(
    parsers.parse(
        'I run `autoresearch search "{query}" --loops {loops:d} --token-budget {budget:d} --no-ontology-reasoning`'
    )
)
def run_with_budget(query, loops, budget, monkeypatch, cli_runner, bdd_context):
    ConfigLoader.reset_instance()
    def mock_run_query(q, cfg, callbacks=None):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(
        cli_app,
        ["search", query, "--loops", str(loops), "--token-budget", str(budget), "--no-ontology-reasoning"],
    )
    bdd_context["result"] = result


@then(parsers.parse("the search config should have loops {loops:d} and token budget {budget:d}"))
def check_budget_config(bdd_context, loops, budget):
    cfg = bdd_context.get("cfg")
    assert cfg.loops == loops
    assert cfg.token_budget == budget
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@when(parsers.parse('I run `autoresearch search "{query}" --agents {agents}`'))
def run_with_agents(query, agents, monkeypatch, cli_runner, bdd_context):
    ConfigLoader.reset_instance()
    def mock_run_query(q, cfg, callbacks=None):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(cli_app, ["search", query, "--agents", agents])
    bdd_context["result"] = result


@then(parsers.parse('the search config should list agents "{agents}"'))
def check_agents_config(bdd_context, agents):
    cfg = bdd_context.get("cfg")
    expected = [a.strip() for a in agents.split(",")]
    assert cfg.agents == expected
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@when(
    parsers.re(
        r'^I run `autoresearch search --parallel --agent-groups "(?P<g1>.+)" "(?P<g2>.+)" "(?P<query>.+)"`$'
    )
)
def run_parallel_cli(g1, g2, query, monkeypatch, cli_runner, bdd_context):
    ConfigLoader.reset_instance()
    groups = [[a.strip() for a in g1.split(",")], [a.strip() for a in g2.split(",")]]

    def mock_parallel(q, cfg, agent_groups):
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_parallel_query", mock_parallel)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(
        cli_app,
        ["search", "--parallel", "--agent-groups", g1, "--agent-groups", g2, query],
    )
    bdd_context["result"] = result
    bdd_context["groups"] = groups


@when(parsers.parse('I run `autoresearch search "{query}" --reasoning-mode {mode}`'))
def run_with_reasoning(query, mode, monkeypatch, cli_runner, bdd_context):
    ConfigLoader.reset_instance()

    def mock_run_query(q, cfg, callbacks=None):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(cli_app, ["search", query, "--reasoning-mode", mode])
    bdd_context["result"] = result


@then(parsers.parse('the search config should use reasoning mode "{mode}"'))
def check_reasoning_mode(bdd_context, mode):
    cfg = bdd_context.get("cfg")
    assert cfg.reasoning_mode.value == mode
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@when(parsers.parse('I run `autoresearch search "{query}" --primus-start {index:d}`'))
def run_with_primus(query, index, monkeypatch, cli_runner, bdd_context):
    ConfigLoader.reset_instance()

    def mock_run_query(q, cfg, callbacks=None):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(cli_app, ["search", query, "--primus-start", str(index)])
    bdd_context["result"] = result


@then(parsers.parse('the search config should have primus start {index:d}'))
def check_primus_start(bdd_context, index):
    cfg = bdd_context.get("cfg")
    assert cfg.primus_start == index
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@then(parsers.parse('the parallel query should use groups "{g1}" and "{g2}"'))
def check_parallel_groups(bdd_context, g1, g2):
    expected = [[a.strip() for a in g1.split(",")], [a.strip() for a in g2.split(",")]]
    assert bdd_context.get("groups") == expected
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""
