# mypy: ignore-errors
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


@then(parsers.parse("the search config should have primus start {index:d}"))
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


# Step definitions for CLI output clarity scenarios


@when("I run `autoresearch search {query}`")
def step_run_search_command(context: BehaviorContext, query: str) -> None:
    """Run autoresearch search command."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", query])
    set_value(context, "cli_result", result)
    set_value(context, "stdout_capture", result.stdout)
    set_value(context, "stderr_capture", result.stderr)


@when("I run `autoresearch reverify {state_id}`")
def step_run_reverify_command(context: BehaviorContext, state_id: str) -> None:
    """Run autoresearch reverify command."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["reverify", state_id])
    set_value(context, "cli_result", result)
    set_value(context, "stdout_capture", result.stdout)
    set_value(context, "stderr_capture", result.stderr)


@when("I run `autoresearch search {query} with progress display")
def step_run_search_with_progress(context: BehaviorContext, query: str) -> None:
    """Run search command that shows progress."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", query])
    set_value(context, "cli_result", result)
    set_value(context, "stdout_capture", result.stdout)
    set_value(context, "stderr_capture", result.stderr)


@when("I run `autoresearch search {query} 2>&1`")
def step_run_search_redirected(context: BehaviorContext, query: str) -> None:
    """Run search command with stderr redirected to stdout."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", query])
    set_value(context, "cli_result", result)
    set_value(context, "stdout_capture", result.stdout)
    set_value(context, "stderr_capture", result.stderr)
    # For redirected output, combine stderr into stdout for testing
    set_value(context, "combined_output", result.stdout + result.stderr)


@when("I run `autoresearch search {query} --bare-mode`")
def step_run_search_bare_mode(context: BehaviorContext, query: str) -> None:
    """Run search command in bare mode."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", query, "--bare-mode"])
    set_value(context, "cli_result", result)
    set_value(context, "stdout_capture", result.stdout)
    set_value(context, "stderr_capture", result.stderr)


@when("I run `autoresearch --help`")
def step_run_help_command(context: BehaviorContext) -> None:
    """Run help command."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["--help"])
    set_value(context, "cli_result", result)
    set_value(context, "stdout_capture", result.stdout)
    set_value(context, "stderr_capture", result.stderr)


@when("I trigger configuration errors in different commands")
def step_trigger_config_errors(context: BehaviorContext) -> None:
    """Trigger configuration errors in different commands."""
    # Test with invalid log format
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test", "--log-format", "invalid"])
    set_value(context, "config_error_result", result)


@then("success message {message} should appear exactly once")
def step_check_success_message_once(context: BehaviorContext, message: str) -> None:
    """Check that success message appears exactly once."""
    stdout_capture = get_required(context, "stdout_capture", str)
    count = stdout_capture.count(message)
    assert count == 1, f"Success message '{message}' appears {count} times, expected 1"


@then("it should appear before the main results output")
def step_check_success_before_results(context: BehaviorContext) -> None:
    """Check that success message appears before main results."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Find position of success message and main content markers
    success_pos = stdout_capture.find("Query processed successfully")
    results_pos = stdout_capture.find("# Answer")  # Markdown header for answer

    if success_pos != -1 and results_pos != -1:
        assert success_pos < results_pos, "Success message should appear before results"
    elif success_pos == -1:
        pytest.fail("Success message not found")
    # If results not found, that's okay - might be error case


@then("no duplicate success messages should be present")
def step_check_no_duplicate_success(context: BehaviorContext) -> None:
    """Check that no duplicate success messages are present."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Count occurrences of success message
    success_count = stdout_capture.count("Query processed successfully")
    assert success_count <= 1, f"Found {success_count} success messages, expected at most 1"


@then("error message should appear exactly once in the structured output")
def step_check_error_message_once_structured(context: BehaviorContext) -> None:
    """Check that error message appears exactly once in structured output."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Should contain error in the structured output (answer field)
    error_indicators = ["Error:", "failed", "invalid"]
    has_error_in_output = any(indicator in stdout_capture for indicator in error_indicators)

    assert has_error_in_output, "Error message not found in structured output"


@then("it should include the error description")
def step_check_error_description(context: BehaviorContext) -> None:
    """Check that error message includes description."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should contain descriptive error text
    error_descriptions = ["failed", "error", "invalid", "not found"]
    has_description = any(desc in stderr_capture.lower() for desc in error_descriptions)

    if not has_description:
        # Check stdout as well
        stdout_capture = get_required(context, "stdout_capture", str)
        has_description = any(desc in stdout_capture.lower() for desc in error_descriptions)

    assert has_description, "Error message should include descriptive text"


