from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterator

import pytest
from click.testing import CliRunner, Result
from httpx import Client, Response
from pytest_bdd import parsers, scenario, then, when

from autoresearch.models import QueryResponse
from tests.behavior.context import BehaviorContext, get_required, set_value

from .common_steps import cli_app

pytest_plugins = ["tests.behavior.steps.common_steps"]


@dataclass(slots=True)
class CLIExpectation:
    """Capture a CLI invocation alongside its expected response."""

    result: Result
    expected: QueryResponse


@dataclass(slots=True)
class HTTPExpectation:
    """Capture an HTTP response with the associated expected payload."""

    response: Response
    expected: QueryResponse


@dataclass(slots=True)
class VisualizationResult:
    """Capture CLI visualization execution details."""

    result: Result
    path: Path


@when(parsers.parse('I run `autoresearch search "{query}"` in a terminal'))
def run_cli_query(
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: QueryResponse,
) -> None:
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query])
    expectation = CLIExpectation(result=result, expected=dummy_query_response)
    set_value(bdd_context, "cli_expectation", expectation)


@when(parsers.parse('I run `autoresearch search "{query}" --reasoning-mode {mode}` in a terminal'))
def run_cli_query_with_mode(
    query: str,
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: QueryResponse,
) -> None:
    """Run CLI search specifying a reasoning mode."""

    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query, "--reasoning-mode", mode])
    expectation = CLIExpectation(result=result, expected=dummy_query_response)
    set_value(bdd_context, "cli_expectation", expectation)


@then(
    "I should receive a readable Markdown answer with `answer`, `citations`, `reasoning`, and `metrics` sections",
)
def check_cli_output(bdd_context: BehaviorContext) -> None:
    expectation = get_required(bdd_context, "cli_expectation", CLIExpectation)
    result = expectation.result
    expected = expectation.expected
    assert result.exit_code == 0
    assert result.stderr == ""
    out = result.stdout
    assert "# Answer" in out
    assert "## Citations" in out
    assert "## Reasoning" in out
    assert "## Metrics" in out
    assert expected.answer in out
    for cite in expected.citations:
        assert cite in out
    for step in expected.reasoning:
        assert step in out
    for key, value in expected.metrics.items():
        assert str(value) in out


@when(parsers.parse('I send a POST request to `/query` with JSON `{ "query": "{query}" }`'))
def send_http_query(
    query: str,
    bdd_context: BehaviorContext,
    api_client: Client,
    dummy_query_response: QueryResponse,
) -> None:
    response = api_client.post("/query", json={"query": query})
    expectation = HTTPExpectation(response=response, expected=dummy_query_response)
    set_value(bdd_context, "http_expectation", expectation)


@then(
    "the response should be a valid JSON document with keys `answer`, `citations`, `reasoning`, and `metrics`",
)
def check_http_response(bdd_context: BehaviorContext) -> None:
    expectation = get_required(bdd_context, "http_expectation", HTTPExpectation)
    response = expectation.response
    expected = expectation.expected
    assert response.status_code == 200
    data = response.json()
    expected_dict = expected.model_dump()
    for key, value in expected_dict.items():
        assert data.get(key) == value
    assert "error" not in data


@when(parsers.re(r'I run `autoresearch\.search\("(?P<query>.+)"\)` via the MCP CLI'))
def run_mcp_cli_query(
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: QueryResponse,
) -> None:
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = cli_runner.invoke(cli_app, ["search", query])
    expectation = CLIExpectation(result=result, expected=dummy_query_response)
    set_value(bdd_context, "mcp_expectation", expectation)


@when(parsers.parse('I run `autoresearch search "{query}" -i` and refine to "{refined}" then exit'))
def run_interactive_query(
    query: str,
    refined: str,
    monkeypatch: pytest.MonkeyPatch,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: QueryResponse,
) -> None:
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel

    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: ConfigModel(loops=2),
    )
    responses: Iterator[str] = iter([refined, "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query, "--interactive"])
    expectation = CLIExpectation(result=result, expected=dummy_query_response)
    set_value(bdd_context, "cli_expectation", expectation)


@when(parsers.re(r'I run `autoresearch visualize "(?P<query>.+)" (?P<file>.+)`'))
def run_visualize_cli(
    query: str,
    file: str,
    tmp_path: Path,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
    dummy_query_response: QueryResponse,
) -> None:
    out = tmp_path / file
    result = cli_runner.invoke(cli_app, ["visualize", query, str(out)])
    visualization = VisualizationResult(result=result, path=out)
    set_value(bdd_context, "visualization", visualization)
    expectation = CLIExpectation(result=result, expected=dummy_query_response)
    set_value(bdd_context, "cli_expectation", expectation)


@when(parsers.re(r"I run `autoresearch visualize-rdf (?P<file>.+)`"))
def run_visualize_rdf_cli(
    file: str,
    tmp_path: Path,
    bdd_context: BehaviorContext,
    cli_runner: CliRunner,
) -> None:
    out = tmp_path / file
    result = cli_runner.invoke(cli_app, ["visualize-rdf", str(out)])
    visualization = VisualizationResult(result=result, path=out)
    set_value(bdd_context, "visualization", visualization)


@then(parsers.parse('the visualization file "{file}" should exist'))
def check_viz_file(file: str, bdd_context: BehaviorContext) -> None:
    visualization = get_required(bdd_context, "visualization", VisualizationResult)
    path = visualization.path
    assert path.exists() and path.stat().st_size > 0
    path.unlink()
    result = visualization.result
    assert result.exit_code == 0
    assert result.stderr == ""


@then(
    "I should receive a JSON output matching the defined schema for `answer`, `citations`, `reasoning`, and `metrics`",
)
def check_mcp_cli_output(bdd_context: BehaviorContext) -> None:
    expectation = get_required(bdd_context, "mcp_expectation", CLIExpectation)
    result = expectation.result
    expected = expectation.expected
    assert result.exit_code == 0
    assert result.stderr == ""
    lines = result.stdout.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if '"answer"' in line:
            start_idx = max(0, idx - 1)
            break
    assert start_idx is not None, "No JSON found in CLI output"
    json_str = "\n".join(lines[start_idx:])
    data = json.loads(json_str)
    assert data == expected.model_dump()


@scenario("../features/query_interface.feature", "Submit query via CLI")
def test_cli_query() -> None:
    pass


@scenario("../features/query_interface.feature", "Submit query via HTTP API")
def test_http_query() -> None:
    pass


@pytest.mark.skip(reason="MCP CLI not required for minimal verify")
@scenario("../features/query_interface.feature", "Submit query via MCP tool")
def test_mcp_query() -> None:
    pass


@scenario("../features/query_interface.feature", "Refine query interactively via CLI")
def test_interactive_query() -> None:
    pass


@scenario("../features/query_interface.feature", "Visualize query results via CLI")
def test_visualize_query() -> None:
    pass


@scenario("../features/query_interface.feature", "Visualize RDF graph via CLI")
def test_visualize_rdf_cli() -> None:
    pass


@scenario(
    "../features/query_interface.feature",
    "Submit query via CLI with reasoning mode",
)
def test_cli_query_with_reasoning_mode() -> None:
    """CLI query works when specifying reasoning mode."""
    pass
