# Fix release plan issue links

## Context

`uv run --extra docs mkdocs build` now emits warnings because
`docs/release_plan.md` links to the in-repo issue files at
`../issues/clean-up-flake8-regressions-in-routing-and-search-storage.md` and
`../issues/fix-testing-guidelines-gpu-link.md`. MkDocs only tracks documents
under `docs/`, so these relative links resolve outside the build tree and are
reported as missing targets. 【aaf0c5†L1-L7】【F:docs/release_plan.md†L20-L36】
The release plan needs to reference the open tickets without tripping the
documentation build ahead of the v0.1.0a1 tag.

## Dependencies

- None

## Acceptance Criteria

- Update `docs/release_plan.md` so its references to the lint and documentation
  tickets no longer point outside the MkDocs tree.
- `uv run --extra docs mkdocs build` completes without warnings about
  `docs/release_plan.md`.
- STATUS.md and TASK_PROGRESS.md note the resolved documentation warning.

## Status

Open
