# Contributing to Autoresearch

Thank you for considering contributing to Autoresearch! This document provides guidelines and instructions to help you contribute effectively to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone. Please be considerate in your communication and respect differing viewpoints and experiences.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see below)
4. Create a new branch for your feature or bugfix
5. Make your changes
6. Submit a pull request

## Development Environment

### Setting Up

1. Create a virtual environment with `uv`:
   ```bash
   uv venv
   ```

2. Install the dependencies and extras:
   ```bash
   uv sync --all-extras
   uv pip install -e .
   ```
   Run `uv lock` whenever `pyproject.toml` changes.

   Some packages such as `hdbscan` require compilation. Make sure GCC, G++, and
   the Python development headers are available before running the command
   above. On Debian/Ubuntu-based systems you can install them with:

   ```bash
   sudo apt-get update
   sudo apt-get install build-essential python3-dev
   ```

   If OpenMP support causes build errors, disable it by setting
   `HDBSCAN_NO_OPENMP=1` in your environment when installing.

   Optional packages enable extra features such as diagram rendering and
   video previews. Install them with:
   ```bash
   sudo apt-get install graphviz ffmpeg
   ```

   Alternatively, you can use the helper script:
   ```bash
   ./scripts/setup.sh
   ```

   If you prefer pip:
   ```bash
   uv pip install -e .
   ```

3. Configure your editor to use the project's linting and formatting settings
   - For VSCode, the recommended settings are included in `.vscode/settings.json`
   - For PyCharm, import the code style settings from `.idea/codeStyles`

### Development Tools

