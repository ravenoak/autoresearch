# Resolve distributed circular import

## Context
`task verify` fails during test collection with a circular import between
`distributed.executors` and `orchestration.state`, preventing integration
tests from running.

## Dependencies

- None

## Acceptance Criteria
- Refactor modules to break the circular dependency between distributed
  executors and orchestration state.
- `task verify` collects tests without ImportError.

## Status
Archived
