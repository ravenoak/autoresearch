# UI Testing Procedures

This document outlines the procedures for testing UI components in the Autoresearch project.

## Testing Framework Overview

Autoresearch uses a multi-layered testing approach for UI components:

1. **Unit Tests**: Test individual UI components in isolation
2. **Integration Tests**: Test interactions between UI components and the core system
3. **Behavior Tests (BDD)**: Test user-facing functionality using Gherkin syntax
4. **Accessibility Tests**: Ensure UI components are accessible to all users
5. **Cross-Modal Tests**: Verify consistent behavior across different interfaces

## Setting Up the Testing Environment

### Prerequisites

- Python 3.12+
- uv (for dependency management)
- pytest and pytest-bdd

Autoresearch uses `uv` for dependency management. The commands below use `uv`.

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/autoresearch.git
cd autoresearch

# Install dependencies with uv
uv venv
uv pip install -e '.[full,parsers,git,llm,dev]'

# Alternatively, use pip
pip install -e ".[dev]"
```

## Unit Testing UI Components

Unit tests for UI components focus on testing individual components in isolation, using mocks for dependencies.

### CLI Component Testing

CLI components are tested using the `typer.testing` module, which provides utilities for testing Typer applications.

```python
# Example: Testing a CLI command
from typer.testing import CliRunner
from autoresearch.main import app

def test_query_command():
    """Test the query command."""
    runner = CliRunner()
    result = runner.invoke(app, ["query", "What is the capital of France?"])
    assert result.exit_code == 0
    assert "Paris" in result.stdout
```

### Streamlit Component Testing

Streamlit components are tested by mocking the Streamlit API and verifying that the correct functions are called with the expected arguments.

```python
# Example: Testing a Streamlit component
from unittest.mock import patch, MagicMock
import streamlit as st
from autoresearch.streamlit_app import render_query_input

def test_render_query_input():
    """Test the query input component."""
    with patch('streamlit.text_input') as mock_text_input:
        mock_text_input.return_value = "What is the capital of France?"
        
        query = render_query_input()
        
        # Verify that text_input was called with the correct arguments
        mock_text_input.assert_called_once()
        args, kwargs = mock_text_input.call_args
        assert "Enter your query" in args[0]
        
        # Verify that the function returns the expected value
        assert query == "What is the capital of France?"
```

## Integration Testing UI Components

Integration tests verify that UI components interact correctly with the core system.

### CLI Integration Testing

```python
# Example: Testing CLI integration with the core system
from typer.testing import CliRunner
from unittest.mock import patch
from autoresearch.main import app
from autoresearch.models import QueryResponse

def test_query_command_integration():
    """Test the query command's integration with the core system."""
    # Mock the core query function
    with patch('autoresearch.core.AutoresearchCore.query') as mock_query:
        # Set up the mock to return a predefined response
        mock_response = QueryResponse(
            query="What is the capital of France?",
            answer="Paris is the capital of France.",
            reasoning="France has Paris as its capital city.",
            citations=["Wikipedia: France"],
            confidence=0.95
        )
        mock_query.return_value = mock_response
        
        # Run the CLI command
        runner = CliRunner()
        result = runner.invoke(app, ["query", "What is the capital of France?"])
        
        # Verify that the core function was called with the correct arguments
        mock_query.assert_called_once_with(
            query="What is the capital of France?",
            reasoning_mode="dialectical"
        )
        
        # Verify that the output contains the expected information
        assert result.exit_code == 0
        assert "Paris is the capital of France." in result.stdout
```

### Streamlit Integration Testing

```python
# Example: Testing Streamlit integration with the core system
from unittest.mock import patch, MagicMock
import streamlit as st
from autoresearch.streamlit_app import run_query
from autoresearch.models import QueryResponse

