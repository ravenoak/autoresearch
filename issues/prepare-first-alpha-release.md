# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
publicly available. To tag version v0.1.0a1, we need a coordinated effort to
finalize outstanding testing, documentation, and packaging tasks while keeping
workflows dispatch-only. The 2025-09-14 runs of `task check` and `task verify`
halt at the type-checking stage due to mypy errors, preventing the test suite
from executing.

## Dependencies
- [resolve mypy errors in orchestrator perf][resolve-mypy-errors]
- [fix-search-ranking-and-extension-tests](fix-search-ranking-and-extension-tests.md)
- [fix-benchmark-scheduler-scaling-test](fix-benchmark-scheduler-scaling-test.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [audit-spec-coverage-and-proofs](audit-spec-coverage-and-proofs.md)
- [fix-api-authentication-regressions](fix-api-authentication-regressions.md)
- [fix-oxigraph-backend-initialization](fix-oxigraph-backend-initialization.md)
- [fix-mkdocs-griffe-warnings](fix-mkdocs-griffe-warnings.md)
- [add-api-authentication-proofs](add-api-authentication-proofs.md)
- [add-oxigraph-backend-proofs](add-oxigraph-backend-proofs.md)

[resolve-mypy-errors]: resolve-mypy-errors-in-orchestrator-perf-and-search-core.md

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is updated.
- Workflows remain manual or dispatch-only.

## Status
Open
