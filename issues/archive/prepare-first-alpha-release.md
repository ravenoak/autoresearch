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
- Updated `docs/release_plan.md` and STATUS.md with the passing 2025-09-25
  `uv run task verify` sweep and targeted coverage rerun, citing the BM25
  normalization, parallel payload, and numpy stub fixes that cleared the
  regressions. The same plan entry now notes the four-call VSS evidence
  captured by the refreshed stubbed search regression and the reproduction
  log so reviewers can track the deterministic vector search counts.
  【F:tests/unit/test_core_modules_additional.py†L18-L379】
  【22e0d1†L1-L11】
  Supporting links:
  - [docs/release_plan.md][plan-status]
  - [STATUS.md][status-sept25]
  - [src/autoresearch/search/core.py][bm25-normalization]
  - [src/autoresearch/orchestration/parallel.py][parallel-claims]
  - [tests/stubs/numpy.py][numpy-stub-deterministic]
- Added the matching 0.1.0a1 changelog note for the same fixes so the release
  record cites the new logs and code paths.
  ([CHANGELOG.md][changelog-verification])
- Archived the verification evidence alongside the focused coverage rerun and
  existing docs build log for traceability. Supporting logs:
  - [task-verify-20250925T022717Z.log][verify-log-pass]
  - [task-coverage-20250925T233024Z-targeted.log][targeted-coverage-log]
  - [mkdocs-build-20250925T001535Z.log][mkdocs-log]

[plan-status]:
  ../../docs/release_plan.md#status
[status-sept25]:
  ../../STATUS.md#september-25-2025
[bm25-normalization]:
  ../../src/autoresearch/search/core.py#L705-L760
[parallel-claims]:
  ../../src/autoresearch/orchestration/parallel.py#L145-L182
[numpy-stub-deterministic]:
  ../../tests/stubs/numpy.py#L12-L81
[changelog-verification]:
  ../../CHANGELOG.md#verification-evidence
[verify-log-pass]:
  ../../baseline/logs/task-verify-20250925T022717Z.log
[targeted-coverage-log]:
  ../../baseline/logs/task-coverage-20250925T233024Z-targeted.log
[mkdocs-log]:
  ../../baseline/logs/mkdocs-build-20250925T001535Z.log

## Status
Archived
