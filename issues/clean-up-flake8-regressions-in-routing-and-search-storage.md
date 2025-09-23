# Clean up flake8 regressions in routing and search storage

## Context
`task check` currently fails during the `flake8` phase after sourcing the Task
PATH helper because two regressions landed in the API routing factory and the
search storage helper. `flake8` reports
`src/autoresearch/api/routing.py:481:9: F841 local variable 'e' is assigned to
but never used` and `src/autoresearch/search/storage.py:13:1: F401
'..errors.StorageError' imported but unused`, so the command exits before it can
reach tests or coverage.
【153af2†L1-L2】【1dc5f5†L1-L24】【d726d5†L1-L3】 The unused `e` variable lives in the
lifespan handler that shields `StorageManager.setup()` during application
start-up, and the unused import sits at the top of the search storage wrapper.
【F:src/autoresearch/api/routing.py†L470-L496】【F:src/autoresearch/search/storage.py†L1-L33】
Clearing these lint failures is required before `task verify` and
`task coverage` can run cleanly ahead of the v0.1.0a1 release.

## Dependencies
- None

## Acceptance Criteria
- Remove or use the defensive `e` variable in
  `src/autoresearch/api/routing.py` so `flake8` no longer emits F841.
- Drop or replace the unused `StorageError` import in
  `src/autoresearch/search/storage.py` so `flake8` no longer emits F401.
- `task check` and `uv run flake8 src tests` complete without lint failures.
- STATUS.md and TASK_PROGRESS.md record the lint cleanup.

## Status
Open
