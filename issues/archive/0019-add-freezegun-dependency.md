# Issue 19: Add freezegun dependency

Track the gap "Missing freezegun dependency causes unit tests to fail" discovered during testing.

## Context
Running `uv run pytest tests/unit -q` raised `ModuleNotFoundError: No module named 'freezegun'`, preventing the unit test suite from executing.

## Acceptance Criteria
- Add `freezegun` to development dependencies
- Unit tests run without missing dependency errors
- Setup instructions mention the dependency

## Status
Done – `freezegun` added to development dependencies and setup instructions updated.

## Related
- #18
