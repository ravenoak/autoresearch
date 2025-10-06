# Task Coverage Minimal Run PR Plan

## Overview

- Objective: capture a fresh minimal-extras coverage run, archive artifacts,
  and update status docs without reviving aborted-run language.
- Strategy: split work into focused PRs so each review remains quick and the
  timestamped artifacts flow downstream in a controlled order.

## PR 1: Minimal Coverage Execution and Archival

- **Goal:** produce and validate the baseline artifacts for the new run.
- **Scope:**
  - Run `uv run python scripts/archive_task_coverage_minimal.py` and confirm the
    command exits cleanly.
  - Inspect `baseline/logs/` to verify `coverage report --fail-under=90`
    succeeded and capture the relevant log snippet in the PR description.
  - Check the generated `baseline/coverage.xml` and archived
    `baseline/archive/${timestamp}.xml` to confirm line-rate ≥ 0.9.
  - Ensure `baseline/archive/${timestamp}/htmlcov/` exists and prune stale
    HTML directories from previous runs if present.
  - Stage the new log, XML snapshot, HTML dossier, and update `.gitignore` for
    timestamped paths that should not repeat.
- **Dependencies:** none.
- **Parallelization:** blocking; later PRs rely on the timestamp emitted here.

## PR 2: Documentation and Status Refresh

- **Goal:** communicate the new minimal coverage snapshot.
- **Scope:**
  - Draft `docs/status/task-coverage-${timestamp}.md`, mirroring prior entries
    and listing any skipped extras such as GPU or NLP helpers.
  - Summarize reproduction steps featuring the helper script used in PR 1.
  - Update `STATUS.md` and `docs/release_plan.md` coverage sections to cite the
    fresh log path, highlight minimal extras, and remove aborted-run language.
- **Dependencies:** requires artifacts and timestamp from PR 1.
- **Parallelization:** must follow PR 1; can run in parallel with unrelated
  efforts once artifacts land.

## PR 3: Follow-up Automation Hygiene (Optional Buffer)

- **Goal:** smooth future reruns and catch regressions early.
- **Scope:**
  - Add a quick check (e.g., Taskfile or CI note) reminding maintainers to run
    the archival helper when coverage dips.
  - Document any lessons learned during verification in `docs/status` or a
    short changelog blurb if desired by release managers.
- **Dependencies:** lightly depends on PR 2 for messaging alignment but could
  proceed after PR 1 if coordination is clear.
- **Parallelization:** can execute after PR 1 once messaging draft exists;
  coordinate with documentation owners to avoid duplicate edits.

## Execution Notes

- Record timestamps using system time at execution to keep artifacts aligned.
- Apply dialectical reasoning in PR discussions: articulate thesis (change),
  antithesis (risks), and synthesis (accepted plan).
- Keep each PR concise so reviewers can process updates quickly.
