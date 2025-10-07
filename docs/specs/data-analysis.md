# Data analysis

## Overview

This spec describes behavior of `metrics_dataframe` for summarizing agent timing
metrics.

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
  - [src/autoresearch/data_analysis.py][m1]
- Tests
  - [tests/behavior/features/data_analysis.feature][t1]
  - [tests/unit/legacy/test_data_analysis.py][t2]
  - [tests/unit/legacy/test_kuzu_polars.py][t3]

[m1]: ../../src/autoresearch/data_analysis.py
[t1]: ../../tests/behavior/features/data_analysis.feature
[t2]: ../../tests/unit/legacy/test_data_analysis.py
[t3]: ../../tests/unit/legacy/test_kuzu_polars.py
