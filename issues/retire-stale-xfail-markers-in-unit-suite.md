# Retire stale xfail markers in unit suite

## Context
Running `uv run --extra test pytest tests/unit -m 'not slow' --maxfail=1 -rxX`
now reports six XPASS entries for tests that still carry `xfail` markers even
though their underlying behaviors succeed. Five of those cases—
`test_execute_agent_remote`, `test_convergence_bound_holds`,
`test_rank_results_idempotent`,
`test_calculate_semantic_similarity`, and
`test_external_lookup_uses_cache`—exercise stabilized implementations in the
Ray executor pipeline and ranking stack
(`src/autoresearch/distributed/executors.py`,
`src/autoresearch/search/core.py`). 【ba4d58†L1-L104】 The remaining marker on
`test_token_budget_monotonicity` still guards an unproven monotonicity claim
while `autoresearch.orchestration.metrics` awaits updated proofs and
simulations. These tests should either graduate to normal assertions with
updated documentation or regain a failure mode that justifies the `xfail`
markers.

## Dependencies
- None

## Acceptance Criteria
- Remove or tighten the `xfail` on
  `tests/unit/test_distributed_executors.py::test_execute_agent_remote` so it
  only fires on genuine Ray serialization regressions, documenting the Ray path
  maintained in `src/autoresearch/distributed/executors.py` within
  `SPEC_COVERAGE.md` and `docs/algorithms/distributed.md`.
- Retain the guard on
  `tests/unit/test_heuristic_properties.py::test_token_budget_monotonicity`
  until `autoresearch.orchestration.metrics` lands the refreshed monotonicity
  proof and the revisions propagate through
  `docs/algorithms/token_budgeting.md`, `docs/specs/metrics.md`, and
  `SPEC_COVERAGE.md`.
- Lift the `xfail` from
  `tests/unit/test_metrics_token_budget_spec.py::test_convergence_bound_holds`
  after synchronizing the convergence proof with the production algorithm and
  recording the change in `docs/algorithms/token_budgeting.md`,
  `docs/specs/metrics.md`, and `SPEC_COVERAGE.md`.
- Restore deterministic expectations for
  `tests/unit/test_ranking_idempotence.py::test_rank_results_idempotent` using
  the stabilized ranking pipeline in `src/autoresearch/search/core.py`, then
  update `docs/algorithms/relevance_ranking.md`, `docs/algorithms/search.md`,
  and `SPEC_COVERAGE.md` to reflect the live check.
- Ensure
  `tests/unit/test_relevance_ranking.py::test_calculate_semantic_similarity`
  exercises the production scoring path from
  `src/autoresearch/search/core.py` without an `xfail`, updating
  `docs/algorithms/semantic_similarity.md` and `SPEC_COVERAGE.md` once the
  guard is removed.
- Make `tests/unit/test_relevance_ranking.py::test_external_lookup_uses_cache`
  fast and reliable without an `xfail` marker, capturing the cache behavior in
  `docs/algorithms/search.md`, `docs/algorithms/cache.md`, and
  `SPEC_COVERAGE.md`.

## Status
Open
