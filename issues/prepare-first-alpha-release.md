# Prepare first alpha release

## Context

The project remains unreleased even though the codebase and documentation are
public, so tagging v0.1.0a1 still needs a coordinated push across testing,
documentation, and packaging while workflows stay dispatch-only.
The September 23 `task verify` baseline shows the suite passing while five
tests marked `xfail` reported XPASS—`tests/unit/test_distributed_executors.py::test_execute_agent_remote`,
`tests/unit/test_metrics_token_budget_spec.py::test_convergence_bound_holds`,
`tests/unit/test_ranking_idempotence.py::test_rank_results_idempotent`,
`tests/unit/test_relevance_ranking.py::test_calculate_semantic_similarity`, and
`tests/unit/test_relevance_ranking.py::test_external_lookup_uses_cache`—so those
guards must be retired before the release can fail fast on regressions.
【F:baseline/logs/task-verify-20250923T204732Z.log†L342-L343】【F:baseline/logs/task-verify-20250923T204732Z.log†L557-L558】
【F:baseline/logs/task-verify-20250923T204732Z.log†L721-L721】【F:baseline/logs/task-verify-20250923T204732Z.log†L736-L737】
【F:baseline/logs/task-verify-20250923T204732Z.log†L747-L748】 The follow-on
`task verify:warnings` run captured on September 23 completed cleanly, giving a
warnings-as-errors baseline with coverage, token-usage, and documentation checks
finishing without failures while optional extras remain manual-only.
【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1-L44】【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1749-L1786】
`SPEC_COVERAGE.md` continues to map each module to specifications plus proofs,
simulations, or tests, so every component still aligns with the project's
spec-first mandate ahead of the release.【F:SPEC_COVERAGE.md†L1-L125】 With those
baselines recorded, the remaining work centers on promoting the five XPASS cases
and staging release artifacts—dry-run builds, changelog notes, and tag
preparation—before drafting release notes and cutting v0.1.0a1.
【F:docs/release_plan.md†L95-L109】【F:.github/workflows/ci.yml†L1-L22】

### PR-sized tasks

- **Retire stale xfail markers** – Promote the five XPASS cases in the unit
  suite so release verification runs fail fast when regressions reappear.
  ([retire-stale-xfail-markers-in-unit-suite](retire-stale-xfail-markers-in-unit-suite.md))
- ✅ **Refresh warnings-as-errors coverage** – Completed with the September 23
  `task verify:warnings` run; keep
  `baseline/logs/verify-warnings-20250923T224648Z.log` as the
  `PYTHONWARNINGS=error::DeprecationWarning` reference when optional extras
  change.【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1-L44】【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1749-L1786】
- **Stage release artifacts** – Draft CHANGELOG.md notes, confirm packaging
  metadata with dry-run builds, and line up the `v0.1.0a1` tag plan once the
  XPASS removals and documentation updates land.【F:docs/release_plan.md†L95-L109】【F:CHANGELOG.md†L1-L200】

## Dependencies

- [retire-stale-xfail-markers-in-unit-suite](retire-stale-xfail-markers-in-unit-suite.md)

## Acceptance Criteria
- All dependency issues, including
  [retire-stale-xfail-markers-in-unit-suite](retire-stale-xfail-markers-in-unit-suite.md),
  are closed.
- The "Prerequisites for tagging 0.1.0a1" in `docs/release_plan.md` are
  satisfied before tagging.【F:docs/release_plan.md†L66-L91】
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.【F:CHANGELOG.md†L1-L200】
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- `task docs` (or `uv run --extra docs mkdocs build`) completes after docs
  extras sync.
- Workflows remain manual or dispatch-only.【F:.github/workflows/ci.yml†L1-L22】

## Status
Open
