# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
publicly available. To tag version v0.1.0a1, we need a coordinated effort to
finalize outstanding testing, documentation, and packaging tasks while keeping
workflows dispatch-only.

## Dependencies
- [install-task-cli-system-level](archive/install-task-cli-system-level.md)
- [fix-api-authentication-and-metrics-tests](fix-api-authentication-and-metrics-tests.md)
- [fix-search-ranking-and-extension-tests](fix-search-ranking-and-extension-tests.md)
- [fix-storage-integration-test-failures](fix-storage-integration-test-failures.md)
- [fix-benchmark-scheduler-scaling-test](fix-benchmark-scheduler-scaling-test.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is updated.
- Workflows remain manual or dispatch-only.

## Status
Open
