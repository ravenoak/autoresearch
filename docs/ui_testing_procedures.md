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

- Python 3.9+
- Poetry (for dependency management)
- pytest and pytest-bdd

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/autoresearch.git
cd autoresearch

# Install dependencies with Poetry
poetry install --with dev

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

The CI configuration is defined in `.github/workflows/test.yml`:

```yaml
name: Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry install --with dev
    - name: Run tests
      run: |
        poetry run pytest --cov=autoresearch
    - name: Upload coverage report
      uses: codecov/codecov-action@v1
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