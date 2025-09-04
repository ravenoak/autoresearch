# Resource Monitor

## Overview

Background resource usage monitoring utilities. See [resource monitor
algorithm][rm] for sampling details.

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
  - [src/autoresearch/resource_monitor.py][m1]
- Tests
  - [tests/unit/test_resource_monitor_gpu.py][t1]
  - [tests/integration/test_monitor_metrics.py][t2]

[m1]: ../../src/autoresearch/resource_monitor.py
[t1]: ../../tests/unit/test_resource_monitor_gpu.py
[t2]: ../../tests/integration/test_monitor_metrics.py
[rm]: ../algorithms/resource_monitor.md
