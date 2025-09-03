# Fix task check command block

## Context
Running `task check` fails with `error: unexpected argument '-' found` because
`Taskfile.yml` embeds `task check-env` on the same line as `uv sync`. The `-`
argument reaches `uv sync`, so lint and tests never run.

## Dependencies
None.

## Acceptance Criteria
- Separate `uv sync` and `task check-env` into distinct commands in `Taskfile.yml`.
- `task check` runs flake8, mypy, spec tests, and targeted unit tests.

## Status
Archived
