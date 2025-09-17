# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

On September 17, 2025, the environment still lacks the Go Task CLI by default,
so a fresh `task verify` run has not been attempted. Targeted retries of the
DuckDB storage backend initialization, orchestrator perf simulation, and
optional extras suites complete without resource tracker errors, suggesting
the fixture cleanup helpers are effective when the suite reaches teardown.
However, running `uv run --extra test pytest tests/unit -q` now aborts during
collection because `scripts/distributed_coordination_sim.py` no longer
exports `elect_leader` or `process_messages`. Until the distributed
properties import their reference helpers, we cannot exercise the full unit
suite to validate that the resource tracker fix persists under coverage.
We still need a full `task verify` execution (with Task installed) to confirm
the issue is gone during coverage runs.

## Dependencies
- [fix-duckdb-storage-schema-initialization](
  ../archive/fix-duckdb-storage-schema-initialization.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