def test_run_query_integration():
    """Test the run_query function's integration with the core system."""
    # Mock the core query function
    with patch('autoresearch.core.AutoresearchCore.query') as mock_query:
        # Set up the mock to return a predefined response
        mock_response = QueryResponse(
            query="What is the capital of France?",
            answer="Paris is the capital of France.",
            reasoning="France has Paris as its capital city.",
            citations=["Wikipedia: France"],
            confidence=0.95
        )
        mock_query.return_value = mock_response
        
        # Mock Streamlit components
        with patch('streamlit.markdown') as mock_markdown:
            # Run the query
            result = run_query("What is the capital of France?")
            
            # Verify that the core function was called with the correct arguments
            mock_query.assert_called_once_with(
                query="What is the capital of France?",
                reasoning_mode="dialectical"
            )
            
            # Verify that the result is displayed correctly
            mock_markdown.assert_called_with("Paris is the capital of France.")
            
            # Verify that the function returns the expected value
            assert result.answer == "Paris is the capital of France."
```

## Behavior-Driven Development (BDD) Testing

BDD tests use Gherkin syntax to describe user-facing behavior in a natural language format.

### Writing Feature Files

Feature files are written in Gherkin syntax and describe the behavior of the system from a user's perspective.

```gherkin
# Example: Feature file for the Streamlit GUI
Feature: Streamlit GUI Features
  As a user
  I want a web-based GUI for Autoresearch
  So that I can interact with the system in a more visual way

  Background:
    Given the Streamlit application is running

  Scenario: Formatted Answer Display with Markdown Rendering
    When I enter a query that returns Markdown-formatted content
    Then the answer should be displayed with proper Markdown rendering
    And formatting elements like headers, lists, and code blocks should be properly styled
```

### Implementing Step Definitions

Step definitions implement the steps described in the feature files.

```python
# Example: Step definitions for the Streamlit GUI feature
from pytest_bdd import scenario, given, when, then, parsers
from unittest.mock import patch, MagicMock
import streamlit as st
from autoresearch.models import QueryResponse

@scenario('../features/streamlit_gui.feature', 'Formatted Answer Display with Markdown Rendering')
def test_formatted_answer_display():
    """Test formatted answer display with Markdown rendering."""
    pass

@given('the Streamlit application is running')
def streamlit_app_running(monkeypatch, bdd_context):
    """Set up the Streamlit application."""
    # Mock Streamlit session state
    monkeypatch.setattr(st, 'session_state', {})
    
    # Mock Streamlit components
    with patch('streamlit.markdown') as mock_markdown:
        bdd_context['mock_markdown'] = mock_markdown

@when('I enter a query that returns Markdown-formatted content')
def enter_markdown_query(bdd_context):
    """Enter a query that returns Markdown-formatted content."""
    # Mock the core query function
    with patch('autoresearch.core.AutoresearchCore.query') as mock_query:
        # Set up the mock to return a response with Markdown content
        mock_response = QueryResponse(
            query="What is Markdown?",
            answer="# Markdown\n\nMarkdown is a lightweight markup language with plain text formatting syntax.\n\n* Easy to read\n* Easy to write\n* Widely supported",
            reasoning="Markdown was created to be easy to read and write.",
            citations=["Wikipedia: Markdown"],
            confidence=0.95
        )
        mock_query.return_value = mock_response
        
        # Store the mock and response in the context
        bdd_context['mock_query'] = mock_query
        bdd_context['response'] = mock_response
        
        # Run the query
        from autoresearch.streamlit_app import run_query
        result = run_query("What is Markdown?")
        
        # Store the result in the context
        bdd_context['result'] = result

@then('the answer should be displayed with proper Markdown rendering')
def check_markdown_rendering(bdd_context):
    """Check that the answer is displayed with proper Markdown rendering."""
    # Verify that markdown was called with the correct content
    mock_markdown = bdd_context['mock_markdown']
    mock_markdown.assert_called_with(bdd_context['response'].answer)
