# Prepare initial alpha release

## Context
The project is publicly visible but unreleased. Environment bootstrap fails
because the `task` CLI and dev dependencies like `pytest_httpx` are missing.
Before tagging `v0.1.0a1`, baseline tests and documentation must be
validated and workflows confirmed to remain dispatch-only.

## Milestone

- 0.1.0a1 (2026-03-01)

## Dependencies

- [investigate-task-check-verify-coverage-failures](investigate-task-check-verify-coverage-failures.md)

## Acceptance Criteria
- Development environment provisions `task` and required extras.
- `task check`, `task verify`, and `task coverage` succeed.
- Release notes and packaging instructions exist for `v0.1.0a1`.
- Issue backlog is prioritized for post-alpha milestones.
- GitHub workflows stay dispatch-only.

## Status
Archived
