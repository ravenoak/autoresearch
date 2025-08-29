# Resolve pre-alpha release blockers

## Context
The project targets its first public alpha (0.1.0a1) but currently lacks a passing full test suite and comprehensive release preparation. `task verify` fails due to missing package metadata, behavior-driven scenarios report failures, and coverage sits around 32%.

## Dependencies
- [fix-task-verify-package-metadata-errors](fix-task-verify-package-metadata-errors.md)

## Acceptance Criteria
- `task verify` completes without missing-package errors.
- Behavior-driven tests run and pass in the default environment.
- Line coverage reaches at least 90% with reports updated.
- Release steps and known limitations documented for tagging 0.1.0a1.

## Status
Open