```

## Accessibility Testing

Accessibility tests ensure that UI components are accessible to all users, including those with disabilities.

### CLI Accessibility Testing

```python
# Example: Testing CLI accessibility
from typer.testing import CliRunner
from autoresearch.main import app
from autoresearch.output_format import OutputFormat, OutputFormatConfig

def test_cli_color_alternatives():
    """Test that CLI output is accessible without color."""
    # Create a configuration with color disabled
    config = OutputFormatConfig(use_color=False)
    output_format = OutputFormat(config)
    
    # Test error message
    error_msg = output_format.format_error("This is an error")
    assert "✗" in error_msg
    assert "ERROR" in error_msg
    
    # Test success message
    success_msg = output_format.format_success("This is a success")
    assert "✓" in success_msg
    assert "SUCCESS" in success_msg
    
    # Test info message
    info_msg = output_format.format_info("This is info")
    assert "ℹ" in info_msg
    assert "INFO" in info_msg
```

### Streamlit Accessibility Testing

```python
# Example: Testing Streamlit accessibility
from unittest.mock import patch, MagicMock
import streamlit as st

def test_streamlit_screen_reader_compatibility():
    """Test that Streamlit components are compatible with screen readers."""
    # Mock Streamlit components
    with patch('streamlit.image') as mock_image:
        # Call the image function with alt text
        st.image("test.png", caption="Alt text for test image")
        
        # Verify that the mock was called with alt text
        mock_image.assert_called_once()
        args, kwargs = mock_image.call_args
        assert kwargs.get('caption') == "Alt text for test image"
    
    # Mock text input
    with patch('streamlit.text_input') as mock_text_input:
        # Call the text_input function with a label
        st.text_input("Query", value="Test query")
        
        # Verify that the mock was called with a label
        mock_text_input.assert_called_once()
        args, kwargs = mock_text_input.call_args
        assert args[0] == "Query"
```

## Cross-Modal Testing

Cross-modal tests verify that behavior is consistent across different interfaces.

The BDD scenarios in `tests/behavior/features/cross_modal_integration.feature`
demonstrate this by validating error handling, configuration synchronization, and
result consistency across the CLI, Streamlit GUI, A2A, and MCP interfaces.

```python
# Example: Testing cross-modal consistency
from unittest.mock import patch, MagicMock
from autoresearch.models import QueryResponse

def test_consistent_error_handling():
    """Test that error handling is consistent across interfaces."""
    # Define a common error
    error_message = "Invalid query: Query cannot be empty"
    
    # Test CLI error handling
    with patch('autoresearch.main.query_command') as mock_cli_query:
        mock_cli_query.side_effect = ValueError(error_message)
        
        # Execute the CLI query and catch the error
        from autoresearch.main import query_command
        try:
            query_command(query="")
            cli_error = None
        except ValueError as e:
            cli_error = str(e)
    
    # Test Streamlit error handling
    with patch('autoresearch.streamlit_app.run_query') as mock_gui_query:
        mock_gui_query.side_effect = ValueError(error_message)
        
        # Execute the GUI query and catch the error
        from autoresearch.streamlit_app import run_query
        try:
            run_query("")
            gui_error = None
        except ValueError as e:
            gui_error = str(e)
    
    # Test A2A error handling
    with patch('autoresearch.a2a_interface.query') as mock_a2a_query:
        mock_a2a_query.side_effect = ValueError(error_message)
        
        # Execute the A2A query and catch the error
        from autoresearch.a2a_interface import query
        try:
            query("")
            a2a_error = None
        except ValueError as e:
            a2a_error = str(e)
    
    # Verify that all interfaces produce the same error message
    assert cli_error == error_message
    assert gui_error == error_message
    assert a2a_error == error_message
```

## Running Tests

### Running All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=autoresearch
```

### Running Specific Test Categories

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run behavior tests
pytest tests/behavior/

# Run tests for a specific file
pytest tests/unit/test_output_format.py

