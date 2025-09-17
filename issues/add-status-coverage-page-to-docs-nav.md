# Add status coverage page to docs nav

## Context
`uv run --extra docs mkdocs build` now succeeds, but the build warns that
`docs/status/task-coverage-2025-09-17.md` is missing from the navigation.
Release preparation should include all published status reports so
contributors do not miss coverage requirements or wonder whether the file is
orphaned. The warning reappears on every docs build until the page is linked
from `mkdocs.yml`, which also means MkDocs will exclude it from published
navigation menus. 【d860f2†L1-L4】【f44ab7†L1-L1】【F:docs/status/task-coverage-2025-09-17.md†L1-L30】

## Dependencies
- None

## Acceptance Criteria
- Add the status coverage log to `mkdocs.yml` (or another appropriate navigation
  grouping) without breaking existing section ordering.
- `uv run --extra docs mkdocs build` completes without navigation warnings in a
  fresh environment with the docs extras synced.
- STATUS.md or TASK_PROGRESS.md notes the resolution so release checklists stay
  in sync.

## Status
Open
