# Status

As of **August 26, 2025**, running `scripts/codex_setup.sh` provisions the
development environment with Go Task and required extras. The VSS extension
falls back to a stub when network access is unavailable, and `task` becomes
available after adding `.venv/bin` to `PATH`.

## Lint, type checks, and spec tests
```text
task check
```
Result: `flake8` and `mypy` pass, but unit tests fail.

## Unit tests
```text
task check
```
Result: 39 failing unit tests, many raising
`StorageError: Failed to initialize schema version`; integration and behavior
suites do not run.

## Integration tests
```text
Integration tests did not run; `task check` stops during unit phase.
```

## Behavior tests
```text
Behavior tests did not run; `task check` stops during unit phase.
```

## Coverage
`task verify` reports total coverage at **14%**, below the required 90%
threshold.
