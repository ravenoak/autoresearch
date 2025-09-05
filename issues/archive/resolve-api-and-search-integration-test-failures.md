# Resolve API and search integration test failures

## Context
The integration suite reports numerous failures across API authentication, documentation, streaming, and search modules. Examples include `tests/integration/test_api_auth.py`, `tests/integration/test_api_docs.py`, `tests/integration/test_api_streaming.py`, `tests/integration/test_search_error_handling.py`, and `tests/integration/test_ranking_formula_consistency.py`. These must pass to stabilize the alpha release.

## Dependencies
None.

## Acceptance Criteria
- All API integration tests pass, covering authentication, docs, and streaming.
- Search integration tests run without AttributeError or regression failures.
- Ranking formula consistency tests succeed.
- `task verify` completes with no API or search test failures.

## Status
Archived
