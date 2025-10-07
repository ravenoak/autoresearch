# Error Recovery

## Overview

Utilities for retrying operations with exponential backoff. The backoff doubles
the delay after each failure using `base_delay * 2^(attempt - 1)` and stops
after a successful call or when retries are exhausted, at which point a
`RuntimeError` is raised. The expected number of attempts for success with
probability `p` is `1/p`, as shown in the [error recovery algorithm note][alg].

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
  - [src/autoresearch/error_recovery.py][m1]
- Tests
  - [tests/unit/legacy/test_error_recovery.py][t1]

[m1]: ../../src/autoresearch/error_recovery.py
[t1]: ../../tests/unit/legacy/test_error_recovery.py
[alg]: ../algorithms/error_recovery.md