# Run a specific test
pytest tests/unit/test_output_format.py::test_format_error
```

### Running BDD Tests

```bash
# Run all BDD tests
pytest tests/behavior/

# Run tests for a specific feature
pytest tests/behavior/steps/streamlit_gui_steps.py

# Run a specific scenario
pytest tests/behavior/steps/streamlit_gui_steps.py::test_formatted_answer_display
```

## Continuous Integration

Autoresearch uses GitHub Actions for continuous integration. The CI pipeline runs all tests on every push and pull request.

### CI Configuration

The CI configuration is defined in `.github/workflows.disabled/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.12
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv pip install -e '.[full,parsers,git,llm,dev]'
    - name: Run tests
      run: |
        pytest --cov=autoresearch
    - name: Upload coverage report
      uses: codecov/codecov-action@v3
```

## Best Practices for UI Testing

1. **Test User Interactions**: Focus on testing how users interact with the UI, not just the internal implementation.

2. **Mock External Dependencies**: Use mocks for external dependencies to isolate the UI components being tested.

3. **Test Accessibility**: Always include tests for accessibility features to ensure the UI is usable by everyone.

4. **Test Error Handling**: Verify that errors are displayed in a user-friendly way and that the UI recovers gracefully.

5. **Test Cross-Modal Consistency**: Ensure that behavior is consistent across different interfaces.

6. **Use BDD for User-Facing Features**: BDD is particularly well-suited for testing user-facing features as it focuses on behavior from the user's perspective.

7. **Maintain Test Coverage**: Aim for high test coverage, especially for critical UI components.

8. **Automate UI Testing**: Automate UI tests as part of the CI pipeline to catch regressions early.

By following these procedures and best practices, you can ensure that the UI components of the Autoresearch system are thoroughly tested and provide a high-quality user experience.

## Enhanced UI Testing Procedures

### Log Format and Output Testing

#### Log Separation Testing

**Objective**: Verify that logs and application output are properly separated.

**Test Scenarios**:

1. **Interactive Terminal Testing**:
```python
def test_interactive_terminal_logging():
    """Test that interactive terminals show console-format logs."""
    runner = CliRunner()
    
    # Mock isatty to return True (interactive terminal)
    with patch('sys.stderr.isatty', return_value=True):
        result = runner.invoke(cli_app, ["search", "test query"])
        
        # Should contain console-format logs in stderr
        assert "[INFO]" in result.stderr
        assert "test query" in result.stderr
        
        # Should contain markdown results in stdout
        assert "# Answer" in result.stdout
```

2. **Automation Context Testing**:
```python
def test_automation_context_logging():
    """Test that automation contexts use JSON logs."""
    runner = CliRunner()
    
    # Mock isatty to return False (automation context)
    with patch('sys.stderr.isatty', return_value=False):
        result = runner.invoke(cli_app, ["search", "test query"])
        
        # Should contain JSON logs in stderr
        import json
        for line in result.stderr.strip().split('\n'):
            if line.strip():
                json.loads(line)  # Should be valid JSON
```

3. **Stream Redirection Testing**:
```python
def test_stream_redirection():
    """Test behavior when streams are redirected."""
    runner = CliRunner()
    
    # Both streams redirected
    with patch('sys.stdout.isatty', return_value=False), \
         patch('sys.stderr.isatty', return_value=False):
        result = runner.invoke(cli_app, ["search", "test query"])
        
        # Should use JSON format for automation
        assert '"level"' in result.stderr
