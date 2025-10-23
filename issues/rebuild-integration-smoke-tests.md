# Rebuild integration smoke tests

## Context
The legacy integration smoke tests relied on ad hoc runners and print-based assertions, which
made it difficult to rely on automated feedback. We need proper pytest coverage for the import
regression checks and the CLI behavior scenarios so that future regressions surface in CI.

## Dependencies
- None

## Acceptance Criteria
- Import regression tests run as standard pytest cases with integration markers and real imports.
- CLI integration smoke tests rely on pytest fixtures for isolation and avoid writing to shared
  directories.
- Optional dependencies that underpin orchestration paths are guarded with existing `requires_*`
  markers.
- The new integration tests pass locally and in CI, demonstrating that the suite is stable.

## Status
Archived
