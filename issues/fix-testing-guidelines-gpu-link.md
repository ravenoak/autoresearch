# Fix testing guidelines GPU wheels link

## Context

`uv run --extra docs mkdocs build` now succeeds but emits `WARNING - Doc file
'testing_guidelines.md' contains a link '../wheels/gpu/README.md', but the
target is not found among documentation files.`【9eabf1†L1-L6】 The warning
appears because `docs/testing_guidelines.md` links to the GPU wheels README
via `[wheels/gpu/README.md](../wheels/gpu/README.md)`, yet MkDocs excludes the
`wheels/` directory from the documentation build.
【F:docs/testing_guidelines.md†L90-L102】
Clean release builds require warning-free documentation runs, so the reference
must either move under `docs/` or be replaced with a working location. A
separate MkDocs warning now fires for `docs/release_plan.md` because it links
to the issue tracker; that follow-up lives in
[fix-release-plan-issue-links](fix-release-plan-issue-links.md) so this ticket
can stay focused on the GPU instructions.

## Dependencies

- None

## Acceptance Criteria

- `docs/testing_guidelines.md` references the GPU wheels instructions without
  triggering MkDocs warnings.
- The authoritative GPU wheel setup instructions remain easy to discover from
  the testing guidelines.
- `uv run --extra docs mkdocs build` finishes without warnings about missing
  documentation files.

## Status

Open
