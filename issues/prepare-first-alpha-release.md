# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
publicly available. To tag version v0.1.0a1, we need a coordinated effort to
finalize outstanding testing, documentation, and packaging tasks while keeping
workflows dispatch-only.

## Dependencies
- [add-test-coverage-for-optional-components](add-test-coverage-for-optional-components.md)
- [resolve-package-metadata-warnings](resolve-package-metadata-warnings.md)
- [fix-api-authentication-integration-tests](archive/fix-api-authentication-integration-tests.md)
- [streamline-task-verify-extras](streamline-task-verify-extras.md)
- [resolve-concurrent-query-interface-regression](resolve-concurrent-query-interface-regression.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is updated.
- Workflows remain manual or dispatch-only.

## Status
Open
