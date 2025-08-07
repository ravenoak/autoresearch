# flake8: noqa
import json
from pytest_bdd import scenario, when, then, parsers

from .common_steps import app_running, app_running_with_default, application_running, cli_app


@when(parsers.parse('I run `autoresearch search "{query}"` in TTY mode'))
def run_in_terminal(query, monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context["terminal_result"] = result


@then(
    "the output should be in Markdown with sections `# Answer`, `## Citations`, `## Reasoning`, and `## Metrics`"
)
def check_markdown_output(bdd_context):
    result = bdd_context["terminal_result"]
    output = result.stdout
    assert "# Answer" in output
    assert "## Citations" in output
    assert "## Reasoning" in output
    assert "## Metrics" in output
    assert result.stderr == ""


@when(parsers.parse('I run `autoresearch search "{query}" | cat`'))
def run_piped(query, monkeypatch, bdd_context, cli_runner):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context["piped_result"] = result


@then(
    "the output should be valid JSON with keys `answer`, `citations`, `reasoning`, and `metrics`"
)
def check_json_output(bdd_context):
    result = bdd_context["piped_result"]
    output = result.stdout
    data = json.loads(output)
    assert "answer" in data
    assert "citations" in data
    assert "reasoning" in data
    assert "metrics" in data
    assert result.stderr == ""


@when(parsers.re(r'I run `autoresearch search "(?P<query>.+)" --output json`'))
def run_with_json_flag(query, monkeypatch, bdd_context, cli_runner):
    result = cli_runner.invoke(cli_app, ["search", query, "--output", "json"])
    bdd_context["json_flag_result"] = result


@then("the output should be valid JSON regardless of terminal context")
def check_json_output_with_flag(bdd_context):
    result = bdd_context["json_flag_result"]
    output = result.stdout
    data = json.loads(output)
    assert "answer" in data
    assert "citations" in data
    assert "reasoning" in data
    assert "metrics" in data
    assert result.stderr == ""


@when(parsers.re(r'I run `autoresearch search "(?P<query>.+)" --output markdown`'))
def run_with_markdown_flag(query, monkeypatch, bdd_context, cli_runner):
    result = cli_runner.invoke(cli_app, ["search", query, "--output", "markdown"])
    bdd_context["markdown_flag_result"] = result


@then("the output should be Markdown-formatted as in TTY mode")
def check_markdown_output_with_flag(bdd_context):
    result = bdd_context["markdown_flag_result"]
    output = result.stdout
    assert "# Answer" in output
    assert "## Citations" in output
    assert "## Reasoning" in output
    assert "## Metrics" in output
    assert result.stderr == ""


@scenario("../features/output_formatting.feature", "Default TTY output")
def test_default_tty_output(bdd_context):
    assert bdd_context["terminal_result"].exit_code == 0


@scenario("../features/output_formatting.feature", "Piped output defaults to JSON")
def test_piped_json_output(bdd_context):
    assert bdd_context["piped_result"].exit_code == 0


@scenario("../features/output_formatting.feature", "Explicit JSON flag")
def test_explicit_json_flag(bdd_context):
    assert bdd_context["json_flag_result"].exit_code == 0


@scenario("../features/output_formatting.feature", "Explicit Markdown flag")
def test_explicit_markdown_flag(bdd_context):
    assert bdd_context["markdown_flag_result"].exit_code == 0
