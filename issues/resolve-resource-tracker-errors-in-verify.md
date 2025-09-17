# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

On September 17, 2025, the environment still lacks the Go Task CLI by default,
so a fresh `task verify` run has not been attempted. After syncing the
`dev-minimal` and `test` extras, `uv run python scripts/check_env.py` confirms
that Go Task is the remaining prerequisite. 【12a21c†L1-L9】【0525bf†L1-L26】
Targeted retries of the DuckDB extension fallback, ranking consistency, and
optional extras suites complete without resource tracker errors, suggesting the
fixture cleanup helpers remain effective when the suite reaches teardown.
【3108ac†L1-L2】【897640†L1-L3】【d26393†L1-L2】 However, running
`uv run --extra test pytest tests/unit -q` still aborts during collection
because `scripts/distributed_coordination_sim.py` no longer exports
`elect_leader` or `process_messages`. 【382418†L1-L23】 Until the distributed
properties import their reference helpers and Go Task is installed, we cannot
exercise the full unit suite under coverage to confirm the resource tracker fix.
We still need a full `task verify` execution (with Task installed) once the
distributed regression is resolved.

## Dependencies
- [fix-duckdb-storage-schema-initialization](
  ../archive/fix-duckdb-storage-schema-initialization.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
