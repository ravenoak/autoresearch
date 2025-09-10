# Resolve concurrent query interface regression

## Context
Running `uv run --extra test pytest` on September 9, 2025 shows `tests/integration/test_a2a_interface.py::test_concurrent_queries` failing with `assert 0 == 3`, indicating the A2A interface no longer returns results concurrently.
On September 10, 2025, `task verify EXTRAS="nlp ui vss git distributed analysis llm parsers"` fails at
`tests/unit/test_a2a_interface.py::TestA2AInterface::test_handle_query_concurrent`, further confirming concurrency issues.

## Dependencies
None.

## Acceptance Criteria
- `tests/integration/test_a2a_interface.py::test_concurrent_queries` returns three results.
- Concurrency logic in the A2A interface is restored with regression coverage.

## Status
Open