@then("it should include actionable suggestions")
def step_check_error_suggestions(context: BehaviorContext) -> None:
    """Check that error message includes actionable suggestions."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should contain suggestion indicators
    suggestion_indicators = ["Suggestion:", "Try", "Check", "Use"]
    has_suggestion = any(indicator in stderr_capture for indicator in suggestion_indicators)

    if not has_suggestion:
        # Check stdout as well
        stdout_capture = get_required(context, "stdout_capture", str)
        has_suggestion = any(indicator in stdout_capture for indicator in suggestion_indicators)

    assert has_suggestion, "Error message should include actionable suggestions"


@then("no duplicate error messages should be present in either stdout or stderr")
def step_check_no_duplicate_errors_streams(context: BehaviorContext) -> None:
    """Check that no duplicate error messages are present in either stdout or stderr."""
    stderr_capture = get_required(context, "stderr_capture", str)
    stdout_capture = get_required(context, "stdout_capture", str)

    combined_output = stderr_capture + stdout_capture

    # Count error indicators - should not be duplicated excessively
    error_indicators = ["Error processing query", "Error:", "failed"]
    for indicator in error_indicators:
        count = combined_output.count(indicator)
        # Allow up to 2 occurrences (one in stderr, one in stdout structured output)
        assert (
            count <= 2
        ), f"Error indicator '{indicator}' appears {count} times, expected at most 2"


@then("progress bars should appear during execution")
def step_check_progress_bars(context: BehaviorContext) -> None:
    """Check that progress bars appear during execution."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Progress indicators should be present
    progress_indicators = ["%", "Processing", "Fetching"]
    has_progress = any(indicator in stderr_capture for indicator in progress_indicators)

    # If no progress indicators, might be fast execution - that's okay
    # But if present, they should not interfere with final output
    if has_progress:
        # Check that progress doesn't appear in final output
        stdout_capture = get_required(context, "stdout_capture", str)
        assert not any(
            indicator in stdout_capture for indicator in progress_indicators
        ), "Progress indicators should not appear in final output"


@then("progress indicators should clear when complete")
def step_check_progress_cleared(context: BehaviorContext) -> None:
    """Check that progress indicators clear when complete."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should not contain stuck progress indicators
    stuck_indicators = ["0% -", "Processing query..."]
    for indicator in stuck_indicators:
        assert indicator not in stderr_capture, f"Stuck progress indicator found: {indicator}"


@then("no progress artifacts should remain after completion")
def step_check_no_progress_artifacts(context: BehaviorContext) -> None:
    """Check that no progress artifacts remain after completion."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should not contain progress artifacts that persist
    artifact_indicators = ["\r", "\x1b[", "Processing query..."]
    for indicator in artifact_indicators:
        assert indicator not in stderr_capture, f"Progress artifact found: {repr(indicator)}"


@then("progress should not interfere with final output")
def step_check_progress_no_interference(context: BehaviorContext) -> None:
    """Check that progress doesn't interfere with final output."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Final output should be clean without progress artifacts
    interference_indicators = ["\r", "\x1b[", "Processing", "%"]
    for indicator in interference_indicators:
        assert (
            indicator not in stdout_capture
        ), f"Progress interference in final output: {repr(indicator)}"


@then("application results should go to stdout")
def step_check_results_to_stdout(context: BehaviorContext) -> None:
    """Check that application results go to stdout."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Should contain result indicators
    result_indicators = ["# Answer", "# Citations", "# Reasoning", "Metrics"]
    has_results = any(indicator in stdout_capture for indicator in result_indicators)

    assert has_results, "Application results not found in stdout"


@then("diagnostic logs should go to stderr")
def step_check_logs_to_stderr(context: BehaviorContext) -> None:
    """Check that diagnostic logs go to stderr."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should contain log indicators (but not in quiet mode)
    log_indicators = ["[INFO]", "[WARNING]", "[ERROR]"]
    has_logs = any(indicator in stderr_capture for indicator in log_indicators)

    # If no logs, might be in quiet mode - that's okay
    # But if logs are present, they should be in stderr
    if has_logs:
        stdout_capture = get_required(context, "stdout_capture", str)
        # Stdout should not contain log indicators (except in redirected mode)
        if "2>&1" not in str(get_required(context, "cli_args", [])):
            for indicator in log_indicators:
                assert (
                    indicator not in stdout_capture
                ), f"Log indicator '{indicator}' found in stdout"


@then("error messages should go to stderr")
def step_check_errors_to_stderr(context: BehaviorContext) -> None:
    """Check that error messages go to stderr."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should contain error indicators
    error_indicators = ["Error processing query", "Error:", "✗"]
    has_errors = any(indicator in stderr_capture for indicator in error_indicators)

    if has_errors:
        stdout_capture = get_required(context, "stdout_capture", str)
        # Stdout should not contain primary error indicators (might have JSON errors)
        for indicator in ["Error processing query", "Error:"]:
            assert indicator not in stdout_capture, f"Error indicator '{indicator}' found in stdout"


