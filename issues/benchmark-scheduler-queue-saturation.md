# Benchmark scheduler under queue saturation

## Context
Simulations show latency spikes when task arrivals near total service capacity.
We need real-world benchmarks to validate mitigation strategies.

## Dependencies
[simulate-distributed-orchestrator-performance][orchestrator-bench]

## Acceptance Criteria
- Benchmark scheduler with arrival rates approaching total service capacity.
- Record latency and throughput for at least three worker counts.
- Propose mitigation strategies for identified bottlenecks.

## Status
Open

[orchestrator-bench]: simulate-distributed-orchestrator-performance.md
