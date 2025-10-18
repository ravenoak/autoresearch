# Retire stale xfail markers in unit suite

## Context (Updated October 17, 2025)

**SIGNIFICANT PROGRESS MADE** - Empirical investigation shows substantial improvement:

**Previous State** (September 2025):
- 127 xfail/skip markers across 44 test files
- Multiple flaky tests blocking release verification

**Current State** (October 17, 2025):
- **35 xfail/skip markers** (74% reduction from 127)
- **Previously flaky tests now pass consistently**:
  - `test_execute_agent_remote` ✅ PASSED
  - `test_convergence_bound_holds` ✅ PASSED
  - `test_rank_results_idempotent` ✅ PASSED
  - `test_calculate_semantic_similarity` ✅ PASSED
  - `test_external_lookup_uses_cache` ✅ PASSED

**Empirical Verification:**
- Unit tests: 937 passed, 42 skipped, 25 deselected
- Integration tests: 350 passed, 20 skipped, 145 deselected
- Behavior tests: 41 passed, 215 skipped, 57 deselected The remaining guard on
`tests/unit/test_heuristic_properties.py::test_token_budget_monotonicity`
reflects an unresolved proof gap in
`autoresearch.orchestration.metrics` rather than an unstable runtime
path.

Dialectically, keeping the `xfail` markers hides true regressions and
masks coverage gaps; removing them without strengthening the surrounding
proofs risks enshrining brittle heuristics. A Socratic review of each
path—Ray serialization, ranking determinism, semantic similarity, cache
coherence, and token budgeting—should therefore drive the promotions.

## Dependencies
- [refresh-token-budget-monotonicity-proof.md]
  (refresh-token-budget-monotonicity-proof.md)
- [stabilize-ranking-weight-property.md]
  (stabilize-ranking-weight-property.md)
- [restore-external-lookup-search-flow.md]
  (restore-external-lookup-search-flow.md)

## Acceptance Criteria
- Remove or tighten the guard on
  `tests/unit/test_distributed_executors.py::test_execute_agent_remote` so
  it only triggers on genuine Ray serialization regressions, documenting
  the Ray path in `docs/algorithms/distributed.md` and
  `SPEC_COVERAGE.md`.
- Lift the `xfail` from
  `tests/unit/test_metrics_token_budget_spec.py::test_convergence_bound_holds`
  after aligning the proof, simulation, and implementation. Update
  `docs/algorithms/token_budgeting.md`, `docs/specs/metrics.md`, and
  `SPEC_COVERAGE.md` accordingly.
- Restore deterministic expectations for
  `tests/unit/test_ranking_idempotence.py::test_rank_results_idempotent`
  using the live ranking pipeline in `src/autoresearch/search/core.py`,
  updating `docs/algorithms/relevance_ranking.md`,
  `docs/algorithms/search.md`, and `SPEC_COVERAGE.md`.
- Ensure
  `tests/unit/test_relevance_ranking.py::test_calculate_semantic_similarity`
  executes the production scoring path without an `xfail`, recording the
  decision in `docs/algorithms/semantic_similarity.md` and
  `SPEC_COVERAGE.md`.
- Make
  `tests/unit/test_relevance_ranking.py::test_external_lookup_uses_cache`
  fast and reliable without `xfail`, documenting the cache behaviour in
  `docs/algorithms/search.md`, `docs/algorithms/cache.md`, and
  `SPEC_COVERAGE.md`.
- Keep the monotonicity guard in
  `tests/unit/test_heuristic_properties.py::test_token_budget_monotonicity`
  until the dependency issue lands, then convert it to a standard
  assertion and cite the refreshed proof.

## Resolution
- Cross-checked the Unreleased changelog entry documenting the retirement
  of search, distributed, and budgeting XFAIL markers. The references
  cover the Ray executor, ranking, semantic similarity, cache, and token
  budget updates that satisfy the acceptance criteria.
- Verified the suite no longer carries `xfail` markers for
  `tests/unit/test_distributed_executors.py`,
  `tests/unit/test_ranking_idempotence.py`,
  `tests/unit/test_relevance_ranking.py`, and
  `tests/unit/test_heuristic_properties.py`.
- With the dependent ranking, search, storage, and token budget tickets
  archived, no further follow-up remains.

## Status
Archived
