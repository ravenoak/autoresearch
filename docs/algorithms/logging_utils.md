# Logging utilities

The `logging_utils` module combines Loguru and structlog to emit JSON logs with
structured context. This enables machine-readable diagnostics while keeping the
interface simple.

## Structured logging

- `configure_logging` routes standard logging through Loguru and renders
  JSON via structlog.
- `get_logger` returns a structlog logger that accepts key–value context.

## Severity handling

Severity is controlled through standard levels (`DEBUG`, `INFO`, etc.). The
function `configure_logging_from_env` reads `AUTORESEARCH_LOG_LEVEL` to set the
threshold.

## Security guarantees

The logging setup aims to avoid leaking secrets. Callers should sanitize
sensitive fields before logging; the [simulation](../../scripts/logging_sim.py)
demonstrates redaction of tokens.

## References

- [`logging_utils.py`](../../src/autoresearch/logging_utils.py)
- [`logging_sim.py`](../../scripts/logging_sim.py)
