# Resolve pre-alpha release blockers

## Context
The project targets its first public alpha (0.1.0a1) but still lacks a
comprehensive release-ready test suite. `task verify` now completes using
pre-built CUDA wheels yet exercises only a small targeted set of tests.
Behavior-driven scenarios continue to fail and coverage reflects just the
57 statements in those targeted modules.

The **August 31, 2025** `task verify` attempt failed early with
`test_message_processing_is_idempotent` raising a Hypothesis deadline error, so
coverage data was not generated.

## Dependencies
- [fix-task-verify-package-metadata-errors](fix-task-verify-package-metadata-errors.md)
- [address-task-verify-dependency-builds](address-task-verify-dependency-builds.md)
- [restore-behavior-driven-test-suite](restore-behavior-driven-test-suite.md)

## Acceptance Criteria
- `task verify` completes without missing-package errors.
- Behavior-driven tests run and pass in the default environment.
- Line coverage reaches at least 90% with reports updated.
- Release steps and known limitations documented for tagging 0.1.0a1.

## Status
Open
