# Retire stale xfail markers in unit suite

## Context
`uv run --extra test pytest tests/unit -m 'not slow' --maxfail=1 -rxX`
now reports XPASS for six tests that still carry `xfail` markers, five of
which exercise production paths that have stabilised in the Ray executor
and ranking pipelines. The September 23 verification log at
`baseline/logs/task-verify-20250923T204732Z.log` shows
`test_execute_agent_remote`, `test_convergence_bound_holds`,
`test_rank_results_idempotent`,
`test_calculate_semantic_similarity`, and
`test_external_lookup_uses_cache` all passing under the warnings-as-errors
harness. The remaining guard on
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

## Status
Open
