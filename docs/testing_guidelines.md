# Testing guidelines

This document provides guidelines for writing tests in the Autoresearch project.
Following these guidelines will ensure consistency, maintainability, and
reliability of the test suite.

For environment setup instructions see [installation](installation.md).

Tests may require optional dependencies. Markers such as `requires_nlp` or
`requires_parsers` map to extras with the same names. `task install` syncs the
`dev-minimal` and `test` extras by default; add groups with `EXTRAS` or set
`AR_EXTRAS` when using the setup script. `task verify` also installs the
`dev-minimal` and `test` extras by default. Include heavy groups such as `nlp`,
`distributed`, `analysis`, or `llm` only when needed:

```bash
EXTRAS="nlp parsers" task install
EXTRAS="analysis distributed" task verify
```

Available extras enable optional features. Heavy groups require explicit flags:

- `test` - full test suite tools (installed by default)
- `nlp` - language processing via spaCy and BERTopic
- `ui` - Streamlit interface
- `vss` - DuckDB vector search extension
- `git` - local Git repository search
- `distributed` - Ray and Redis for distributed processing
- `analysis` - Polars-based analytics
- `llm` - large language model libraries
- `parsers` - PDF and DOCX ingestion
- `gpu` - GPU-accelerated dependencies

## Test Organization

Tests are organized into four categories:

1. **Unit Tests** (`tests/unit/`): Test individual components in isolation
2. **Integration Tests** (`tests/integration/`): Test interactions between
   components
3. **Behavior Tests** (`tests/behavior/`): BDD-style tests using Gherkin syntax
4. **Targeted Tests** (`tests/targeted/`): Temporary tests for specific issues.
   Run them manually and migrate to unit or integration suites once
   validated.

## Running tests

Two installation strategies support different workflows:

- **Minimal:** `task check` runs linting, type checks, and a fast targeted
  subset. It syncs the `dev-minimal` and `test` extras. Add optional features
  with `task install EXTRAS="nlp ui"` choosing from `analysis`, `distributed`,
  `git`, `llm`, `nlp`, `parsers`, `ui`, `vss`, and `gpu`.
- **Full:** `task verify` runs linting, type checks, and coverage. It installs
  the `dev-minimal` and `test` extras by default. Append optional groups with
  `EXTRAS` for integration scenarios.

`task check` offers fast feedback, while `task verify` enforces coverage and is
expected before committing.

If the `task` CLI is unavailable, install the test extras before invoking
`pytest` directly:

```bash
uv pip install -e ".[test]"
uv run pytest -q
```

This ensures required plugins like `pytest-bdd` are installed.

If `pytest` reports missing plugins, ensure the `[test]` extra is installed:

```bash
uv sync --extra test
# or
uv pip install -e '.[test]'
```

Redis is an optional dependency, but tests that interact with it are marked
`requires_distributed`. A lightweight `fakeredis` instance starts automatically
when a real server is unreachable so distributed tests run without external
infrastructure.

