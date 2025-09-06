# Distributed

## Overview

Distributed execution utilities. See [distributed coordination][dc] for
coalition and scheduling details.

## Algorithms

- **Round-robin** assigns each incoming task to the next worker in turn for
  balanced workloads.
- **Work stealing** lets idle workers pull tasks from peers, equalizing queue
  lengths under bursty load.
- **Priority queue** scheduling selects the highest-priority task available so
  urgent work executes first.
- Detailed complexity and performance models appear in
  [distributed coordination][dc].

## Invariants

- **No lost tasks:** every enqueued task is processed or persisted.
- **Single leader:** at most one coordinator acts as leader at any time.
- **FIFO ordering:** brokers emit tasks in the order they were published.
- **Progress:** active workers eventually drain their assigned queues.
- Property-based tests such as [test_distributed_coordination.py][t4] and
  [test_coordination_properties.py][t5] exercise these guarantees.

## Proof Sketch

- A FIFO broker ensures ordering because dequeues mirror enqueues; tests [t4]
  assert this correspondence.
- Leader election chooses the minimum identifier; with unique identifiers a
  single leader exists, and random shuffles in [t5] confirm convergence.
- Tasks persist until acknowledged by a worker, so no task is lost;
  integration tests [t1] demonstrate end-to-end completion.
- As long as a worker remains alive, queued tasks eventually run, yielding
  liveness.

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
