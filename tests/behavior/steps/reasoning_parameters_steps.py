from tests.behavior.utils import empty_metrics
from tests.behavior.context import BehaviorContext
from pytest_bdd import scenario, when, then, parsers
from autoresearch.main import app as cli_app
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


@scenario("../features/reasoning_parameters.feature", "Override circuit breaker settings via CLI")
def test_circuit_breaker_flags(bdd_context: BehaviorContext):
    pass


@scenario("../features/reasoning_parameters.feature", "Tune adaptive token budgeting via CLI")
def test_adaptive_budget_flags(bdd_context: BehaviorContext):
    pass


@when(parsers.parse('I run `autoresearch search "{query}" --circuit-breaker-threshold {threshold:d} --circuit-breaker-cooldown {cooldown:d} --no-ontology-reasoning'))
def run_breaker_cli(query, threshold, cooldown, monkeypatch, cli_runner, bdd_context: BehaviorContext):
    ConfigLoader.reset_instance()

    def mock_run_query(
        q,
        cfg,
        callbacks=None,
        *,
        agent_factory=None,
        storage_manager=None,
    ):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics=empty_metrics())

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(
        cli_app,
        [
            "search",
            query,
            "--circuit-breaker-threshold",
            str(threshold),
            "--circuit-breaker-cooldown",
            str(cooldown),
            "--no-ontology-reasoning",
        ],
    )
    bdd_context["result"] = result


@then(parsers.parse("the search config should set circuit breaker threshold {threshold:d} and cooldown {cooldown:d}"))
def check_breaker_config(bdd_context: BehaviorContext, threshold, cooldown):
    cfg = bdd_context.get("cfg")
    assert cfg.circuit_breaker_threshold == threshold
    assert cfg.circuit_breaker_cooldown == cooldown
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""


@when(parsers.parse('I run `autoresearch search "{query}" --adaptive-max-factor {factor:d} --adaptive-min-buffer {buffer:d} --no-ontology-reasoning'))
def run_adaptive_cli(query, factor, buffer, monkeypatch, cli_runner, bdd_context: BehaviorContext):
    ConfigLoader.reset_instance()

    def mock_run_query(
        q,
        cfg,
        callbacks=None,
        *,
        agent_factory=None,
        storage_manager=None,
    ):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics=empty_metrics())

    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel())
    result = cli_runner.invoke(
        cli_app,
        [
            "search",
            query,
            "--adaptive-max-factor",
            str(factor),
            "--adaptive-min-buffer",
            str(buffer),
            "--no-ontology-reasoning",
        ],
    )
    bdd_context["result"] = result


@then(parsers.parse("the search config should have adaptive factor {factor:d} and buffer {buffer:d}"))
def check_adaptive_config(bdd_context: BehaviorContext, factor, buffer):
    cfg = bdd_context.get("cfg")
    assert cfg.adaptive_max_factor == factor
    assert cfg.adaptive_min_buffer == buffer
    result = bdd_context["result"]
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""
