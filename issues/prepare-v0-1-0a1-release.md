# Prepare v0.1.0a1 release

## Context
The first alpha release needs a stable environment and passing tests. Packaging
should work offline, optional extras must install, and core algorithms require
initial proofs. Completing these steps clears the way to tag v0.1.0a1.

## Dependencies
- [fix-task-verify-coverage-hang](fix-task-verify-coverage-hang.md)
- [resolve-llm-extra-installation-failure](resolve-llm-extra-installation-failure.md)
- [improve-duckdb-extension-fallback](improve-duckdb-extension-fallback.md)
- [add-test-coverage-for-optional-components](add-test-coverage-for-optional-components.md)
- [add-storage-eviction-proofs-and-simulations](add-storage-eviction-proofs-and-simulations.md)

## Acceptance Criteria
- `task verify` runs to completion with all extras installed.
- DuckDB VSS extension fallback is documented and tested offline.
- `[llm]` extra installs within environment limits.
- Optional modules reach ≥90% line coverage.
- Storage eviction algorithm includes proof and simulations.
- TestPyPI dry-run succeeds and tag `v0.1.0a1` is created.

## Status
Open
