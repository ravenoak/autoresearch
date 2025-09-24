# Prepare first alpha release

## Context
The repository remains publicly visible yet untagged, so the first alpha
release still depends on a coordinated push across testing, packaging,
and documentation. The September 23 baselines captured in
`baseline/logs/task-verify-20250923T204732Z.log` and
`baseline/logs/verify-warnings-20250923T224648Z.log` confirm that
`task verify`, `task coverage`, and the warnings-as-errors sweep all pass
with 890 unit, 324 integration, and 29 behavior tests. A fresh
September 24 run of
`uv run --extra test pytest tests/unit -m "not slow" -rxX` reproduces the
same pass counts while reporting five XPASS promotions and eight
remaining XFAIL guards across ranking, search, parser, and storage
modules. Those results surface additional alignment work before tagging.
The Go Task CLI is still absent from the default Codex shell, so release
operators must keep using `uv` invocations unless they source the
`scripts/setup.sh` PATH helper.

A dialectical review of the outstanding work now surfaces four themes:
the XPASS promotions, refreshed mathematical backing for the token
budget heuristic, completion of the remaining XFAIL clean-up in ranking,
search, parser, and storage modules, and staging of packaging artifacts.
Socratic questioning asks whether the existing documentation actually
proves what the tests assert and whether our packaging instructions
match a fresh dry run. New issues cover each thread so that we can close
this release ticket once the dependencies land.

A fresh September 24 verification rechecked the supporting lint (`uv run
--extra dev-minimal --extra test flake8 src tests`), typing (`uv run
--extra dev-minimal --extra test mypy src`), and documentation (`uv run
--extra docs mkdocs build`) gates. Each command succeeded while
`task --version` still fails, reinforcing the need to rely on `uv`
wrappers or the PATH helper until we package a Task binary alongside the
alpha tag. 【6c5abf†L1-L1】【16543c†L1-L1】【84bbfd†L1-L4】【5b4d9e†L1-L1】
【311dfe†L1-L2】

### Completed PR-sized tasks
- [retire-stale-xfail-markers-in-unit-suite.md]
  (archive/retire-stale-xfail-markers-in-unit-suite.md)
- [refresh-token-budget-monotonicity-proof.md]
  (archive/refresh-token-budget-monotonicity-proof.md)
- [stabilize-ranking-weight-property.md]
  (archive/stabilize-ranking-weight-property.md)
- [restore-external-lookup-search-flow.md]
  (archive/restore-external-lookup-search-flow.md)
- [finalize-search-parser-backends.md]
  (archive/finalize-search-parser-backends.md)
- [stabilize-storage-eviction-property.md]
  (archive/stabilize-storage-eviction-property.md)
- [stage-0-1-0a1-release-artifacts.md]
  (archive/stage-0-1-0a1-release-artifacts.md)

## Dependencies
- [retire-stale-xfail-markers-in-unit-suite.md]
  (archive/retire-stale-xfail-markers-in-unit-suite.md)
- [refresh-token-budget-monotonicity-proof.md]
  (archive/refresh-token-budget-monotonicity-proof.md)
- [stabilize-ranking-weight-property.md]
  (archive/stabilize-ranking-weight-property.md)
- [restore-external-lookup-search-flow.md]
  (archive/restore-external-lookup-search-flow.md)
- [finalize-search-parser-backends.md]
  (archive/finalize-search-parser-backends.md)
- [stabilize-storage-eviction-property.md]
  (archive/stabilize-storage-eviction-property.md)
- [stage-0-1-0a1-release-artifacts.md]
  (archive/stage-0-1-0a1-release-artifacts.md)

## Acceptance Criteria
- All dependency issues listed above are closed.
- The "Prerequisites for tagging 0.1.0a1" section in
  `docs/release_plan.md` reflects the latest dry-run packaging logs and
  XPASS retirements.
- `CHANGELOG.md` includes drafted release notes for `0.1.0a1` that cite
  the staging sweep.
- `task docs` (or `uv run --extra docs mkdocs build`) succeeds after the
  documentation extras are synced.
- Workflows under `.github/workflows` remain dispatch-only.
- The `v0.1.0a1` tag is created only after the above steps and a fresh
  `task verify` pass succeed.

## Resolution
All dependency tickets have now been archived alongside the Unreleased
changelog updates that document their fixes. Capture a final
`task verify` run (including warnings-as-errors) after the upcoming
verification sweep, then archive this umbrella issue with the resulting
log references.

## Status
Open
