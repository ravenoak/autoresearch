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
Result: 13 failing unit tests and 4 errors. Several
`StorageError: Failed to create tables` errors persist, so integration and
behavior suites do not run.

## Integration tests
```text
Integration tests did not run; `task check` stops during unit phase.
```

## Behavior tests
```text
Behavior tests did not run; `task check` stops during unit phase.
```

## Coverage
`task verify` fails during collection with a circular import in the
distributed executors. Coverage remains unavailable; the previous baseline was
**14%**, below the required 90% threshold.
