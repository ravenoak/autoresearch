# Status

As of **August 28, 2025**, the environment lacks the `task` CLI. Manual
`uv` commands validate linting and type checks, but storage backend errors
block full test execution.

## Lint, type checks, and spec tests
`flake8`, `mypy`, and `scripts/check_spec_tests.py` pass with no issues.

## Unit tests
`pytest tests/unit` reports **84 passed, 1 skipped, and 29 deselected**.

## Targeted tests
`pytest tests/targeted` fails during collection: modules `docx` and
`pdfminer` are missing.

## Integration tests
Storage initialization raises `AttributeError: 'DuckDBPyConnection' object has
no attribute 'fetchone'`, yielding **15 failed, 157 passed, 4 skipped, 93
deselected, 39 errors**.

## Behavior tests
Behavior scenarios trigger the same DuckDB initialization error and all fail.

## Coverage
Coverage was not recomputed; unit subset coverage remains at **91%**.
