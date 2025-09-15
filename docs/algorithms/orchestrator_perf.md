# Orchestrator Performance

## Overview
`orchestrator_perf` models queueing behaviour for the orchestrator worker
pool.

## Algorithm
It applies M/M/c queue formulas to estimate wait times and worker
utilisation.

## Proof sketch
The formulas derive from standard queueing theory, ensuring bounds on
queue length and service time.

## Simulation
`scripts/orchestrator_perf_sim.py` samples synthetic workloads and the
tests compare predictions to measured metrics.

## References
- [code](../../src/autoresearch/orchestrator_perf.py)
- [spec](../specs/orchestrator-perf.md)
- [tests](../../tests/unit/test_orchestrator_perf_sim.py)
- [simulation](../../scripts/orchestrator_perf_sim.py)

## Related Issues
- [Simulate distributed orchestrator performance][issue]

[issue]: ../../issues/archive/simulate-distributed-orchestrator-performance.md
