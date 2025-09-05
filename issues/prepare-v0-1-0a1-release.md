# Prepare v0.1.0a1 release

## Context
The first alpha release needs a stable environment and passing tests. Packaging
should work offline, optional extras must install, and core algorithms require
initial proofs. Completing these steps clears the way to tag v0.1.0a1.

## Dependencies
- [ensure-go-task-cli-availability](archive/ensure-go-task-cli-availability.md)
- [fix-task-verify-coverage-hang](archive/fix-task-verify-coverage-hang.md)
- [fix-check-env-package-metadata-errors](archive/fix-check-env-package-metadata-errors.md)
- [add-test-coverage-for-optional-components](archive/add-test-coverage-for-optional-components.md)
- [formalize-spec-driven-development-standards]
  (archive/formalize-spec-driven-development-standards.md)
- [fix-streaming-webhook-test-style](fix-streaming-webhook-test-style.md)

## Acceptance Criteria
- `task verify` runs to completion with all extras installed.
- DuckDB VSS extension fallback is documented and tested offline.
- `[llm]` extra installs within environment limits.
- Optional modules reach ≥90% line coverage.
- TestPyPI dry-run succeeds and tag `v0.1.0a1` is created.

## Status
Open
