# Scheduler Benchmark

## Overview

The `benchmark_scheduler` function measures resource usage of the backup
scheduler. It runs the scheduler for a requested duration and reports the CPU
and peak memory consumption observed.

## Algorithms

1. Replace the backup creation function with a no-op to avoid disk I/O.
2. Start the backup scheduler with in-memory paths.
3. Sleep for the requested duration.
4. Stop the scheduler and restore the original backup function.
5. Return the difference in user CPU time and max resident memory.

## Invariants

- CPU time remains below one second.
- Memory usage stays under 50 MB.

## Proof Sketch

The scheduler spends the test duration sleeping and performing minimal work.
Because the backup function is stubbed, no data is allocated or processed.
Therefore the CPU time stays near zero and memory usage remains bounded, which
matches the invariants exercised in the unit tests.

## Simulation Expectations

- Run the scheduler for varying durations to confirm minimal CPU usage.
- Monitor memory across runs to ensure no significant growth.

## Traceability

- Code: [src/autoresearch/scheduler_benchmark.py][m1]
- Tests: [tests/unit/legacy/test_scheduler_benchmark.py][t1]

[m1]: ../../src/autoresearch/scheduler_benchmark.py
[t1]: ../../tests/unit/legacy/test_scheduler_benchmark.py
