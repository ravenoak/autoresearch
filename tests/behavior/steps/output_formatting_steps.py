# mypy: ignore-errors
# flake8: noqa
import json

from autoresearch.models import QueryResponse
from autoresearch.output_format import OutputFormatter
from tests.behavior.context import BehaviorContext
from pytest_bdd import parsers, scenario, then, when

from .common_steps import app_running, app_running_with_default, application_running, cli_app


@when(parsers.parse('I run `autoresearch search "{query}"` in TTY mode'))
def run_in_terminal(query, monkeypatch, bdd_context: BehaviorContext, cli_runner):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context["terminal_result"] = result


@when(
    parsers.parse(
        'I run `autoresearch search "{query}"` in TTY mode with control characters'
    )
)
def run_tty_with_control_characters(
    query, monkeypatch, bdd_context: BehaviorContext, cli_runner
):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    def fake_run_query(*_args, **_kwargs):
        return QueryResponse(
            query=query,
            answer="Escaped\x01answer with zero-width\u200b",
            citations=["Reference\x02"],
            reasoning=["Reasoning\x03 step"],
            metrics={"format": "markdown"},
        )

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator.run_query",
        staticmethod(fake_run_query),
    )
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context["control_tty_result"] = result


@then(
    "the output should be in Markdown with sections `# Answer`, `## Citations`, `## Reasoning`, and `## Metrics`"
)
def check_markdown_output(bdd_context: BehaviorContext):
    result = bdd_context["terminal_result"]
    output = result.stdout
    assert "# Answer" in output
    assert "## Citations" in output
    assert "## Reasoning" in output
    assert "## Metrics" in output
    assert result.stderr == ""


@when(parsers.parse('I run `autoresearch search "{query}" | cat`'))
def run_piped(query, monkeypatch, bdd_context: BehaviorContext, cli_runner):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = cli_runner.invoke(cli_app, ["search", query])
    bdd_context["piped_result"] = result


@then(
    "the output should be valid JSON with keys `answer`, `citations`, `reasoning`, and `metrics`"
)
def check_json_output(bdd_context: BehaviorContext):
    result = bdd_context["piped_result"]
    output = result.stdout
    data = json.loads(output)
    assert "answer" in data
    assert "citations" in data
    assert "reasoning" in data
    assert "metrics" in data
    assert result.stderr == ""


@when(parsers.re(r'I run `autoresearch search "(?P<query>.+)" --output json`'))
def run_with_json_flag(query, monkeypatch, bdd_context: BehaviorContext, cli_runner):
    result = cli_runner.invoke(cli_app, ["search", query, "--output", "json"])
    bdd_context["json_flag_result"] = result


@then("the output should be valid JSON regardless of terminal context")
def check_json_output_with_flag(bdd_context: BehaviorContext):
    result = bdd_context["json_flag_result"]
    output = result.stdout
    data = json.loads(output)
    assert "answer" in data
    assert "citations" in data
    assert "reasoning" in data
    assert "metrics" in data
    assert result.stderr == ""


@when(parsers.re(r'I run `autoresearch search "(?P<query>.+)" --output markdown`'))
def run_with_markdown_flag(query, monkeypatch, bdd_context: BehaviorContext, cli_runner):
    result = cli_runner.invoke(cli_app, ["search", query, "--output", "markdown"])
    bdd_context["markdown_flag_result"] = result


@then("the output should be Markdown-formatted as in TTY mode")
def check_markdown_output_with_flag(bdd_context: BehaviorContext):
    result = bdd_context["markdown_flag_result"]
    output = result.stdout
    assert "# Answer" in output
    assert "## Citations" in output
    assert "## Reasoning" in output
    assert "## Metrics" in output
    assert result.stderr == ""


@when("I format a response containing control characters as markdown")
def format_response_with_control_characters(bdd_context: BehaviorContext):
    answer = "Escaped\x01answer\u200b"
    citations = ["Reference\x02", "   "]
    reasoning = ["Reasoning\x03", "\u200bmarker"]
    response = QueryResponse(
        answer=answer,
        citations=citations,
        reasoning=reasoning,
        metrics={},
    )
    markdown = OutputFormatter.render(response, "markdown")
    bdd_context["control_markdown"] = markdown


@then("the markdown output should fence escaped control sequences")
def check_control_markdown(bdd_context: BehaviorContext):
    markdown = bdd_context["control_markdown"]

    assert markdown.count("```text") >= 3
    for raw in ("\x01", "\x02", "\x03", "\u200b"):
        assert raw not in markdown
    for escaped in ("\\u0001", "\\u0002", "\\u0003", "\\u200b", "\\u0020\\u0020\\u0020"):
        assert escaped in markdown

    answer_section = markdown.split("## Answer", 1)[1]
    assert "```text" in answer_section.split("##", 1)[0]


@then("the CLI markdown output should include escaped control sequences")
def check_cli_control_output(bdd_context: BehaviorContext):
    result = bdd_context["control_tty_result"]
    output = result.stdout

    assert result.exit_code == 0
    assert "# Answer" in output
    assert "```text" in output

    for raw in ("\x01", "\x02", "\x03", "\u200b"):
        assert raw not in output
    for escaped in ("\\u0001", "\\u0002", "\\u0003", "\\u200b"):
        assert escaped in output

    answer_section = output.split("# Answer", 1)[1].split("##", 1)[0]
    assert "```text" in answer_section


@when(parsers.re(r'I run `autoresearch search "(?P<query>.+)" --output graph`'))
def run_with_graph_flag(query, bdd_context: BehaviorContext, cli_runner):
    result = cli_runner.invoke(cli_app, ["search", query, "--output", "graph"])
    bdd_context["graph_flag_result"] = result


@then('the output should include "Knowledge Graph"')
def check_graph_output(bdd_context: BehaviorContext):
    result = bdd_context["graph_flag_result"]
    assert "Knowledge Graph" in result.stdout
    assert result.stderr == ""


@scenario("../features/output_formatting.feature", "Default TTY output")
def test_default_tty_output(bdd_context: BehaviorContext):
    assert bdd_context["terminal_result"].exit_code == 0


@scenario("../features/output_formatting.feature", "Piped output defaults to JSON")
def test_piped_json_output(bdd_context: BehaviorContext):
    assert bdd_context["piped_result"].exit_code == 0


@scenario("../features/output_formatting.feature", "Explicit JSON flag")
def test_explicit_json_flag(bdd_context: BehaviorContext):
    assert bdd_context["json_flag_result"].exit_code == 0


@scenario("../features/output_formatting.feature", "Explicit Markdown flag")
def test_explicit_markdown_flag(bdd_context: BehaviorContext):
    assert bdd_context["markdown_flag_result"].exit_code == 0


@scenario(
    "../features/output_formatting.feature",
    "Markdown escapes control characters",
)
def test_markdown_control_characters(bdd_context: BehaviorContext):
    assert "control_markdown" in bdd_context


@scenario("../features/output_formatting.feature", "Graph output format")
def test_graph_output(bdd_context: BehaviorContext):
    assert bdd_context["graph_flag_result"].exit_code == 0
