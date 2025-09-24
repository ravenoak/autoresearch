# Distributed

## Overview
The distributed package coordinates work across multiple nodes.

## Algorithm
Scheduling combines several strategies. A leader elects workers via
heartbeats and assigns tasks while monitoring queue saturation.
- **Round-robin** hands each new task to the next worker.
- **Work stealing** lets idle workers pull tasks from peers.
- **Priority queues** ensure high-priority tasks run first.
Failure recovery adds an overhead factor ``1/(1-p)`` where ``p`` is the
failure probability.

## Proof sketch
Leader election uses timeouts so at most one leader exists; tasks are
acknowledged, preventing loss.

## Simulation
`tests/unit/test_distributed.py` and `scripts/distributed_coordination_sim.py`
model coordination and verify convergence.

Regression coverage also exercises
[`test_execute_agent_remote`](
  ../../tests/unit/test_distributed_executors.py::test_execute_agent_remote
),
which ensures Ray-compatible serialization of `QueryState`.
The regression now runs without an `xfail` guard, and
[`SPEC_COVERAGE.md`](../../SPEC_COVERAGE.md) records the Ray path as
standard coverage for the distributed executors module.

## References
- [code](../../src/autoresearch/distributed/)
- [spec](../specs/distributed.md)
- [tests](../../tests/unit/test_distributed.py)
- [simulation](../../scripts/distributed_coordination_sim.py)

## Related Issues
- [Fix distributed perf sim CLI failure][issue]

[issue]: ../../issues/archive/fix-distributed-perf-sim-cli-failure.md
