# Status

As of **August 4, 2025**, the environment includes the `task` CLI. Running
`task check` executes linting, type checks, spec tests, and the unit subset.
The command reports **84 passed, 1 skipped, and 24 deselected** unit tests in
roughly two and a half minutes.

## Lint, type checks, and spec tests
`task check` completes without failures. `flake8` and `mypy` pass without
errors.

## Unit tests
All unit tests in `tests/unit` now pass.

## Targeted tests
`task verify` fails during collection: targeted tests require missing
dependencies `python-docx` and `pdfminer.six`.

## Integration tests
```text
Integration tests did not run; targeted tests failing.
```

## Behavior tests
```text
Behavior tests did not run; targeted tests failing.
```

## Coverage
Coverage remains unavailable because targeted tests failed. The last recorded
baseline was **14%**, below the required 90% threshold.