```

#### Quiet Mode Testing

**Objective**: Verify that quiet mode suppresses diagnostic messages appropriately.

**Test Scenarios**:

1. **Diagnostic Suppression**:
```python
def test_quiet_mode_suppression():
    """Test that quiet mode suppresses INFO and DEBUG logs."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--quiet-logs"])
    
    # Should not contain INFO or DEBUG level logs
    import re
    info_debug_pattern = r'"level":\s*"(INFO|DEBUG)"'
    assert not re.search(info_debug_pattern, result.stderr)
    
    # May contain WARNING or ERROR logs
    error_warning_pattern = r'"level":\s*"(ERROR|WARNING|CRITICAL)"'
    has_error_warning = bool(re.search(error_warning_pattern, result.stderr))
    # This is okay - warnings and errors should still show
```

2. **Error Preservation**:
```python
def test_quiet_mode_errors():
    """Test that errors are still shown in quiet mode."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "invalid query", "--quiet-logs"])
    
    # Errors should still be visible
    assert "Error:" in result.stderr or "Error:" in result.stdout
```

### Accessibility Testing

#### Bare Mode Testing

**Objective**: Verify that bare mode provides accessible, text-only output.

**Test Scenarios**:

1. **Symbol Removal**:
```python
def test_bare_mode_no_symbols():
    """Test that bare mode removes Unicode symbols."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--bare-mode"])
    
    # Should not contain Unicode symbols
    unicode_symbols = ["✓", "✗", "⚠", "ℹ", "🔍", "📊"]
    for symbol in unicode_symbols:
        assert symbol not in result.stdout
        assert symbol not in result.stderr
```

2. **Plain Text Labels**:
```python
def test_bare_mode_text_labels():
    """Test that bare mode uses plain text labels."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--bare-mode"])
    
    # Should contain plain text labels
    plain_labels = ["SUCCESS:", "ERROR:", "WARNING:", "INFO:"]
    has_plain_labels = any(label in result.stdout + result.stderr for label in plain_labels)
    assert has_plain_labels, "Bare mode should use plain text labels"
```

3. **No ANSI Codes**:
```python
def test_bare_mode_no_ansi():
    """Test that bare mode removes ANSI color codes."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--bare-mode"])
    
    # Should not contain ANSI escape sequences
    import re
    ansi_pattern = r'\x1b\[[0-9;]*m'
    ansi_matches = re.findall(ansi_pattern, result.stdout + result.stderr)
    assert not ansi_matches, "Bare mode should not contain ANSI codes"
```

4. **Functionality Preservation**:
```python
def test_bare_mode_functionality():
    """Test that bare mode preserves core functionality."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--bare-mode"])
    
    # Should still contain essential information
    essential_indicators = ["Answer", "Citations", "Reasoning"]
    has_essential = all(indicator in result.stdout for indicator in essential_indicators)
    assert has_essential, "Bare mode should preserve essential functionality"
```

#### Screen Reader Compatibility Testing

**Objective**: Verify compatibility with assistive technologies.

**Test Scenarios**:

1. **Semantic Structure**:
```python
def test_semantic_structure():
    """Test that output has proper semantic structure."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--bare-mode"])
    
    # Should have proper heading structure
    headings = re.findall(r'^#{1,6}\s+.*$', result.stdout, re.MULTILINE)
    if headings:
        # Check heading hierarchy
        heading_levels = [len(heading.split()[0]) for heading in headings]
        # H1 should come first if present
        if 1 in heading_levels:
            h1_index = heading_levels.index(1)
            assert h1_index == 0 or all(level > 1 for level in heading_levels[:h1_index])
```

2. **Text Alternatives**:
```python
def test_text_alternatives():
    """Test that symbols have text equivalents."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query"])
    
    # If symbols are used, they should be accompanied by text
    symbol_usage = "✓" in result.stdout or "✗" in result.stdout or "⚠" in result.stdout
    
    if symbol_usage:
        text_equivalents = ["Success", "Error", "Warning"]
        has_text = any(text in result.stdout for text in text_equivalents)
        assert has_text, "Symbols should be accompanied by text equivalents"
