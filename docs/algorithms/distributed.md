# Distributed

## Overview
The distributed package coordinates work across multiple nodes.

## Algorithm
A leader elects workers via heartbeats and assigns tasks while monitoring
queue saturation.

## Proof sketch
Leader election uses timeouts so at most one leader exists; tasks are
acknowledged, preventing loss.

## Simulation
`tests/unit/test_distributed.py` and `scripts/distributed_coordination_sim.py`
model coordination and verify convergence.

## References
- [code](../../src/autoresearch/distributed/)
- [spec](../specs/distributed.md)
- [tests](../../tests/unit/test_distributed.py)
- [simulation](../../scripts/distributed_coordination_sim.py)

## Related Issues
- [Fix distributed perf sim CLI failure][issue]

[issue]: ../../issues/archive/fix-distributed-perf-sim-cli-failure.md
