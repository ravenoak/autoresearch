# Review Guidelines

- Add new workflow files only in `.github/workflows/` and ensure they
  trigger exclusively through `workflow_dispatch`. Reject push, schedule,
  or pull request triggers.
- Move obsolete or unneeded workflows to `.github/workflows.disabled/`
  to keep the active directory minimal.
