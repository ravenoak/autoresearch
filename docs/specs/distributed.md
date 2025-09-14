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
- Failure recovery adds an overhead factor `1/(1-p)` as described in
  [distributed overhead](../algorithms/distributed_overhead.md) and modeled by
  `orchestrator_distributed_sim.py`.

## Invariants

- **No lost tasks:** every enqueued task is processed or persisted.
- **Single leader:** at most one coordinator acts as leader at any time.
- **FIFO ordering:** brokers emit tasks in the order they were published.
- **Progress:** active workers eventually drain their assigned queues.
- Property-based tests such as `test_distributed_coordination.py` and
  `test_coordination_properties.py` exercise these guarantees.

## Proof Sketch

- A FIFO broker ensures ordering because dequeues mirror enqueues.
- Leader election chooses the minimum identifier; with unique identifiers a
  single leader exists, and random shuffles in [t5] confirm convergence.
- Tasks persist until acknowledged by a worker, so no task is lost;
  integration tests [t1] demonstrate end-to-end completion.
- As long as a worker remains alive, queued tasks eventually run, yielding
    liveness.
- The script `distributed_coordination_formulas.py` derives round-robin
  allocations and failure overhead.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines. Benchmarks such as
`distributed_recovery_benchmark.py` record CPU and memory usage during
retries. Simulations like `distributed_coordination_sim.py` exercise leader
election and ordering.

[dc]: ../algorithms/distributed_coordination.md
