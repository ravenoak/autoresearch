# Document docs build prerequisites

## Context
Running `uv run mkdocs build` in the evaluation container still fails with
`No such file or directory` because the docs extras are not installed by
default. 【9f25fa†L1-L3】 Contributors currently have to remember to sync the
docs dependencies manually, even though the Taskfile exposes a `docs` target
that installs the extras on demand. 【F:Taskfile.yml†L348-L350】 We need to
document the expected workflow so release instructions consistently recommend
either `task docs` or `uv run --extra docs mkdocs build` before verifying the
site.

## Dependencies
- None

## Acceptance Criteria
- Update release documentation (e.g. README or `docs/release_plan.md`) to
  instruct contributors to run `task docs` or `uv run --extra docs mkdocs build`
  before building the site.
- Confirm the updated guidance matches the Taskfile `docs` task and avoids
  suggesting `uv run mkdocs build` without extras.
- Note the change in STATUS.md or other status tracking so the release issue
  reflects the clarified workflow.

## Status
Open
