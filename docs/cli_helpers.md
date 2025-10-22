# CLI testing helpers

When writing CLI tests, avoid real storage initialisation by using the
`dummy_storage` fixture. It registers a minimal `autoresearch.storage` module
and provides a no-op `StorageManager.setup`.

Use the fixture with `pytest.mark.usefixtures("dummy_storage")` at the module
level or by including it as a parameter in individual tests. Import the CLI
entry point only after applying the fixture:

```
import importlib

pytestmark = pytest.mark.usefixtures("dummy_storage")

app = importlib.import_module("autoresearch.main").app
```

This ensures storage calls are isolated and keeps CLI tests fast and
deterministic.

## Backup restore errors

The `backup restore` command reports clearer failures when archives are
missing or corrupted.

- Missing paths show `Invalid backup path: <path> does not exist`.
- Corrupted archives surface `Error restoring backup: Corrupted backup archive`.

Use these messages when asserting restore behaviour in tests.

## Enhanced CLI Interface Features

### Log Format Control

The CLI now provides intelligent log formatting that adapts to your usage context:

**Auto-Detection**: Automatically detects terminal type and usage context:
- **Interactive terminals**: Human-readable console format
- **Automation/redirected**: JSON format for machine parsing

**Manual Control**:
```bash
# Force console format for human readability
autoresearch search "query" --log-format console

# Force JSON format for automation
autoresearch search "query" --log-format json

# Use auto-detection (default)
autoresearch search "query" --log-format auto
```

**Environment Variable**:
```bash
export AUTORESEARCH_LOG_FORMAT=console
autoresearch search "query"  # Uses console format
```

### Quiet Mode

Suppress diagnostic messages while preserving errors and warnings:
```bash
# Only show errors and warnings
autoresearch search "query" --quiet-logs

# Combine with other options
autoresearch search "query" --quiet-logs --depth standard
```

### Bare Mode for Accessibility

Enable simplified output for screen readers and text-only interfaces:
```bash
# Disable colors, symbols, and decorative formatting
autoresearch search "query" --bare-mode
```

**Features**:
- Plain text labels (SUCCESS, ERROR, WARNING, INFO)
- No Unicode symbols
- No ANSI color codes
- Essential functionality preserved
- Screen reader compatible

### Prompt-toolkit Enhancements

Install the `prompt` extra (`uv sync --extra prompt`) to enable rich
interactive prompts backed by prompt-toolkit. When stdin and stdout are TTYs
and bare mode is disabled, prompts gain:

- Persistent per-session history navigated with the arrow keys
- Optional multi-line editing using standard prompt-toolkit shortcuts
- Tab completion seeded from registered agent names, CLI options, and prior
  responses

The wrapper falls back to the baseline `typer.prompt` implementation when
prompt-toolkit is unavailable, the terminal is non-interactive, or bare mode is
enabled. Validators registered via `Prompt.ask(..., validator=...)` run in both
paths so automated scripts and accessibility tooling keep identical behaviour.

### Section-Level Control

Fine-tune which sections appear in your output:

**Show Available Sections**:
```bash
# See what sections are available for a depth level
autoresearch search "query" --depth standard --show-sections
```

**Include Specific Sections**:
```bash
# Include reasoning section even at concise depth
autoresearch search "query" --depth concise --include=reasoning

# Include multiple sections
autoresearch search "query" --include=metrics,reasoning
```

**Exclude Specific Sections**:
```bash
# Exclude raw response at trace depth
autoresearch search "query" --depth trace --exclude=raw_response

# Exclude multiple sections
autoresearch search "query" --exclude=raw_response,citations
```

**Combine Include and Exclude**:
```bash
# Include metrics but exclude citations
autoresearch search "query" --include=metrics --exclude=citations
```

### Output Stream Management

**Clean Separation**:
- **stdout**: Application results and user-facing content
- **stderr**: Diagnostic logs, progress indicators, and status messages
- **No mixing**: Human-readable content never mixed with JSON logs in normal usage

**Automation-Friendly**:
```bash
# JSON logs go to stderr, results to stdout
autoresearch search "query" > results.json

# Capture both streams separately
autoresearch search "query" > results.json 2> logs.json
```

### Error Handling Improvements

All error messages now include:
- **Clear descriptions** of what went wrong
- **Actionable suggestions** for resolution
- **Code examples** showing correct usage
- **Consistent formatting** across all interfaces

**Example**:
```bash
autoresearch search "query" --log-format invalid
# Error: Invalid log format: invalid. Valid options: json, console, auto
# Suggestion: Use --log-format console for human-readable output
# Example: autoresearch search "query" --log-format console
```

## Testing Enhanced Features

### BDD Test Scenarios

The enhanced CLI features are thoroughly tested using BDD scenarios:

**Logging Separation**:
```gherkin
Scenario: Default auto-detection in interactive terminal
  When I run `autoresearch search "test query"` in an interactive terminal
  Then log messages should use console format "[LEVEL] component: message"
  And application results should appear in markdown format without JSON logs
```

