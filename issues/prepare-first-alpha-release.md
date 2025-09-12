# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
publicly available. To tag version v0.1.0a1, we need a coordinated effort to
finalize outstanding testing, documentation, and packaging tasks while keeping
workflows dispatch-only.

## Dependencies
- [add-a2a-concurrency-proofs-and-simulations](
  archive/add-a2a-concurrency-proofs-and-simulations.md)
- [stabilize-api-and-improve-search](stabilize-api-and-improve-search.md)
- [resolve-integration-test-regressions](archive/resolve-integration-test-regressions.md)
- [fix-duckdb-storage-schema-initialization](fix-duckdb-storage-schema-initialization.md)
- [resolve-storage-persistence-test-failure](resolve-storage-persistence-test-failure.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [avoid-large-downloads-in-task-verify](archive/avoid-large-downloads-in-task-verify.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is updated.
- Workflows remain manual or dispatch-only.

## Status
Open