Use [Go Task](https://taskfile.dev/#/) to run specific suites inside the
project's virtual environment:

```bash
task test:unit         # unit tests
task test:integration  # integration tests excluding slow tests
task test:behavior     # behavior-driven tests
task test:fast         # unit, integration, and behavior tests (no slow)
task test:slow         # only tests marked as slow
task test:all          # entire suite including slow tests
task verify           # lint, type checks, targeted tests with coverage
task coverage          # full suite with coverage and regression checks
```
Run `task verify` before committing to ensure linting, type checks, and
targeted tests meet the 90% coverage threshold. Use `task coverage` for the
full suite with token regression checks. The threshold is controlled by the
`COVERAGE_THRESHOLD`
variable, set to `90` in the Taskfile and CI workflow. CI stores a baseline
`coverage.xml` in `baseline/coverage.xml` and compares future runs against it
to detect regressions. To perform the comparison locally, run:

```bash
uv run python scripts/check_token_regression.py --coverage-current coverage.xml
```

After tests complete, verify coverage meets the threshold:

```bash
uv run coverage report --fail-under=90
```

After coverage reports are generated, synchronize documentation:

```bash
uv run python scripts/update_coverage_docs.py
```

This writes the percentage to [../STATUS.md](../STATUS.md),
[../TASK_PROGRESS.md](../TASK_PROGRESS.md), and
[release_plan.md](release_plan.md) so all references remain aligned.

The [scripts/simulate_llm_adapter.py](../scripts/simulate_llm_adapter.py)
script models adapter switching and token budgets for exploratory testing:

```bash
uv run python scripts/simulate_llm_adapter.py "example prompt"
```

You can also invoke the slow suite directly with:

```bash
pytest -m slow
```

`task test:fast` usually finishes in about **3 minutes**. The slow tests add
roughly **7 minutes**, so `task test:all` takes around **10 minutes** total
and is used by CI. Maintain at least **90% coverage**. When running suites
separately, prefix each command with `coverage run -p` and merge the results
using `coverage combine` before generating a report with `coverage html` or
`coverage xml`.

## Naming Conventions

### Test Files

- Test files should be named `test_<module_name>.py`
- For unit tests, the module name should match the module being tested
- For integration tests, the module name should describe the interaction
  being tested
- For behavior tests, step definition files should be named
  `<feature_name>_steps.py`

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

Every test function should have a docstring that explains what it's
testing. The docstring should:

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

Common project fixtures live in `tests/conftest.py`. Use
`example_autoresearch_toml` for a realistic `autoresearch.toml` and
`example_env_file` for a sample `.env` with required variables.
`ensure_duckdb_schema` invokes `StorageManager.setup` so tests that touch
storage start with a fresh DuckDB database. The setup routine automatically
creates any missing tables.

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

Use `task coverage` to run the full suite with coverage and enforce the
90% threshold. The command also invokes
`scripts/check_token_regression.py` to detect token usage regressions.
CI compares `coverage.xml` against a cached baseline so any drop in
coverage is caught. For a quicker pre-commit check run `task verify`,
which executes a reduced suite with coverage and the same regression
guard. If legitimate changes exceed the token threshold, update
`tests/integration/baselines/token_usage.json` and commit the new
baseline.

## Template

A template for unit tests is available at `tests/unit/test_template.py`. Use
this template as a starting point for new test files.

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
    
    with patch.object(StorageManager.context, 'graph', mock_graph):
        with patch.object(StorageManager.state, 'lru', {}):
            # Execute
            StorageManager.persist_claim(claim)
            
            # Verify
              mock_graph.add_node.assert_called_once_with(
                  "claim1", confidence=0.8
              )
              mock_graph.add_edge.assert_called_once_with(
                  "claim1", "claim2"
              )
```

## Behavior-Driven Tests

Behavior tests in `tests/behavior/` use **pytest-bdd**. Steps share
state via the `bdd_context` fixture and scenarios end with assertions
that validate this context. When writing scenario functions:

The base directory for feature files is set in `pytest.ini`:

```ini
bdd_features_base_dir = tests/behavior/features
```

Run behavior tests from the repository root so this path resolves correctly.
`task behavior` and `uv run pytest --rootdir=. tests/behavior -q` both
respect the configured base directory.

The `pytest-bdd` plugin is provided through the `.[test]` extra, loaded via
``-p pytest_bdd`` in ``pytest.ini``, and registered in
``tests/behavior/__init__.py``. ``tests/behavior/conftest.py`` also configures
``bdd_features_base_dir`` so paths like
``tests/behavior/features/<feature>.feature`` resolve when invoked directly.

``tests/behavior/features/__init__.py`` marks the directory as a package so
pytest can discover scenarios when feature files are targeted by path.

To execute a single feature file, run from the repository root:

```
uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q
```

The `tests/behavior/features/conftest.py` path hook ensures step definitions
load correctly in this mode.

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

The default install (`uv pip install -e '.[full,parsers,git,llm,dev]'`)
provides all core dependencies, but the full test suite uses several
features that rely on additional extras:

- `ui` – required for Streamlit GUI tests in
  `tests/integration/test_streamlit_gui.py`.
- `analysis` – enables Polars-based utilities tested in
  `tests/unit/test_kuzu_polars.py`.
- `vss` – loads the DuckDB vector extension used by
  `tests/integration/test_vector_extension_extended.py` and
  `tests/integration/test_knn_benchmark.py`.
- `distributed` – installs Ray and Redis so distributed integration tests run
  against real services instead of the lightweight stub in
  `tests/conftest.py`.

If these extras are missing the corresponding tests are skipped (or run
with a stub in the case of the `distributed` extra). Install them with
`uv pip install -e '.[full,parsers,git,llm,dev,ui,analysis,vss,distributed]'`
to run every test.

### Distributed tests

Install the extra and run the marked scenarios directly:

```bash
uv pip install -e '.[distributed]'
uv run pytest -m requires_distributed -q
```

`tests/conftest.py` starts a lightweight Redis service using `fakeredis` when a
real server is not reachable. The `redis_client` fixture connects to this
service so distributed tests run without external infrastructure. Install
`fakeredis` if you do not have a server running. Tests marked
`requires_distributed` are skipped when neither a real Redis server nor
`fakeredis` is available. For local development you can start a Redis container
with:

```bash
uv pip install fakeredis
docker-compose up -d redis
```

## Required services and data

- Network calls are mocked via `pytest-httpx`; install it if missing.
- Config tests write temporary files and require `tomli-w`.
- Baseline JSON files in `tests/integration/baselines/` store expected
  metrics and token counts.
- RDF persistence tests load `owlrl` to apply reasoning rules.
- Some search backends rely on `python-docx` for document parsing.
- No external services are required; all components run in memory.

### Storage fixtures

- Use the `duckdb_path` fixture for storage tests. It invokes
  `StorageManager.initialize_schema()` and yields a clean database path to
  prevent cross-test contamination:

  ```python
  def test_example(duckdb_path):
      storage.setup(duckdb_path)
      ...
  ```

## Updating Baselines

Some integration tests compare runtime metrics against JSON files in
`tests/integration/baselines`. When legitimate changes modify these
metrics (for example token counts), run the failing test to capture the
new values and update the corresponding baseline file. Token-based tests
allow a small overage configurable via the ``TOKEN_USAGE_THRESHOLD``
environment variable.

1. Run the test with
   ``pytest tests/integration/test_token_usage_integration.py``.
2. Inspect the assertion failure to see the updated token counts.
3. Edit ``tests/integration/baselines/token_usage.json`` to match the new
   values and commit the change alongside your code.

Keeping baselines in sync ensures that performance regressions are
intentional and reviewed.

## Conclusion

Following these guidelines will ensure that the test suite is consistent,
maintainable, and reliable. If you have any questions or suggestions,
please open an issue or pull request.
