# Testing Guidelines for Autoresearch

This document provides guidelines for writing tests in the Autoresearch project. Following these guidelines will ensure consistency, maintainability, and reliability of the test suite.

## Test Organization

Tests are organized into three categories:

1. **Unit Tests** (`tests/unit/`): Test individual components in isolation
2. **Integration Tests** (`tests/integration/`): Test interactions between components
3. **Behavior Tests** (`tests/behavior/`): BDD-style tests using Gherkin syntax

## Running tests

Before running any tests ensure the project is installed with the `ci` extra.
The `scripts/setup.sh` helper installs the heavier `full` and `dev` groups for
development, but CI only requires the lightweight `ci` dependencies along with
any optional extras you wish to exercise.

Use [Go Task](https://taskfile.dev/#/) to run specific suites inside the project's virtual environment:

```bash
task test:unit         # unit tests
task test:integration  # integration tests excluding slow tests
task test:behavior     # behavior-driven tests
task test:fast         # unit, integration, and behavior tests (no slow)
task test:slow         # only tests marked as slow
task test:all          # entire suite including slow tests
```
You can also invoke the slow suite directly with:

```bash
pytest -m slow
```

`task test:fast` usually finishes in about **3 minutes**. The slow tests add roughly **7 minutes**, so `task test:all` takes around **10 minutes** total and is used by CI. Maintain at least **90% coverage**. When running suites separately, prefix each command with `coverage run -p` and merge the results using `coverage combine` before generating a report with `coverage html` or `coverage xml`.

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

## Heavy Dependency Mocking

Some optional libraries, such as `bertopic` and Hugging Face `transformers`,
can trigger large downloads when imported. Tests mock these modules in
`tests/conftest.py` to keep execution lightweight:

```python
sys.modules.setdefault("bertopic", MagicMock())
sys.modules.setdefault("transformers", MagicMock())
```

If a test requires functionality from these packages, provide more specific
mocks within the test itself. This approach ensures the unit suite runs without
attempting to download heavy models.

## DuckDB VSS extension during tests

The storage backend uses DuckDB's VSS extension for vector search. To keep the
test suite self-contained the `tests/conftest.py` fixtures provide a stubbed
`VECTOR_EXTENSION_PATH` when this environment variable is not already set. The
fixtures also mock the `VSSExtensionLoader` so no network downloads occur and
the extension appears to be loaded. When a test needs the real extension, mark
it with `@pytest.mark.real_vss` or set the `REAL_VSS_TEST` environment
variable.

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

## Behavior-Driven Tests

Behavior tests in `tests/behavior/` use **pytest-bdd**. Steps share
state via the `bdd_context` fixture and scenarios end with assertions
that validate this context. When writing scenario functions:

* Use `@scenario` to map a Gherkin scenario to the test.
* Accept `bdd_context` (and other fixtures if needed) and assert that
  steps populated expected values.
* Capture CLI or GUI logs with `caplog` to verify accessibility or
  logging output.

Behavior step files can access preconfigured clients using two fixtures:
`cli_client` provides a `CliRunner` for invoking the Typer CLI and
`api_client` yields a `TestClient` connected to the FastAPI app. Use
these fixtures instead of instantiating new clients within step functions.

This pattern keeps the feature files expressive while ensuring the
Python tests make concrete assertions about CLI behaviour, GUI
accessibility, and log messages.

## Optional extras for tests

The minimal CI install (`uv pip install -e '.[dev-minimal]'`) does not
include all optional extras. The full test suite uses several features
that rely on these extras:

- `ui` – required for Streamlit GUI tests in
  `tests/integration/test_streamlit_gui.py`.
- `analysis` – enables Polars-based utilities tested in
  `tests/unit/test_kuzu_polars.py`.
- `vss` – loads the DuckDB vector extension used by
  `tests/integration/test_vector_extension_extended.py` and
  `tests/integration/test_knn_benchmark.py`.
- `distributed` – installs Ray so that the distributed integration tests
  exercise real processes instead of the lightweight stub in
  `tests/conftest.py`.

If these extras are missing the corresponding tests are skipped (or run
with a stub in the case of the `distributed` extra). Install them with
`uv pip install --extras "ui,analysis,vss,distributed"` to run
every test.

## Updating Baselines

Some integration tests compare runtime metrics against JSON files in
`tests/integration/baselines`. When legitimate changes modify these
metrics (for example token counts), run the failing test to capture the
new values and update the corresponding baseline file.

1. Run the test with `pytest tests/integration/test_token_usage.py`.
2. Inspect the assertion failure to see the updated token counts.
3. Edit the JSON baseline file to match the new values and commit the
   change alongside your code.

Keeping baselines in sync ensures that performance regressions are
intentional and reviewed.

## Conclusion

Following these guidelines will ensure that the test suite is consistent, maintainable, and reliable. If you have any questions or suggestions, please open an issue or pull request.
