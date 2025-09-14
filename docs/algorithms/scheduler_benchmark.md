# Scheduler Benchmark

## Overview
`scheduler_benchmark` measures resource usage of the task scheduler.

## Algorithm
It runs a timed loop, tracking CPU time and memory growth while enqueuing
dummy tasks.

## Proof sketch
The benchmark's loop runs for a fixed duration; bounds on the queue size
ensure resources remain within limits.

## Simulation
`tests/unit/test_scheduler_benchmark.py` validates timing growth and
memory ceilings.

## References
- [code](../../src/autoresearch/scheduler_benchmark.py)
- [spec](../specs/scheduler_benchmark.md)
- [tests](../../tests/unit/test_scheduler_benchmark.py)

## Related Issues
- [Benchmark scheduler queue saturation][issue]

[issue]: ../../issues/archive/benchmark-scheduler-queue-saturation.md
