# flake8: noqa
import json
from pytest_bdd import scenario, when, then, parsers

from .common_steps import *  # noqa: F401,F403


@when(parsers.parse('I run `autoresearch search "{query}"` in a terminal'))
def run_cli_query(query, monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context["cli_result"] = result


@then(
    "I should receive a readable Markdown answer with `answer`, `citations`, "
    "`reasoning`, and `metrics` sections",
)
def check_cli_output(bdd_context):
    result = bdd_context["cli_result"]
    assert result.exit_code == 0
    out = result.stdout
    assert "# Answer" in out
    assert "## Citations" in out
    assert "## Reasoning" in out
    assert "## Metrics" in out


@when(
    parsers.parse(
        'I send a POST request to `/query` with JSON `{ "query": "{query}" }`'
    )
)
def send_http_query(query, bdd_context, api_client):
    response = api_client.post("/query", json={"query": query})
    bdd_context["http_response"] = response


@then(
    "the response should be a valid JSON document with keys `answer`, `citations`, `reasoning`, and `metrics`",
)
def check_http_response(bdd_context):
    response = bdd_context["http_response"]
    assert response.status_code == 200
    data = response.json()
    for key in ["answer", "citations", "reasoning", "metrics"]:
        assert key in data


@when(parsers.re(r'I run `autoresearch\.search\("(?P<query>.+)"\)` via the MCP CLI'))
def run_mcp_cli_query(query, monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context["mcp_result"] = result


@when(
    parsers.parse(
        'I run `autoresearch search "{query}" -i` and refine to "{refined}" then exit'
    )
)
def run_interactive_query(query, refined, monkeypatch, bdd_context, cli_runner):
    from autoresearch.config import ConfigModel, ConfigLoader

    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: ConfigModel(loops=2),
    )
    responses = iter([refined, "q"])
    monkeypatch.setattr("autoresearch.main.Prompt.ask", lambda *a, **k: next(responses))
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query, "--interactive"])
    bdd_context["cli_result"] = result


@when(parsers.re(r'I run `autoresearch visualize "(?P<query>.+)" (?P<file>.+)`'))
def run_visualize_cli(query, file, tmp_path, bdd_context, cli_runner):
    out = tmp_path / file
    result = cli_runner.invoke(cli_app, ["visualize", query, str(out)])
    bdd_context["viz_result"] = result
    bdd_context["viz_path"] = out


@then(parsers.parse('the visualization file "{file}" should exist'))
def check_viz_file(file, bdd_context):
    path = bdd_context["viz_path"]
    assert path.exists() and path.stat().st_size > 0


@then(
    "I should receive a JSON output matching the defined schema for `answer`, `citations`, `reasoning`, and `metrics`",
)
def check_mcp_cli_output(bdd_context):
    result = bdd_context["mcp_result"]
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
    for key in ["answer", "citations", "reasoning", "metrics"]:
        assert key in data


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
