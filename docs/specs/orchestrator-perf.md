# Orchestrator Performance

## Overview

`queue_metrics` models an M/M/c queue for the orchestrator's worker pool, while
`simulate` augments those metrics with a simple memory estimate. The spec
summarizes formulas, invariants, and validation strategies.

## Algorithms

- Utilization is `rho = lambda / (c * mu)` where `lambda` is arrival rate,
  `mu` the per-worker service rate, and `c` the worker count.
- The empty-queue probability is
  `p0 = 1 / (sum_{n=0}^{c-1} (lambda/mu)^n / n! + (lambda/mu)^c /`
  `(c! * (1 - rho)))`.
- Average queue length follows
  `Lq = p0 * (lambda/mu)^c * rho / (c! * (1 - rho)^2)`.
- `simulate` returns queue metrics and adds `tasks * mem_per_task` as
  `expected_memory`.

## Invariants

- `workers`, `arrival_rate`, and `service_rate` are positive.
- `rho < 1` ensures stability; otherwise metrics are undefined.
- `expected_memory` equals `tasks * mem_per_task`.

## Proof Sketch

Standard M/M/c results [1] yield the expressions for `p0` and `Lq`. When
`rho < 1`, these formulas guarantee finite queue length. `simulate` merely
multiplies task count by per-task memory, so the memory invariant holds.

## Simulation Expectations

- Run `uv run scripts/orchestrator_perf_sim.py --workers 2 --arrival-rate 3 \
  --service-rate 5 --tasks 50 --mem-per-task 0.5` to verify metrics.
- Increasing `workers` should decrease `Lq` while utilization stays below one.
- Adding `--benchmark` exercises the throughput micro-benchmark.

## Benchmark Tuning

Hardware differences affect throughput. Unit tests and scripts use the
``SCHEDULER_BASELINE_OPS`` and ``SCHEDULER_SCALE_THRESHOLD`` environment
variables to calibrate expectations.

- ``SCHEDULER_BASELINE_OPS`` sets the minimum single-worker throughput in
  tasks per second. The fixture-backed default mirrors
  ``baseline/evaluation/scheduler_benchmark.json`` (≈121.7) and can be
  lowered on constrained systems.
- ``SCHEDULER_SCALE_THRESHOLD`` defines the required speedup when adding
  more workers. Tests compute 90 % of the recorded throughput ratio
  (≈1.78) so modest hardware variance still satisfies the expectation.
- Memory checks reuse the same baseline to enforce a 25 MiB budget during
  regression runs.

Adjust these variables before running ``pytest`` or
``scripts/orchestrator_perf_sim.py --benchmark`` to match local hardware.

## Traceability

- Code: [src/autoresearch/orchestrator_perf.py][m1]
- Script: [scripts/orchestrator_perf_sim.py][m2]
- Tests
  - [tests/integration/test_orchestrator_performance.py][t94]
  - [tests/unit/legacy/test_orchestrator_perf_sim.py][t95]
  - [tests/unit/legacy/test_scheduler_benchmark.py][t96]

[1]: https://en.wikipedia.org/wiki/M/M/c_queue
[m1]: ../../src/autoresearch/orchestrator_perf.py
[m2]: ../../scripts/orchestrator_perf_sim.py

[t94]: ../../tests/integration/test_orchestrator_performance.py
[t95]: ../../tests/unit/legacy/test_orchestrator_perf_sim.py
[t96]: ../../tests/unit/legacy/test_scheduler_benchmark.py
