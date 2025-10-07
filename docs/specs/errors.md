# Errors

## Overview

Error hierarchy for Autoresearch.

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
  - [src/autoresearch/errors.py][m1]
- Tests
  - [tests/unit/legacy/test_config_errors.py][t1]
  - [tests/unit/legacy/test_config_validation_errors.py][t2]
  - [tests/unit/legacy/test_errors.py][t3]

[m1]: ../../src/autoresearch/errors.py
[t1]: ../../tests/unit/legacy/test_config_errors.py
[t2]: ../../tests/unit/legacy/test_config_validation_errors.py
[t3]: ../../tests/unit/legacy/test_errors.py
