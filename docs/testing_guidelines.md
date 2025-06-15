# Testing Guidelines for Autoresearch

This document provides guidelines for writing tests in the Autoresearch project. Following these guidelines will ensure consistency, maintainability, and reliability of the test suite.

## Test Organization

Tests are organized into three categories:

1. **Unit Tests** (`tests/unit/`): Test individual components in isolation
2. **Integration Tests** (`tests/integration/`): Test interactions between components
3. **Behavior Tests** (`tests/behavior/`): BDD-style tests using Gherkin syntax

## Naming Conventions

### Test Files

- Test files should be named `test_<module_name>.py`
- For unit tests, the module name should match the module being tested
- For integration tests, the module name should describe the interaction being tested
- For behavior tests, step definition files should be named `<feature_name>_steps.py`

### Test Functions

- Test functions should be named `test_<function_name>_<scenario>`
- The function name should match the function being tested
- The scenario should describe the specific test case
- Examples:
  - `test_persist_claim_valid_input`
  - `test_vector_search_empty_result`
  - `test_execute_agent_error_handling`

## Test Structure

Each test should follow a clear structure:

1. **Setup**: Prepare the test environment, create objects, and set up mocks
2. **Execute**: Call the function or method being tested
3. **Verify**: Assert that the expected behavior occurred

Use comments to clearly separate these sections:

```python
def test_function_behavior():
    """Test that the function behaves as expected."""
    # Setup
    # ...
    
    # Execute
    # ...
    
    # Verify
    # ...
```

## Docstrings

Every test function should have a docstring that explains what it's testing. The docstring should:

1. Describe the expected behavior, not the implementation
2. Be clear and concise
3. Provide context if necessary

Example:

```python
def test_persist_claim_valid_input():
    """Test that a valid claim is correctly persisted to storage.
    
    This test verifies that when a valid claim is provided, it is:
    1. Validated correctly
    2. Persisted to the graph
    3. Added to the LRU cache
    """
```

## Fixtures

Use fixtures for common setup and teardown to reduce code duplication:

1. Define fixtures in `conftest.py` if they're used across multiple test files
2. Define fixtures in the test file if they're only used in that file
3. Use the `scope` parameter to control the lifetime of the fixture
4. Use the `yield` statement for teardown code

Example:

```python
@pytest.fixture
def mock_storage():
    """Create a mock storage system for testing."""
    # Setup
    mock_graph = MagicMock()
    mock_db = MagicMock()
    
    with patch('autoresearch.storage._graph', mock_graph):
        with patch('autoresearch.storage._db_conn', mock_db):
            yield mock_graph, mock_db
    
    # Teardown (if needed)
```

## Mocking

Use mocking to isolate the code being tested:

1. Use `unittest.mock.patch` for mocking functions and objects
2. Use `unittest.mock.MagicMock` for creating mock objects
3. Use `pytest.monkeypatch` for modifying environment variables and attributes
4. Be specific about what you're mocking to avoid over-mocking

Example:

```python
def test_function_with_mocking():
    """Test function behavior with mocking."""
    # Setup
    with patch('module.function') as mock_function:
        mock_function.return_value = 'mocked value'
        
        # Execute
        result = function_under_test()
        
        # Verify
        assert result == 'expected value'
        mock_function.assert_called_once_with('expected argument')
```

## Parameterization

Use parameterization to test the same functionality with different inputs:

```python
@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("input1", "output1"),
        ("input2", "output2"),
        ("input3", "output3"),
    ],
)
def test_function_with_parameters(input_value, expected_output):
    """Test function behavior with different parameters."""
    # Setup
    
    # Execute
    result = function_under_test(input_value)
    
    # Verify
    assert result == expected_output
```

## Error Handling

Test error handling by verifying both the error type and message:

```python
def test_function_error_handling():
    """Test that the function handles errors properly."""
    # Setup
    
    # Execute and Verify
    with pytest.raises(ValueError) as excinfo:
        function_under_test('invalid input')
    
    # Verify the error message
    assert "Expected error message" in str(excinfo.value)
```

## Test Isolation

Ensure that tests are isolated from each other:

1. Don't rely on the state from other tests
2. Clean up any side effects in teardown code
3. Use fixtures with appropriate scopes
4. Reset global state before and after tests

## Test Coverage

Aim for high test coverage:

1. Test all public methods and functions
2. Test edge cases and error conditions
3. Use parameterization to test multiple inputs
4. Test both positive and negative scenarios

## Template

A template for unit tests is available at `tests/unit/test_template.py`. Use this template as a starting point for new test files.

## Example

Here's a complete example of a well-structured test:

```python
import pytest
from unittest.mock import patch, MagicMock
from autoresearch.storage import StorageManager

@pytest.fixture
def mock_graph():
    """Create a mock graph for testing."""
    return MagicMock()

def test_persist_claim_valid_input(mock_graph):
    """Test that a valid claim is correctly persisted to storage."""
    # Setup
    claim = {
        "id": "claim1",
        "attributes": {"confidence": 0.8},
        "relations": [{"src": "claim1", "dst": "claim2"}]
    }
    
    with patch('autoresearch.storage._graph', mock_graph):
        with patch('autoresearch.storage._lru', {}):
            # Execute
            StorageManager.persist_claim(claim)
            
            # Verify
            mock_graph.add_node.assert_called_once_with("claim1", confidence=0.8)
            mock_graph.add_edge.assert_called_once_with("claim1", "claim2")
```

## Conclusion

Following these guidelines will ensure that the test suite is consistent, maintainable, and reliable. If you have any questions or suggestions, please open an issue or pull request.