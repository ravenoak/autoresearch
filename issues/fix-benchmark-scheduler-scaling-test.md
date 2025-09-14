# Fix benchmark scheduler scaling test

## Context
`task verify` fails on September 14, 2025 in
`tests/unit/test_orchestrator_perf_sim.py::test_benchmark_scheduler_scales`.
The benchmark asserts throughput scales with more workers but reports
`440.365` operations per second, below the expected `817.869`. This
regression prevents completion of the verification run and masks the
resource tracker error investigation.

## Dependencies
None

## Acceptance Criteria
- `tests/unit/test_orchestrator_perf_sim.py::test_benchmark_scheduler_scales`
  passes consistently on `task verify`.
- Benchmark thresholds reflect realistic performance margins.
- Documentation notes the expected scaling behavior and tuning options.

## Status
Open