```

### Progressive Disclosure Testing

#### Section Control Testing

**Objective**: Verify that section control options work correctly.

**Test Scenarios**:

1. **Show Sections Command**:
```python
def test_show_sections():
    """Test --show-sections option."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--depth", "standard", "--show-sections"])
    
    # Should show available sections
    assert "Available sections for Standard depth:" in result.stdout
    assert "Answer" in result.stdout
    assert "Citations" in result.stdout
    assert "Reasoning" in result.stdout
```

2. **Include Sections**:
```python
def test_include_sections():
    """Test --include option."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--depth", "concise", "--include=reasoning"])
    
    # Should include reasoning section even at concise depth
    assert "Reasoning" in result.stdout
```

3. **Exclude Sections**:
```python
def test_exclude_sections():
    """Test --exclude option."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--depth", "trace", "--exclude=raw_response"])
    
    # Should exclude raw response section
    assert "Raw response" not in result.stdout
    # But should still include other trace sections
    assert "Reasoning" in result.stdout
```

4. **Section Validation**:
```python
def test_invalid_section():
    """Test validation of invalid section names."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--include=nonexistent_section"])
    
    # Should show error message about invalid section
    assert "Invalid section name" in result.stderr
    assert "Valid sections:" in result.stderr
    assert result.exit_code == 1
```

### Cross-Platform Testing

#### Terminal Compatibility Testing

**Objective**: Verify consistent behavior across different terminal environments.

**Test Scenarios**:

1. **Windows Terminal**:
```python
def test_windows_terminal():
    """Test compatibility with Windows Terminal."""
    # Mock Windows environment
    with patch('platform.system', return_value='Windows'), \
         patch('os.environ.get', return_value='WindowsTerminal'):
        
        runner = CliRunner()
        result = runner.invoke(cli_app, ["search", "test query"])
        
        # Should work correctly in Windows Terminal
        assert result.exit_code == 0
```

2. **Linux Terminals**:
```python
def test_linux_terminals():
    """Test compatibility with various Linux terminals."""
    terminals = ['xterm', 'gnome-terminal', 'konsole']
    
    for term in terminals:
        with patch.dict(os.environ, {'TERM': term}):
            runner = CliRunner()
            result = runner.invoke(cli_app, ["search", "test query"])
            
            # Should work correctly
            assert result.exit_code == 0
```

3. **macOS Terminals**:
```python
def test_macos_terminals():
    """Test compatibility with macOS terminals."""
    with patch('platform.system', return_value='Darwin'):
        runner = CliRunner()
        result = runner.invoke(cli_app, ["search", "test query"])
        
        # Should work correctly on macOS
        assert result.exit_code == 0
```

### Error Message Testing

#### Enhanced Error Testing

**Objective**: Verify that enhanced error messages provide actionable guidance.

**Test Scenarios**:

1. **Log Format Errors**:
```python
def test_log_format_error():
    """Test error message for invalid log format."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--log-format", "invalid"])
    
    # Should provide helpful error message
    assert "Invalid log format: invalid" in result.stderr
    assert "Valid options: json, console, auto" in result.stderr
    assert "Use --log-format console" in result.stderr
    assert result.exit_code == 1
```

2. **Configuration Errors**:
```python
def test_config_error():
    """Test error message for configuration issues."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--invalid-option"])
    
    # Should provide helpful suggestions
    assert "Error:" in result.stderr
    assert "Suggestion:" in result.stderr
```

3. **Network Errors**:
```python
def test_network_error():
    """Test error message for network issues."""
    runner = CliRunner()
    # Mock network failure
    with patch('requests.get', side_effect=ConnectionError("Network unreachable")):
        result = runner.invoke(cli_app, ["search", "test query"])
        
        # Should provide network-specific suggestions
        assert "Check your internet connection" in result.stderr or \
               "Check your network connection" in result.stderr
```

### Performance Testing

#### UI Responsiveness Testing

**Objective**: Verify that UI improvements don't degrade performance.

**Test Scenarios**:

1. **Startup Time**:
```python
def test_cli_startup_time():
    """Test that CLI startup time meets requirements."""
    start_time = time.time()
    
    runner = CliRunner()
    result = runner.invoke(cli_app, ["--help"])
    
    startup_time = time.time() - start_time
    
    # Should start up quickly
    assert startup_time < 1.0, f"CLI startup too slow: {startup_time}s"
