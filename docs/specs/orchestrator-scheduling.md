# Orchestrator Scheduling

## Overview
The orchestrator assigns work to agents while balancing priority and load.

## Algorithms
- Maintain a priority queue of pending tasks.
- Dispatch tasks round-robin among available agents.

## Invariants
- Each task is executed at most once.
- Agent concurrency never exceeds the configured limit.

## Proofs
The priority queue ensures higher priority tasks run first, and the round-
robin dispatcher guarantees fair agent utilization, preserving the
invariants.

## Traceability
- [src/autoresearch/orchestrator_perf.py][m1]
- [tests/unit/test_orchestrator_perf_sim.py][t1]
- [tests/unit/test_scheduler_benchmark.py][t2]

[m1]: ../../src/autoresearch/orchestrator_perf.py
[t1]: ../../tests/unit/test_orchestrator_perf_sim.py
[t2]: ../../tests/unit/test_scheduler_benchmark.py
