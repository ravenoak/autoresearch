# Fix distributed perf sim CLI failure

## Context
`task verify` fails at
`tests/unit/test_distributed_perf_sim_script.py::test_cli_execution`
because `scripts/distributed_perf_sim.py` exits with an error when
invoked via `uv run`.

## Dependencies
- None

## Acceptance Criteria
- `test_distributed_perf_sim_script.py::test_cli_execution` passes during
  `task verify`.
- `distributed_perf_sim.py` handles CLI arguments and completes without
  errors.

## Status
Open