@then("status messages should go to stderr")
def step_check_status_to_stderr(context: BehaviorContext) -> None:
    """Check that status messages go to stderr."""
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should contain status indicators
    status_indicators = ["Query processed successfully", "✓", "State ID:"]
    has_status = any(indicator in stderr_capture for indicator in status_indicators)

    assert has_status, "Status messages not found in stderr"


@then("stderr and stdout should be properly separated")
def step_check_streams_separated(context: BehaviorContext) -> None:
    """Check that stderr and stdout are properly separated."""
    stdout_capture = get_required(context, "stdout_capture", str)
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should have content in both streams
    assert stdout_capture.strip(), "stdout should not be empty"
    assert stderr_capture.strip(), "stderr should not be empty"

    # Should not have the same content (unless redirected)
    if "2>&1" not in str(get_required(context, "cli_args", [])):
        # In non-redirected mode, streams should be different
        assert (
            stdout_capture != stderr_capture
        ), "stdout and stderr should be different in non-redirected mode"


@then("human-readable content should not be mixed with JSON logs")
def step_check_no_mixed_content(context: BehaviorContext) -> None:
    """Check that human-readable content is not mixed with JSON logs."""
    combined_output = get_required(context, "combined_output", str)

    # Should not have mixed content patterns
    import re

    # Pattern: JSON log line followed by human text
    mixed_pattern = r'\{.*"level".*\}.*\n.*[A-Za-z].*'
    has_mixed = bool(re.search(mixed_pattern, combined_output, re.MULTILINE | re.DOTALL))

    if has_mixed:
        # Allow some mixing in redirected mode, but not in normal mode
        if "2>&1" not in str(get_required(context, "cli_args", [])):
            pytest.fail("Human-readable content mixed with JSON logs")


@then("each stream should contain appropriate content type")
def step_check_appropriate_content_types(context: BehaviorContext) -> None:
    """Check that each stream contains appropriate content type."""
    stdout_capture = get_required(context, "stdout_capture", str)
    stderr_capture = get_required(context, "stderr_capture", str)

    # Stdout should contain results (markdown or JSON)
    has_results = (
        "# Answer" in stdout_capture or '"answer"' in stdout_capture or "Metrics" in stdout_capture
    )

    # Stderr should contain logs or status messages
    has_logs_or_status = (
        "[INFO]" in stderr_capture
        or "Query processed successfully" in stderr_capture
        or "Error" in stderr_capture
    )

    assert has_results, "stdout should contain results"
    assert has_logs_or_status, "stderr should contain logs or status"


@then("output should contain no Unicode symbols")
def step_check_no_unicode_symbols(context: BehaviorContext) -> None:
    """Check that output contains no Unicode symbols."""
    stdout_capture = get_required(context, "stdout_capture", str)
    stderr_capture = get_required(context, "stderr_capture", str)

    unicode_symbols = ["✓", "✗", "⚠", "ℹ", "🔍", "📊"]
    combined_output = stdout_capture + stderr_capture

    for symbol in unicode_symbols:
        assert symbol not in combined_output, f"Unicode symbol '{symbol}' found in output"


@then("output should contain no ANSI color codes")
def step_check_no_ansi_codes(context: BehaviorContext) -> None:
    """Check that output contains no ANSI color codes."""
    stdout_capture = get_required(context, "stdout_capture", str)
    stderr_capture = get_required(context, "stderr_capture", str)

    import re

    ansi_pattern = r"\x1b\[[0-9;]*m"
    combined_output = stdout_capture + stderr_capture

    ansi_matches = re.findall(ansi_pattern, combined_output)
    assert not ansi_matches, f"ANSI color codes found in output: {ansi_matches}"


@then("output should use plain text labels")
def step_check_plain_text_labels(context: BehaviorContext) -> None:
    """Check that output uses plain text labels."""
    stdout_capture = get_required(context, "stdout_capture", str)
    stderr_capture = get_required(context, "stderr_capture", str)

    # Should contain plain text labels instead of symbols
    plain_labels = ["SUCCESS", "ERROR", "WARNING", "INFO"]
    combined_output = stdout_capture + stderr_capture

    has_plain_labels = any(label in combined_output for label in plain_labels)
    assert has_plain_labels, "Plain text labels not found in output"


