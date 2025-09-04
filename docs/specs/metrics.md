# Metrics

## Overview

Token usage tracking and budget adaptation helpers. See the [token budgeting
algorithm](../algorithms/token_budgeting.md) for update rules.

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
  - [src/autoresearch/orchestration/metrics.py][m1]
- Tests
  - [tests/unit/test_metrics_token_budget_spec.py][t1]

[m1]: ../../src/autoresearch/orchestration/metrics.py
[t1]: ../../tests/unit/test_metrics_token_budget_spec.py

