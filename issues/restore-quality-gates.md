# Restore quality gates

## Context
The strict typing and coverage gates were temporarily replaced with placeholder
commands while optional extras stabilized. With those dependencies available
again we are restoring the real `uv run mypy --strict src tests` invocation in
`task check`/`task verify`, and we are reinstating a meaningful coverage
threshold. Contributors also need clear documentation so they can opt into
heavy extras locally when the strict gate requires them.

## Dependencies
- None

## Acceptance Criteria
- `task mypy-strict`, `task check`, and `task verify` call `uv run mypy --strict
  src tests` rather than echoing skip messages.
- Coverage tooling enforces a project-wide minimum (≥70%) via `.coveragerc` or
  equivalent command-line flags.
- Testing documentation explains how the restored gates behave and how to pass
  `EXTRAS` to install optional dependencies for local runs.
- Issue can close once `task check` and `task verify` pass with the reinstated
  gates.

## Status
Archived

`task check` and `task verify` succeeded on 2025-10-23 after reinstating the
strict typing and coverage gates, so this issue is closed.
