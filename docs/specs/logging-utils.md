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

- Modules
  - [src/autoresearch/logging_utils.py][m1]
- Tests
  - [tests/unit/test_logging_utils.py][t1]
  - [tests/unit/test_logging_utils_env.py][t2]

[m1]: ../../src/autoresearch/logging_utils.py
[t1]: ../../tests/unit/test_logging_utils.py
[t2]: ../../tests/unit/test_logging_utils_env.py
