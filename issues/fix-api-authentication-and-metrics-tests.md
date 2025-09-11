# Fix API authentication and metrics tests

## Context
Integration tests for API key enforcement and monitoring metrics fail.
`tests/integration/test_api_streaming.py::test_stream_requires_api_key`,
`tests/integration/test_cli_http.py::test_http_api_key`, and
`tests/integration/test_monitor_metrics.py::test_system_monitor_metrics_exposed`
report incorrect status codes.

## Dependencies
None.

## Acceptance Criteria
- API endpoints reject requests without a key.
- Monitoring metrics endpoint responds with HTTP 200 when configured.
- Associated integration tests pass.
- Documentation references authentication and metrics behavior.

## Status
Open
