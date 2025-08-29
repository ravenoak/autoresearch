# Configure Redis service for tests

## Context
Behavior and integration tests depend on a Redis backend, but the current test
runs hang in `redis.cluster` awaiting a server. A lightweight solution is needed
so tests fail fast or run with an in-memory substitute.

`tests/conftest.py` now starts a `fakeredis` instance when no server is
reachable, allowing distributed tests to run without external services.

## Dependencies

- None

## Acceptance Criteria
- Provide a local Redis instance or in-memory substitute for tests.
- Tests using Redis are tagged `requires_distributed` and skip cleanly when the
  service is unavailable.
- Document setup steps in testing guides or README.
- `uv run pytest -m requires_distributed -q` exits without hanging.

## Status
Archived
