# Tracing utilities

OpenTelemetry helpers for instrumenting operations.

## Key behaviors

- `setup_tracing(enabled)` initializes a console span exporter when enabled and is idempotent; disabled or repeated calls leave tracing off.
- `get_tracer(name)` always returns a tracer; spans record only when tracing has been enabled.

## Traceability

- **Modules**
  - `src/autoresearch/tracing.py`
- **Tests**
  - `../../tests/behavior/features/tracing.feature`