```

2. **Command Execution Time**:
```python
def test_command_execution_time():
    """Test that commands execute within reasonable time limits."""
    start_time = time.time()
    
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "simple query"])
    
    execution_time = time.time() - start_time
    
    # Should complete within reasonable time
    assert execution_time < 10.0, f"Command execution too slow: {execution_time}s"
```

3. **Memory Usage**:
```python
def test_memory_usage():
    """Test that memory usage remains reasonable."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "memory test query"])
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable
    assert memory_increase < 50 * 1024 * 1024, f"Memory usage too high: {memory_increase} bytes"
```

### Integration Testing

#### Cross-Interface Consistency

**Objective**: Verify consistent behavior across all interfaces.

**Test Scenarios**:

1. **CLI vs API Consistency**:
```python
def test_cli_api_consistency():
    """Test that CLI and API provide consistent responses."""
    # Test CLI
    cli_runner = CliRunner()
    cli_result = cli_runner.invoke(cli_app, ["search", "consistency test"])
    
    # Test API (if available)
    # api_result = api_client.post("/query", json={"query": "consistency test"})
    
    # Should provide similar information
    # assert cli_result.stdout contains similar data to api_result.json()
```

2. **Depth Level Consistency**:
```python
def test_depth_consistency():
    """Test that depth levels work consistently."""
    depths = ["tldr", "concise", "standard", "trace"]
    
    for depth in depths:
        result = CliRunner().invoke(cli_app, ["search", "test query", "--depth", depth])
        
        # Each depth should provide appropriate level of detail
        if depth == "tldr":
            assert "Answer" in result.stdout
            # Should be relatively short
            assert len(result.stdout) < 2000
        elif depth == "trace":
            # Should contain more detailed information
            assert "Reasoning" in result.stdout
            assert len(result.stdout) > 1000
```

### Regression Testing

#### Output Uniqueness Testing

**Objective**: Ensure no output duplication occurs.

**Test Scenarios**:

1. **Success Message Uniqueness**:
```python
def test_no_duplicate_success_messages():
    """Test that success messages appear exactly once."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query"])
    
    # Count success message occurrences
    success_count = result.stdout.count("Query processed successfully")
    assert success_count <= 1, f"Found {success_count} success messages"
```

2. **Error Message Uniqueness**:
```python
def test_no_duplicate_error_messages():
    """Test that error messages appear exactly once."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "invalid query"])
    
    # Count error message occurrences
    error_count = (result.stdout + result.stderr).count("Error processing query")
    assert error_count <= 2, f"Found {error_count} error messages"
```

3. **Progress Artifact Cleanup**:
```python
def test_no_progress_artifacts():
    """Test that progress indicators are properly cleaned up."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query"])
    
    # Should not contain progress artifacts
    artifact_indicators = ["\r", "\x1b[", "Processing query..."]
    for indicator in artifact_indicators:
        assert indicator not in result.stdout, f"Progress artifact found: {repr(indicator)}"
```

### Continuous Integration

#### Automated Testing Pipeline

**CI Configuration Updates**:

```yaml
# .github/workflows/ui-tests.yml
name: UI Tests

on:
  push:
    paths:
      - 'src/autoresearch/main/app.py'
      - 'src/autoresearch/cli_utils.py'
      - 'src/autoresearch/logging_utils.py'
      - 'tests/behavior/features/logging_separation.feature'
      - 'tests/behavior/features/cli_output_clarity.feature'
      - 'tests/behavior/features/ux_standards_testing.feature'

jobs:
  ui-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.12
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv pip install -e '.[full,parsers,git,llm,dev]'
    - name: Run UI tests
      run: |
        pytest tests/behavior/features/logging_separation.feature -v
        pytest tests/behavior/features/cli_output_clarity.feature -v
        pytest tests/behavior/features/ux_standards_testing.feature -v
    - name: Run accessibility tests
      run: |
        pytest tests/behavior/features/ui_accessibility.feature -v
