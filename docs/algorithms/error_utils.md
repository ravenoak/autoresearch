# Error utilities

The `error_utils` module standardizes how exceptions become user-facing
messages.

## Structured reporting

`ErrorInfo` captures a message, severity, suggestions, code examples and
context. Formatters adapt this structure for CLI, GUI, API and agent-to-agent
interfaces.

## Severity handling

`ErrorSeverity` enumerates levels (`critical`, `error`, `warning`, `info`).
`get_error_info` maps common exceptions to the appropriate severity; timeouts
downgrade to `warning`.

## Security guarantees

Callers are responsible for scrubbing secrets in exception context. When the
context is sanitized (e.g., `api_key='[REDACTED]'`), the helpers preserve the
redaction.

## References

- [`error_utils.py`](../../src/autoresearch/error_utils.py)

## Simulation

Automated tests confirm error utils behavior.

- [Spec](../specs/error-utils.md)
- [Tests](../../tests/unit/test_error_utils_additional.py)
