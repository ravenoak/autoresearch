# Review Guidelines

- Add new workflow files only in `.github/workflows/` and ensure they
  trigger exclusively through `workflow_dispatch`. Reject push, schedule,
  or pull request triggers.
- Move obsolete or unneeded workflows to `.github/workflows.disabled/`
  to keep the active directory minimal.
- Confirm the automated `task mypy-strict` gate runs early in manual CI
  workflows so strict typing regressions fail fast.
- Leave the TestPyPI dry run paused unless the `run_testpypi_dry_run`
  input is explicitly enabled during `workflow_dispatch` execution.