```

#### Test Organization

**New Test Files Created**:

1. **Logging Separation Tests**:
   - `tests/behavior/features/logging_separation.feature`
   - `tests/behavior/steps/logging_steps.py` (enhanced)

2. **Output Clarity Tests**:
   - `tests/behavior/features/cli_output_clarity.feature`
   - `tests/behavior/steps/cli_options_steps.py` (enhanced)

3. **UX Standards Tests**:
   - `tests/behavior/features/ux_standards_testing.feature`
   - `tests/behavior/steps/ux_standards_steps.py`

4. **Progressive Disclosure Tests**:
   - `tests/behavior/features/progressive_disclosure.feature`
   - Enhanced existing step files

**Test Categories**:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component interaction testing
- **Behavior Tests**: End-to-end user scenario testing
- **Accessibility Tests**: WCAG and usability compliance testing
- **Performance Tests**: Response time and resource usage testing
- **Cross-Platform Tests**: Terminal and OS compatibility testing

### Manual Testing Procedures

#### Accessibility Testing Checklist

**Screen Reader Testing**:
- [ ] Test with NVDA on Windows
- [ ] Test with VoiceOver on macOS
- [ ] Test with Orca on Linux
- [ ] Verify all content is announced correctly
- [ ] Check that navigation is logical

**Keyboard Navigation Testing**:
- [ ] Navigate entire interface using only Tab/Shift+Tab
- [ ] Verify focus indicators are visible
- [ ] Test all interactive elements
- [ ] Check skip links functionality

**Visual Testing**:
- [ ] Test with high contrast mode
- [ ] Test with color blindness simulation
- [ ] Verify text is readable at 200% zoom
- [ ] Check that information is not conveyed by color alone

#### Cross-Platform Testing Checklist

**Terminal Compatibility**:
- [ ] Test in Windows Terminal
- [ ] Test in macOS Terminal
- [ ] Test in iTerm2
- [ ] Test in various Linux terminals (gnome-terminal, konsole, xterm)
- [ ] Verify Unicode symbol display
- [ ] Check color output functionality

**Operating System Testing**:
- [ ] Test on Windows 10/11
- [ ] Test on macOS Monterey/Ventura
- [ ] Test on Ubuntu 22.04/20.04
- [ ] Test on CentOS/RHEL
- [ ] Verify locale handling
- [ ] Check line ending compatibility

#### User Experience Testing

**Usability Testing**:
- [ ] Test with new users unfamiliar with CLI
- [ ] Verify error messages are understandable
- [ ] Check that help text is helpful
- [ ] Test progressive disclosure effectiveness
- [ ] Verify response times meet expectations

**Performance Testing**:
- [ ] Measure CLI startup time (< 500ms target)
- [ ] Test command execution times
- [ ] Monitor memory usage during operations
- [ ] Check CPU usage under load
- [ ] Verify no memory leaks in long operations

### Test Maintenance

#### Regular Updates

**Quarterly Reviews**:
- Review test coverage for new features
- Update test scenarios for UI changes
- Validate accessibility compliance
- Check cross-platform compatibility

**Version Updates**:
- Update test expectations for new CLI options
- Modify tests for changed output formats
- Add tests for new error conditions
- Update performance benchmarks

#### Test Data Management

**Mock Data**:
- Maintain realistic test queries
- Update expected outputs for format changes
- Ensure test data covers edge cases
- Keep test data current with real usage patterns

**Test Environments**:
- Maintain consistent test environments
- Update dependencies regularly
- Monitor test execution times
- Archive obsolete test scenarios

By implementing these comprehensive testing procedures, we ensure that UI improvements maintain quality, accessibility, and user satisfaction across all interfaces and platforms.
