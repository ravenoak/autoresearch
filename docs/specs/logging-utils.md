# Logging Utils

## Overview

Logging utilities that combine loguru and structlog for structured JSON logging.
Includes helpers to configure logging and obtain structured loggers.

## Algorithms

- Implement core behaviors described above.

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Core routines enforce invariants by validating inputs and state.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines.

## Traceability


- Modules
  - [src/autoresearch/logging_utils.py][m1]
- Tests
  - [tests/unit/test_logging_utils.py][t1]
  - [tests/unit/test_logging_utils_env.py][t2]

[m1]: ../../src/autoresearch/logging_utils.py
[t1]: ../../tests/unit/test_logging_utils.py
[t2]: ../../tests/unit/test_logging_utils_env.py
