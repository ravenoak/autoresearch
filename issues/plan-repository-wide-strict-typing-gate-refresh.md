# Plan repository-wide strict typing gate refresh

## Context
The strict typing gate already passes locally, and PR3 calls for removing the
residual test exclusions, capturing a fresh `mypy --strict` snapshot, and
updating the documentation and CI references. To keep iterations short and
reduce risk, we should split the work into focused pull requests with explicit
handoffs and verification notes.

## Dependencies
- None

## Acceptance Criteria
- Each scoped pull request listed in the plan defines actionable tasks and
  acceptance checks.
- Parallelisation and sequencing notes clarify which pull requests can progress
  simultaneously and which must wait for predecessors.
- The plan covers removing the mypy exclusion, recording a new strict run
  snapshot, updating documentation, and confirming CI entry points.
- Status is left Open until the plan has been executed or superseded.

## Plan

### PR3-a – Strict typing rehearsal and instrumentation
- Confirm the current `uv run mypy --strict src tests` invocation succeeds with
  the existing exclusion in place.
- Document any remaining blockers; if failures surface, raise follow-up tickets
  before proceeding.
- Produce a dry-run strict log under `baseline/logs/` to capture the pre-change
  state (timestamp, file count, and success indicator) so we can compare when
  the exclusion is removed.
- Inventory CI entry points (`Taskfile.yml`, `task check`, and reusable task
  definitions) to note where `task mypy-strict` is referenced today.
- Outcome: verified baseline proves removal work is low risk.
- Parallelisation: may run alongside unrelated doc or tooling updates that do
  not touch mypy configuration.

### PR3-b – Remove mypy test exclusions and refresh baseline
- Delete the `tests/(?:ui|unit)` exclusion from the `[tool.mypy]` configuration
  in `pyproject.toml`, removing the key entirely if it becomes empty.
- Re-run `uv run mypy --strict src tests` to confirm the gate stays green and
  capture the post-change metadata (ISO-8601 timestamp, file count, success
  status) in a new `baseline/logs/mypy-strict-<timestamp>.log` entry.
- Diff the dry-run log from PR3-a against the refreshed log to ensure the file
  count now reflects full suite coverage.
- Update or add CI notes (e.g., comments in `Taskfile.yml`) to indicate that no
  further filters are applied when invoking the strict task.
- Outcome: configuration fully covers `tests/` under strict typing with updated
  evidence.
- Parallelisation: depends on PR3-a completing successfully; should not be run
  concurrently with PR3-c because the documentation there consumes this log.

### PR3-c – Documentation and CI verification refresh
- Update `docs/dev/typing-strictness.md` to describe the removal of the
  exclusion, summarise the new strict run metadata, and explicitly note that all
  test suites now participate in the strict gate.
- Record in the documentation how the new baseline log is named and where it is
  stored, linking to the fresh timestamped artifact from PR3-b.
- Double-check `task check`, GitHub Actions workflows, and any other CI entry
  points to confirm they invoke `task mypy-strict` without additional filters;
  document that verification in the PR summary and commit message.
- Outcome: contributors can rely on the documentation and logs to understand
  strict typing coverage.
- Parallelisation: blocked on PR3-b because it consumes the refreshed log and
  configuration.

## Status
Open
