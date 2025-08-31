# Replace FastAPI on event with lifespan events

## Context
Recent test runs emit `DeprecationWarning` from FastAPI that `on_event` is deprecated in favor of
lifespan handlers in `src/autoresearch/api/routing.py`. Using `on_event` may break with FastAPI
0.115+.

## Dependencies
None.

## Acceptance Criteria
- Refactor startup and shutdown hooks to FastAPI lifespan handlers.
- Update tests to cover application lifespan behavior.
- `task check` runs without FastAPI deprecation warnings.

## Status
Open
