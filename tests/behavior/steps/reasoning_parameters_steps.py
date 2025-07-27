from pytest_bdd import scenario, when, then, parsers
from autoresearch.main import app as cli_app
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


@scenario("../features/reasoning_parameters.feature", "Override circuit breaker settings via CLI")
def test_circuit_breaker_flags(bdd_context):
    pass


@scenario("../features/reasoning_parameters.feature", "Tune adaptive token budgeting via CLI")
def test_adaptive_budget_flags(bdd_context):
    pass


@when(parsers.parse('I run `autoresearch search "{query}" --circuit-breaker-threshold {threshold:d} --circuit-breaker-cooldown {cooldown:d} --no-ontology-reasoning'))
def run_breaker_cli(query, threshold, cooldown, monkeypatch, cli_runner, bdd_context):
    ConfigLoader.reset_instance()

    def mock_run_query(q, cfg, callbacks=None):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

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
def check_breaker_config(bdd_context, threshold, cooldown):
    cfg = bdd_context.get("cfg")
    assert cfg.circuit_breaker_threshold == threshold
    assert cfg.circuit_breaker_cooldown == cooldown
    assert bdd_context["result"].exit_code == 0


@when(parsers.parse('I run `autoresearch search "{query}" --adaptive-max-factor {factor:d} --adaptive-min-buffer {buffer:d} --no-ontology-reasoning'))
def run_adaptive_cli(query, factor, buffer, monkeypatch, cli_runner, bdd_context):
    ConfigLoader.reset_instance()

    def mock_run_query(q, cfg, callbacks=None):
        bdd_context["cfg"] = cfg
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

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
def check_adaptive_config(bdd_context, factor, buffer):
    cfg = bdd_context.get("cfg")
    assert cfg.adaptive_max_factor == factor
    assert cfg.adaptive_min_buffer == buffer
    assert bdd_context["result"].exit_code == 0
