# flake8: noqa
import json
from pytest_bdd import scenario, when, then, parsers

from .common_steps import app_running, app_running_with_default, application_running, cli_app


@when(parsers.parse('I run `autoresearch search "{query}"` in a terminal'))
def run_cli_query(query, monkeypatch, bdd_context, cli_runner, dummy_query_response):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context.update({"cli_result": result, "expected": dummy_query_response})


@then(
    "I should receive a readable Markdown answer with `answer`, `citations`, "
    "`reasoning`, and `metrics` sections",
)
def check_cli_output(bdd_context):
    result = bdd_context["cli_result"]
    expected = bdd_context["expected"]
    assert result.exit_code == 0
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


@when(
    parsers.parse(
        'I send a POST request to `/query` with JSON `{ "query": "{query}" }`'
    )
)
def send_http_query(query, bdd_context, api_client, dummy_query_response):
    response = api_client.post("/query", json={"query": query})
    bdd_context.update({"http_response": response, "expected": dummy_query_response})


@then(
    "the response should be a valid JSON document with keys `answer`, `citations`, `reasoning`, and `metrics`",
)
def check_http_response(bdd_context):
    response = bdd_context["http_response"]
    expected = bdd_context["expected"]
    assert response.status_code == 200
    data = response.json()
    assert data == expected.model_dump()


@when(parsers.re(r'I run `autoresearch\.search\("(?P<query>.+)"\)` via the MCP CLI'))
def run_mcp_cli_query(query, monkeypatch, bdd_context, cli_runner, dummy_query_response):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context.update({"mcp_result": result, "expected": dummy_query_response})


@when(
    parsers.parse(
        'I run `autoresearch search "{query}" -i` and refine to "{refined}" then exit'
    )
)
def run_interactive_query(query, refined, monkeypatch, bdd_context, cli_runner, dummy_query_response):
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader

    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: ConfigModel(loops=2),
    )
    responses = iter([refined, "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query, "--interactive"])
    bdd_context.update({"cli_result": result, "expected": dummy_query_response})


@when(parsers.re(r'I run `autoresearch visualize "(?P<query>.+)" (?P<file>.+)`'))
def run_visualize_cli(query, file, tmp_path, bdd_context, cli_runner, dummy_query_response):
    out = tmp_path / file
    result = cli_runner.invoke(cli_app, ["visualize", query, str(out)])
    bdd_context.update({"viz_result": result, "viz_path": out, "expected": dummy_query_response})


@when(parsers.re(r'I run `autoresearch visualize-rdf (?P<file>.+)`'))
def run_visualize_rdf_cli(file, tmp_path, bdd_context, cli_runner):
    out = tmp_path / file
    result = cli_runner.invoke(cli_app, ["visualize-rdf", str(out)])
    bdd_context["viz_result"] = result
    bdd_context["viz_path"] = out


@then(parsers.parse('the visualization file "{file}" should exist'))
def check_viz_file(file, bdd_context):
    path = bdd_context["viz_path"]
    assert path.exists() and path.stat().st_size > 0
    path.unlink()


@then(
    "I should receive a JSON output matching the defined schema for `answer`, `citations`, `reasoning`, and `metrics`",
)
def check_mcp_cli_output(bdd_context):
    result = bdd_context["mcp_result"]
    expected = bdd_context["expected"]
    assert result.exit_code == 0
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
def test_cli_query():
    pass


@scenario("../features/query_interface.feature", "Submit query via HTTP API")
def test_http_query():
    pass


@scenario("../features/query_interface.feature", "Submit query via MCP tool")
def test_mcp_query():
    pass


@scenario("../features/query_interface.feature", "Refine query interactively via CLI")
def test_interactive_query():
    pass


@scenario("../features/query_interface.feature", "Visualize query results via CLI")
def test_visualize_query():
    pass


@scenario("../features/query_interface.feature", "Visualize RDF graph via CLI")
def test_visualize_rdf_cli():
    pass
