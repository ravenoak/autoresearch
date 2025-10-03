from __future__ import annotations
from tests.behavior.utils import empty_metrics

from dataclasses import dataclass
from typing import Callable

import pytest
from click.testing import CliRunner, Result
from pytest_bdd import parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from tests.behavior.context import BehaviorContext, get_required, set_value

from .common_steps import cli_app


@dataclass(slots=True)
class CLIExecution:
    """Capture a CLI invocation and the resulting configuration."""

    config: ConfigModel
    result: Result


@dataclass(slots=True)
class ParallelExecution:
    """Capture parallel CLI invocation metadata."""

    result: Result
    groups: list[list[str]]


@scenario("../features/cli_options.feature", "Set loops and token budget via CLI")
def test_token_budget_loops(bdd_context: BehaviorContext) -> None:
    pass


@scenario("../features/cli_options.feature", "Choose specific agents via CLI")
def test_choose_agents(bdd_context: BehaviorContext) -> None:
    pass


@scenario("../features/cli_options.feature", "Run agent groups in parallel via CLI")
def test_parallel_groups(bdd_context: BehaviorContext) -> None:
    pass


@scenario("../features/cli_options.feature", "Override reasoning mode via CLI")
def test_cli_reasoning_mode(bdd_context: BehaviorContext) -> None:
    pass


@scenario("../features/cli_options.feature", "Override primus start via CLI")
def test_cli_primus_start(bdd_context: BehaviorContext) -> None:
    pass


def _install_query_stub(
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
) -> Callable[[str, ConfigModel, object | None], QueryResponse]:
    """Install an orchestrator stub that records the provided config."""

    def mock_run_query(
        query: str,
        cfg: ConfigModel,
        callbacks: object | None = None,
        *,
        agent_factory: object | None = None,
        storage_manager: object | None = None,
    ) -> QueryResponse:
        set_value(bdd_context, "captured_config", cfg)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics=empty_metrics())

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    return mock_run_query


@when(
    parsers.parse(
        'I run `autoresearch search "{query}" --loops {loops:d} --token-budget {budget:d} --no-ontology-reasoning`'
    )
)
def run_with_budget(
    query: str,
    loops: int,
    budget: int,
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
) -> None:
    ConfigLoader.reset_instance()
    _install_query_stub(monkeypatch, bdd_context)
    result = cli_runner.invoke(
        cli_app,
        [
            "search",
            query,
            "--loops",
            str(loops),
            "--token-budget",
            str(budget),
            "--no-ontology-reasoning",
        ],
    )
    config = get_required(bdd_context, "captured_config", ConfigModel)
    execution = CLIExecution(config=config, result=result)
    set_value(bdd_context, "cli_execution", execution)


@then(parsers.parse("the search config should have loops {loops:d} and token budget {budget:d}"))
def check_budget_config(
    bdd_context: BehaviorContext,
    loops: int,
    budget: int,
) -> None:
    execution = get_required(bdd_context, "cli_execution", CLIExecution)
    cfg = execution.config
    assert cfg.loops == loops
    assert cfg.token_budget == budget
    result = execution.result
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@when(parsers.parse('I run `autoresearch search "{query}" --agents {agents}`'))
def run_with_agents(
    query: str,
    agents: str,
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
) -> None:
    ConfigLoader.reset_instance()
    _install_query_stub(monkeypatch, bdd_context)
    result = cli_runner.invoke(cli_app, ["search", query, "--agents", agents])
    config = get_required(bdd_context, "captured_config", ConfigModel)
    execution = CLIExecution(config=config, result=result)
    set_value(bdd_context, "cli_execution", execution)


@then(parsers.parse('the search config should list agents "{agents}"'))
def check_agents_config(bdd_context: BehaviorContext, agents: str) -> None:
    execution = get_required(bdd_context, "cli_execution", CLIExecution)
    cfg = execution.config
    expected = [a.strip() for a in agents.split(",")]
    assert cfg.agents == expected
    result = execution.result
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@when(
    parsers.re(
        r'^I run `autoresearch search --parallel --agent-groups "(?P<g1>.+)" "(?P<g2>.+)" "(?P<query>.+)"`$'
    )
)
def run_parallel_cli(
    g1: str,
    g2: str,
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
) -> None:
    ConfigLoader.reset_instance()
    groups = [[a.strip() for a in g1.split(",")], [a.strip() for a in g2.split(",")]]

    def mock_parallel(
        q: str,
        cfg: ConfigModel,
        agent_groups: list[list[str]],
    ) -> QueryResponse:
        set_value(bdd_context, "captured_config", cfg)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics=empty_metrics())

    monkeypatch.setattr(Orchestrator, "run_parallel_query", mock_parallel)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(
        cli_app,
        ["search", "--parallel", "--agent-groups", g1, "--agent-groups", g2, query],
    )
    parallel = ParallelExecution(result=result, groups=groups)
    set_value(bdd_context, "parallel_execution", parallel)


@when(parsers.parse('I run `autoresearch search "{query}" --reasoning-mode {mode}`'))
def run_with_reasoning(
    query: str,
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
) -> None:
    ConfigLoader.reset_instance()
    _install_query_stub(monkeypatch, bdd_context)
    result = cli_runner.invoke(cli_app, ["search", query, "--reasoning-mode", mode])
    config = get_required(bdd_context, "captured_config", ConfigModel)
    execution = CLIExecution(config=config, result=result)
    set_value(bdd_context, "cli_execution", execution)


@then(parsers.parse('the search config should use reasoning mode "{mode}"'))
def check_reasoning_mode(bdd_context: BehaviorContext, mode: str) -> None:
    execution = get_required(bdd_context, "cli_execution", CLIExecution)
    cfg = execution.config
    assert cfg.reasoning_mode.value == mode
    result = execution.result
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@when(parsers.parse('I run `autoresearch search "{query}" --primus-start {index:d}`'))
def run_with_primus(
    query: str,
    index: int,
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
) -> None:
    ConfigLoader.reset_instance()
    _install_query_stub(monkeypatch, bdd_context)
    result = cli_runner.invoke(cli_app, ["search", query, "--primus-start", str(index)])
    config = get_required(bdd_context, "captured_config", ConfigModel)
    execution = CLIExecution(config=config, result=result)
    set_value(bdd_context, "cli_execution", execution)


@then(parsers.parse('the search config should have primus start {index:d}'))
def check_primus_start(bdd_context: BehaviorContext, index: int) -> None:
    execution = get_required(bdd_context, "cli_execution", CLIExecution)
    cfg = execution.config
    assert cfg.primus_start == index
    result = execution.result
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@then(parsers.parse('the parallel query should use groups "{g1}" and "{g2}"'))
def check_parallel_groups(
    bdd_context: BehaviorContext,
    g1: str,
    g2: str,
) -> None:
    parallel = get_required(bdd_context, "parallel_execution", ParallelExecution)
    expected = [[a.strip() for a in g1.split(",")], [a.strip() for a in g2.split(",")]]
    assert parallel.groups == expected
    result = parallel.result
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""
