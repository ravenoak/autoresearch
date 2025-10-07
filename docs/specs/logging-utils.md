# Logging Utils

## Overview

Logging utilities that combine loguru and structlog for structured JSON
logging. Includes helpers to configure logging and obtain structured
loggers.

## Algorithms

- Implement core behaviors described above.

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Assume the logger is configured through `setup_logging`. The routine
attaches a single sink and preserves contextual metadata. A subsequent
call checks for existing sinks, ensuring idempotent configuration.
Structured dictionaries flow through the logger, so the loguru and
structlog integration yields deterministic JSON output, satisfying the
invariants.

## Simulation Expectations

Tests parameterize logger configuration and environment variables to
verify idempotent setup and context propagation. On 2025-09-07,
`pytest tests/unit/legacy/test_logging_utils.py
tests/unit/legacy/test_logging_utils_env.py` reported four passing tests.

## Traceability


- Modules
  - [src/autoresearch/logging_utils.py][m1]
- Tests
  - [tests/unit/legacy/test_logging_utils.py][t1]
  - [tests/unit/legacy/test_logging_utils_env.py][t2]

[m1]: ../../src/autoresearch/logging_utils.py
[t1]: ../../tests/unit/legacy/test_logging_utils.py
[t2]: ../../tests/unit/legacy/test_logging_utils_env.py
