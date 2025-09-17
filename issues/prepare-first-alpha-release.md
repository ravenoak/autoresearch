# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-17 the Go Task CLI is still absent in a fresh environment, so running
`uv run task check` fails until contributors install Task manually. After
syncing the `dev-minimal` and `test` extras, `uv run python scripts/check_env.py`
now reports only the missing Go Task CLI. 【12a21c†L1-L9】【0525bf†L1-L26】
Targeted test suites continue to pass where helpers exist: the config weight
validator, DuckDB extension fallback, VSS extension loader, ranking
consistency, and optional extras checks all succeed with the `[test]` extras
installed. 【4567c0†L1-L2】【3108ac†L1-L2】【abaaf2†L1-L2】【897640†L1-L3】【d26393†L1-L2】
However, running `uv run --extra test pytest tests/unit -q` still fails during
collection because `scripts/distributed_coordination_sim.py` no longer exports
`elect_leader` or `process_messages`, so the distributed coordination
properties cannot import their reference helpers. 【382418†L1-L23】 `uv run mkdocs
build` also fails because docs extras are not present in a minimal
environment. 【9f25fa†L1-L3】 These gaps block the release checklist and require
targeted fixes before we can draft reliable release notes.

## Dependencies
- [restore-distributed-coordination-simulation-exports](
  restore-distributed-coordination-simulation-exports.md)
- [resolve-resource-tracker-errors-in-verify](
  resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](
  resolve-deprecation-warnings-in-tests.md)
- [document-docs-build-prerequisites](document-docs-build-prerequisites.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- Workflows remain manual or dispatch-only.

## Status
Open