**Output Clarity**:
```gherkin
Scenario: Success message appears exactly once before results
  When I run `autoresearch search "test query"`
  Then success message "Query processed successfully" should appear exactly once
  And it should appear before the main results output
  And no duplicate success messages should be present
```

**Accessibility**:
```gherkin
Scenario: Bare mode removes decorative elements
  When I run `autoresearch search "test query" --bare-mode`
  Then output should contain no Unicode symbols (✓, ✗, ⚠, ℹ)
  And output should contain no ANSI color codes
  And output should use plain text labels (SUCCESS, ERROR, WARNING, INFO)
  And all functionality should be preserved
```

**Progressive Disclosure**:
```gherkin
Scenario: Include specific sections in output
  When I run `autoresearch search "test query" --depth concise --include=reasoning`
  Then the output should include the reasoning section
  And the output should still respect the concise depth limits for other sections
  And sections not explicitly included should follow the depth default
```

### Unit Test Helpers

**Mock Terminal Detection**:
```python
def test_interactive_terminal():
    """Test behavior in interactive terminal context."""
    with patch('sys.stderr.isatty', return_value=True):
        runner = CliRunner()
        result = runner.invoke(cli_app, ["search", "test query"])
        # Verify console format logs
        assert "[INFO]" in result.stderr
```

**Mock Automation Context**:
```python
def test_automation_context():
    """Test behavior in automation context."""
    with patch('sys.stderr.isatty', return_value=False):
        runner = CliRunner()
        result = runner.invoke(cli_app, ["search", "test query"])
        # Verify JSON format logs
        import json
        for line in result.stderr.strip().split('\n'):
            if line.strip():
                json.loads(line)  # Should be valid JSON
```

**Mock Bare Mode**:
```python
def test_bare_mode():
    """Test bare mode functionality."""
    with patch.dict(os.environ, {"AUTORESEARCH_BARE_MODE": "true"}):
        runner = CliRunner()
        result = runner.invoke(cli_app, ["search", "test query"])
        # Verify plain text output
        assert "SUCCESS:" in result.stdout
        assert "✓" not in result.stdout
```

### Integration Test Patterns

**Cross-Interface Consistency**:
```python
def test_cli_gui_consistency():
    """Test that CLI and GUI provide consistent responses."""
    # Test CLI
    cli_result = CliRunner().invoke(cli_app, ["search", "consistency test"])
    
    # Test GUI (mocked)
    with patch('streamlit.markdown') as mock_markdown:
        # GUI call
        gui_result = run_gui_query("consistency test")
        
        # Verify consistency
        assert cli_result.stdout contains similar data to gui_result
```

**Error Handling Consistency**:
```python
def test_error_handling_consistency():
    """Test that error handling is consistent across interfaces."""
    error_scenarios = [
        "invalid log format",
        "missing configuration",
        "network failure"
    ]
    
    for scenario in error_scenarios:
        # Test CLI
        cli_result = trigger_cli_error(scenario)
        
        # Test API
        api_result = trigger_api_error(scenario)
        
        # Verify consistent error format and suggestions
        assert cli_result.stderr contains similar error info to api_result
```

## Migration Guide

### From Previous Versions

**New CLI Options**:
- `--log-format`: Control log output format
- `--quiet-logs`: Suppress diagnostic messages
- `--bare-mode`: Enable accessibility mode
- `--show-sections`: Display available sections
- `--include`/`--exclude`: Control section visibility

**Behavioral Changes**:
- Log format auto-detection (may change output format)
- Enhanced error messages (more detailed and actionable)
- Improved output stream separation

**Configuration Updates**:
- No configuration changes required
- All new features work with existing configurations
- Environment variables available for advanced customization

### Backward Compatibility

**Preserved Functionality**:
- All existing CLI commands work unchanged
- Default behavior remains the same (auto-detection)
- No breaking changes to existing APIs
- Existing tests continue to pass

**Deprecation Warnings**:
- No deprecated features
- All changes are additive and backward compatible

## Troubleshooting

### Common Issues

**JSON logs appearing in CLI output**:
- Check that you're using an interactive terminal
- Try: `autoresearch search "query" --log-format console`
- Report if issue persists

**Output appears duplicated**:
- This should not occur with the current implementation
- Report as a bug with specific reproduction steps

**Colors not displaying correctly**:
- Use `--bare-mode` for text-only output
- Check terminal color support
- Try a different terminal emulator

**Section control not working**:
- Verify section names are correct (use `--show-sections` to list)
- Check that depth level supports the requested sections
- Use `--include` for sections not normally shown at that depth

### Getting Help

**Command Help**:
```bash
# Get help for any command
autoresearch search --help
autoresearch --help
```

**Feature Documentation**:
- User Guide: `docs/user_guide.md`
- CLI Helpers: `docs/cli_helpers.md`
- API Reference: `docs/api_reference/`

**Support Channels**:
- GitHub Issues: Bug reports and feature requests
- Documentation: Technical details and examples
- Community: User discussions and questions

The enhanced CLI interface provides powerful new capabilities while maintaining backward compatibility and improving user experience across all usage contexts.
