# Orchestrator Scheduling

## Overview

The orchestrator assigns work to agents while balancing priority and load.

## Algorithms

- Maintain a priority queue of pending tasks.
- Dispatch tasks round-robin among available agents.

## Invariants

- Each task is executed at most once.
- Agent concurrency never exceeds the configured limit.

## Proof Sketch

The priority queue ensures higher priority tasks run first, and the round-robin
dispatcher guarantees fair agent utilization, preserving the invariants.

## Simulation Expectations

- Simulate mixed-priority workloads to confirm queue ordering.
- Vary agent counts to verify concurrency limits.

## Traceability

- Code: [src/autoresearch/orchestrator_perf.py][m1]
- Tests
  - [tests/integration/test_orchestrator_performance.py][t94]
  - [tests/unit/legacy/test_orchestrator_perf_sim.py][t95]
  - [tests/unit/legacy/test_scheduler_benchmark.py][t96]

[m1]: ../../src/autoresearch/orchestrator_perf.py

[t94]: ../../tests/integration/test_orchestrator_performance.py
[t95]: ../../tests/unit/legacy/test_orchestrator_perf_sim.py
[t96]: ../../tests/unit/legacy/test_scheduler_benchmark.py