- **Task**: The project uses [Task](https://taskfile.dev) for common development tasks
  ```bash
  # Clean Python cache files
  task clean

  # Run all checks (lint, type check, test)
  task check

  # Run unit and integration tests (excludes tests marked "slow")
  task test:fast

  # Run the entire suite including slow tests
  task test:all

  # Lint, type check and run all tests with coverage
  task verify
  ```

### Troubleshooting

- **Missing tools**: If commands like `flake8` or `pytest` are not found, make sure the
  virtual environment is activated with `source .venv/bin/activate`. Reinstall
  dependencies using `uv pip install -e '.[full,dev]'` if necessary.
- **Missing `task` command**: Run `which task` to verify Go Task is installed.
  Re-run `scripts/setup.sh` if the command is unavailable.

## Code Style Guidelines

Autoresearch follows strict code style guidelines to maintain consistency across the codebase:

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use 4 spaces for indentation (no tabs)
- Maximum line length of 100 characters
- Use meaningful variable and function names
- Add docstrings to all public modules, functions, classes, and methods

### Linting and Type Checking

Before submitting a pull request, ensure your code passes all linting and type checking:

```bash
# Format code
uv run black .
uv run isort .
# Automatically fix issues using ruff
uv run ruff format src tests
uv run ruff check --fix src tests
```

```bash
# Run flake8 for linting
uv run flake8 src tests

# Run mypy for type checking
uv run mypy src
uv run mypy --strict tests/behavior
# Expect roughly 20 seconds runtime on a standard setup.
# Use '--cache-dir=.mypy_cache' to enable incremental caching or
# run mypy on subpackages (e.g. 'uv run mypy src/autoresearch')
# if you need quicker iterations.
```

Install the repository's pre-commit hooks to execute the focused flake8 rule
set (`F401`, `F402`, `F811`, `W291`, `W293`, `W391`) before every commit:

```bash
pre-commit install
pre-commit run --all-files flake8-lint
```

The lint hook aligns with `tests/integration/test_lint_regressions.py`, which
fails if unused imports or stray whitespace return to `search/core`, behavior
fixtures, or the integration suite.

### Project-specific mypy baseline

Before modifying the search stack or the tests that exercise it, capture the
current typing gaps. First ensure the `dev-minimal` and `test` extras are
installed (for example by running `task install`, which syncs both extras).
Then execute the focused baseline check:

```bash
uv run --extra dev-minimal --extra test \
  mypy src/autoresearch/search/core.py tests/unit tests/integration
```

Running the targeted command keeps the scope reproducible while covering the
highest impact modules. Recording the resulting error inventory in your pull
request description grounds subsequent fixes and helps reviewers track
progress against the known baseline.

### Imports

- Group imports in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library specific imports
- Within each group, imports should be sorted alphabetically

### Docstrings

- Use Google-style docstrings
- Include type annotations in function signatures
- Document parameters, return values, and exceptions

Example:
```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of the function.

    Longer description explaining the function's purpose and behavior.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    # Function implementation
    return True
```

## Testing Requirements

Autoresearch follows a BDD/TDD approach to development. All new features and bug fixes should include appropriate tests. Additional recommendations are provided in [docs/testing_guidelines.md](docs/testing_guidelines.md).

### Test Organization

Tests are organized into three categories:

1. **Unit Tests** (`tests/unit/`): Test individual components in isolation
2. **Integration Tests** (`tests/integration/`): Test interactions between components
3. **Behavior Tests** (`tests/behavior/`): BDD-style tests using Gherkin syntax

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest --rootdir=. tests/behavior -q

# Run with coverage report
uv run pytest --cov=src
```

For convenience you can run linting, type checks, and the full test suite with coverage using:

```bash
task verify
```

The BDD tests live under `tests/behavior` and can be executed separately if you
only want to run the behavior scenarios.

After tests complete, remove untracked artifacts such as `kg.duckdb`, `rdf_store`,
and any `__pycache__` directories to keep your working tree clean.

### Test Coverage Requirements

- All new code should have at least 90% test coverage
- Critical components should have 100% test coverage
- Tests should cover both normal operation and error cases

Continuous integration invokes `task coverage`, which runs the entire suite with
coverage reporting. This command must succeed to satisfy the 90% coverage gate.

### Writing Tests

#### Unit Tests
- Create a new file in `tests/unit/` named `test_<module_name>.py`
- Use pytest fixtures for setup and teardown
- Test each function and method independently
- Mock external dependencies

#### Integration Tests
- Create a new file in `tests/integration/` named `test_<feature_name>.py`
- Test how components interact with each other
- Minimize mocking to test actual interactions

#### Behavior Tests
- Create a feature file in `tests/behavior/features/` using Gherkin syntax
- Implement step definitions in `tests/behavior/steps/`
- Focus on user-facing behavior and scenarios

### Stub Modules for Optional Dependencies

Tests rely on typed stub modules under `tests/stubs/` to provide fallbacks for
optional third-party packages.  When adding a new stub:

- Define the runtime behaviour with lightweight classes or functions.
- Describe the available attributes using `typing.Protocol` (or `TypedDict`
  when modelling dictionaries) so that mypy can type-check code that imports
  the stubbed module.
- Install the module via :func:`tests.stubs._registry.install_stub_module`
  instead of manually modifying `sys.modules`.  The helper creates parent
  packages, registers submodules, and returns the typed module instance.
- Keep the stub small and deterministic—avoid network calls or heavy
  dependencies.  If the real package is available, prefer importing it and only
  use the stub when the import fails.

Document new helper utilities or patterns alongside the stub so other
contributors can maintain type parity with the real dependency.

### Strict typing workflow and stub fidelity

The project enforces `--strict` typing across `src/` and `tests/`.  Use the
following workflow to keep the codebase free from accidental `Any` regressions.

#### Adding or updating stubs

- Start from a failing import or type error and confirm whether a runtime shim
  already exists under `tests/stubs/`.
- Mirror the public API of the real package: align module names, exported
  attributes, and the minimal behaviour needed by Autoresearch.
- Use protocols or typed callables to model interactions instead of returning
  loose dictionaries or untyped objects.
- Record expectations in unit tests when possible so that stub drift is caught
  by the suite.
- After implementing the stub, run the strict mypy command listed below to
  verify there are no residual `Any` types or interface mismatches.

#### Socratic stub fidelity checklist

Ask yourself these questions before submitting the stub:

- Do I understand how the production library behaves, and does the stub expose
  the same surface area that our code consumes?
- Where might `Any` sneak back in?  Did every function and attribute gain an
  explicit type instead of relying on inference from literals?
- If the real package were installed, would the code still run without hitting
  the stub?  Have I verified imports prefer the real module when available?
- What unit or integration test will fail if the stub drifts from the real
  implementation?  If none exist, can I add one?
- Could downstream contributors misinterpret my types?  Did I document the stub
  so reviewers can challenge hidden assumptions?

#### Required strict type-check commands before merging

Run both commands locally and paste the successful output into your pull
request description:

```bash
uv run --extra dev-minimal --extra test mypy --strict src tests
task check
```

Running the commands in this order first guarantees a clean strict type pass,
then reuses `task check` to execute the broader formatter, lint, and test
bundle.  If strict typing fails, address the missing annotations or stub gaps
before requesting review.

## Pull Request Process

1. Create a new branch for your feature or bugfix with a descriptive name
2. Make your changes, following the code style guidelines
3. Add or update tests to cover your changes
4. Add or update documentation as needed
5. Run all tests and ensure they pass
6. Submit a pull request with a clear description of the changes
7. Address any feedback from code reviews

### Pull Request Checklist

- [ ] Code follows the style guidelines
- [ ] Tests have been added or updated
- [ ] Documentation has been updated
- [ ] All tests pass
- [ ] Code has been linted and type-checked
- [ ] Commit messages are clear and descriptive

## Documentation

Good documentation is crucial for the project. Please follow these guidelines:

- Update the README.md if your changes affect the installation or usage
- Add or update docstrings for all public functions, classes, and methods
- Update or create documentation in the `docs/` directory as needed
- Use clear, concise language and provide examples where appropriate

### Specification workflow
- Draft specs for new modules in `docs/specs/` using the template in
  [docs/specs/README.md](docs/specs/README.md).
- Capture algorithms, invariants, proofs, and traceability links.

## Community

- Join the discussion in [GitHub Discussions](https://github.com/ravenoak/autoresearch/discussions)
- Report bugs and request features through [GitHub Issues](https://github.com/ravenoak/autoresearch/issues)
- Follow the project on GitHub to stay updated on changes

Thank you for contributing to Autoresearch!