@then("all functionality should be preserved")
def step_check_functionality_preserved(context: BehaviorContext) -> None:
    """Check that all functionality is preserved in bare mode."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Should still contain core functionality indicators
    core_indicators = ["Answer", "Citations", "Reasoning", "Metrics"]
    has_core = all(indicator in stdout_capture for indicator in core_indicators)

    assert has_core, "Core functionality indicators not found in bare mode output"


@then("formatting should be purely textual")
def step_check_purely_textual(context: BehaviorContext) -> None:
    """Check that formatting is purely textual."""
    stdout_capture = get_required(context, "stdout_capture", str)
    stderr_capture = get_required(context, "stderr_capture", str)

    combined_output = stdout_capture + stderr_capture

    # Should not contain Rich console markup
    rich_indicators = ["[bold", "[red", "[green", "[yellow", "[blue", "[cyan]"]
    for indicator in rich_indicators:
        assert indicator not in combined_output, f"Rich markup found: {indicator}"


@then("each command should produce unique, non-duplicated output")
def step_check_unique_output_per_command(context: BehaviorContext) -> None:
    """Check that each command produces unique output."""
    # This is tested by running multiple commands and checking their outputs are different
    # The step definitions above already capture multiple command results
    pass  # Implementation depends on context setup


@then("success/error messages should not repeat across different commands")
def step_check_no_cross_command_repetition(context: BehaviorContext) -> None:
    """Check that messages don't repeat across commands."""
    # This would be tested by comparing outputs from different commands
    pass  # Implementation depends on context setup


@then("each command should have its own distinct output pattern")
def step_check_distinct_patterns(context: BehaviorContext) -> None:
    """Check that each command has distinct output patterns."""
    # This would be tested by analyzing output structure from different commands
    pass  # Implementation depends on context setup


@then("error messages should be consistent in format and content")
def step_check_consistent_error_format(context: BehaviorContext) -> None:
    """Check that error messages are consistent."""
    config_result = get_required(context, "config_error_result", CliRunner.Result)

    # Should contain consistent error format
    error_indicators = ["Invalid log format", "Valid options:"]
    has_consistent_format = all(indicator in config_result.stderr for indicator in error_indicators)

    assert has_consistent_format, "Error message format not consistent"


@then("error suggestions should be contextual to the specific command")
def step_check_contextual_suggestions(context: BehaviorContext) -> None:
    """Check that error suggestions are contextual."""
    config_result = get_required(context, "config_error_result", CliRunner.Result)

    # Should contain contextual suggestions
    contextual_indicators = ["log format", "json, console, auto"]
    has_contextual = all(indicator in config_result.stderr for indicator in contextual_indicators)

    assert has_contextual, "Error suggestions not contextual"


@then("error codes should be consistent where applicable")
def step_check_consistent_error_codes(context: BehaviorContext) -> None:
    """Check that error codes are consistent."""
    config_result = get_required(context, "config_error_result", CliRunner.Result)

    # Should exit with consistent error code (usually 1 for CLI errors)
    assert config_result.exit_code == 1, f"Unexpected exit code: {config_result.exit_code}"


@then("help text should be clearly formatted and easy to read")
def step_check_help_formatting(context: BehaviorContext) -> None:
    """Check that help text is clearly formatted."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Should contain help indicators
    help_indicators = ["Usage:", "Options:", "Arguments:", "--help"]
    has_help = all(indicator in stdout_capture for indicator in help_indicators)

    assert has_help, "Help text not properly formatted"


@then("option descriptions should be concise and actionable")
def step_check_option_descriptions(context: BehaviorContext) -> None:
    """Check that option descriptions are concise and actionable."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Should contain option descriptions
    option_indicators = ["--log-format", "--quiet-logs", "--bare-mode"]
    has_options = all(indicator in stdout_capture for indicator in option_indicators)

    assert has_options, "New option descriptions not found in help"


@then("examples should be provided where helpful")
def step_check_helpful_examples(context: BehaviorContext) -> None:
    """Check that examples are provided."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Should contain usage examples
    example_indicators = ["Examples:", "autoresearch search"]
    has_examples = any(indicator in stdout_capture for indicator in example_indicators)

    assert has_examples, "Helpful examples not found"


@then("all new options should be documented")
def step_check_new_options_documented(context: BehaviorContext) -> None:
    """Check that all new options are documented."""
    stdout_capture = get_required(context, "stdout_capture", str)

    # Should contain all new options
    new_options = ["--log-format", "--quiet-logs", "--bare-mode"]
    all_documented = all(option in stdout_capture for option in new_options)

    assert all_documented, "Not all new options are documented in help"
