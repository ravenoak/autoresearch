# Logging Utils

Logging utilities that combine loguru and structlog for structured JSON
logging. Includes helpers to configure logging and obtain structured
loggers.

## Features

- Unified JSON logging via `configure_logging`.
- `configure_logging_from_env` reads `AUTORESEARCH_LOG_LEVEL` to set the
  log level.
- `get_logger` returns a structured logger for modules.

## Traceability

- `../../tests/unit/test_logging_utils.py`
- `../../tests/unit/test_logging_utils_env.py`
