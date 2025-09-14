# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
publicly available. To tag version v0.1.0a1, we need a coordinated effort to
finalize outstanding testing, documentation, and packaging tasks while keeping
workflows dispatch-only. `task check` now passes after resolving earlier mypy
errors, but `task verify` fails in
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::test_verify_extension_failure`,
blocking the release.

## Dependencies
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

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is updated.
- Workflows remain manual or dispatch-only.

## Status
Open
