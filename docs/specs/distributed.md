# Distributed

## Overview

Distributed execution utilities. See [distributed coordination][dc] for
coalition and scheduling details.

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
  - [src/autoresearch/distributed/][m1]
- Tests
  - [tests/integration/test_distributed_agent_storage.py][t1]
  - [tests/unit/test_distributed.py][t2]
  - [tests/unit/test_distributed_extra.py][t3]
  - [tests/analysis/test_distributed_coordination.py][t4]
  - [tests/unit/distributed/test_coordination_properties.py][t5]

[m1]: ../../src/autoresearch/distributed/
[t1]: ../../tests/integration/test_distributed_agent_storage.py
[t2]: ../../tests/unit/test_distributed.py
[t3]: ../../tests/unit/test_distributed_extra.py
[t4]: ../../tests/analysis/test_distributed_coordination.py
[t5]: ../../tests/unit/distributed/test_coordination_properties.py

[dc]: ../algorithms/distributed_coordination.md
