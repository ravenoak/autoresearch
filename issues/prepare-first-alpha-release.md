# Prepare first alpha release

## Context
Version 0.1.0a1 will be the project's first public alpha. The environment
provisions via `scripts/setup.sh`, yet `task check` stalls during unit tests
and integration tests require the `redis` package. Behavior tests remain
unreliable. Release notes and packaging steps are incomplete.

## Acceptance Criteria
- `task check` and `task verify` complete on a fresh clone.
- Integration tests run with `redis` available or skip cleanly when absent.
- Behavior suite passes or scenarios are updated.
- Release notes and packaging instructions drafted.
- Backlog prioritized for post-alpha milestones.

## Status
Open

