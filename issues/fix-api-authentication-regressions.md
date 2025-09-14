# Fix API authentication regressions

## Context
A `uv run pytest` on 2025-09-14 reported numerous authentication and
permission failures. Requests without valid API keys returned `200` instead
of `401` or `403`, affecting suites under `tests/integration/test_api_auth*`,
`test_api_docs.py`, `test_api_streaming.py`, `test_cli_http.py`, and
`test_monitor_metrics.py`.

## Dependencies
None

## Acceptance Criteria
- API endpoints enforce API keys and correct status codes.
- Authentication middleware validates requests before reading the body.
- Integration tests for auth, docs, streaming, CLI, and metrics pass.
- Documentation explains required API keys and roles.

## Status
Open
