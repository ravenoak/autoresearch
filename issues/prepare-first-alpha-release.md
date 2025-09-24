# Prepare first alpha release

## Context
The repository remains publicly visible yet untagged, so the first alpha
release still depends on a coordinated push across testing, packaging,
and documentation. The September 23 baselines captured in
`baseline/logs/task-verify-20250923T204732Z.log` and
`baseline/logs/verify-warnings-20250923T224648Z.log` confirm that
`task verify`, `task coverage`, and the warnings-as-errors sweep all pass
with 890 unit, 324 integration, and 29 behavior tests. Those runs also
highlight five XPASS cases that continue to carry `xfail` markers, which
prevents the release gate from failing fast when regressions appear. The
Go Task CLI is still absent from the default Codex shell, so release
operators must keep using `uv` invocations unless they source the
`scripts/setup.sh` PATH helper.

A dialectical review of the outstanding work surfaces three threads: the
XPASS promotions, refreshed mathematical backing for the token budget
heuristic, and staging of packaging artifacts. Socratic questioning asks
whether the existing documentation actually proves what the tests assert
and whether our packaging instructions match a fresh dry run. New issues
cover each thread so that we can close this release ticket once the
dependencies land.

### PR-sized tasks
- [retire-stale-xfail-markers-in-unit-suite.md]
  (retire-stale-xfail-markers-in-unit-suite.md)
- [refresh-token-budget-monotonicity-proof.md]
  (refresh-token-budget-monotonicity-proof.md)
- [stage-0-1-0a1-release-artifacts.md]
  (stage-0-1-0a1-release-artifacts.md)

## Dependencies
- [retire-stale-xfail-markers-in-unit-suite.md]
  (retire-stale-xfail-markers-in-unit-suite.md)
- [refresh-token-budget-monotonicity-proof.md]
  (refresh-token-budget-monotonicity-proof.md)
- [stage-0-1-0a1-release-artifacts.md]
  (stage-0-1-0a1-release-artifacts.md)

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

## Status
Open
