# API Rate Limiting

## Overview

Token bucket limits API requests per client. See [algorithm][alg] for proof and
convergence details.

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
  - [src/autoresearch/api/middleware.py][m1]
- Tests
  - [tests/unit/test_property_api_rate_limit_bounds.py][t1]

[m1]: ../../src/autoresearch/api/middleware.py
[t1]: ../../tests/unit/test_property_api_rate_limit_bounds.py

[alg]: ../algorithms/api_rate_limiting.md
