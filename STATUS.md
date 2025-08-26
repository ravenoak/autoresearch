# Status

As of **August 26, 2025**, running `scripts/setup.sh` provisions the development
environment with Go Task and required extras. The VSS extension falls back to a
stub when network access is unavailable, but `./.venv/bin/task` is available for
checks.

## Lint, type checks, and spec tests
```text
./.venv/bin/task check
```
Result: passed

## Unit tests
```text
./.venv/bin/task check
```
Result: fails with `StorageError: Failed to initialize schema version` during
unit tests and halts before integration and behavior suites.

## Integration tests
```text
Integration tests did not run; `task check` stops during unit phase.
```

## Behavior tests
```text
Behavior tests did not run; `task check` stops during unit phase.
```

## Coverage
Coverage data was not generated; previous baseline remains at 67%, below the
required 90% threshold.
