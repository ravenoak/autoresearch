# Retire stale xfail markers in unit suite

## Context
Running `uv run --extra test pytest tests/unit -m 'not slow' --maxfail=1 -rxX`
now reports six XPASS entries for tests that still carry `xfail` markers even
though their underlying behaviors succeed. The affected cases include the Ray
remote executor, token budget heuristics, metrics convergence bounds, ranking
idempotence, and two relevance-ranking helpers. 【ba4d58†L1-L104】 These tests
should either graduate to normal assertions with updated proofs and simulations
or regain a failure mode that justifies the `xfail` markers.

## Dependencies
- None

## Acceptance Criteria
- Remove or tighten the `xfail` on
  `tests/unit/test_distributed_executors.py::test_execute_agent_remote` so it
  only triggers when Ray serialization genuinely fails under Python 3.12.
- Promote `tests/unit/test_heuristic_properties.py::test_token_budget_monotonicity`
  to a normal test backed by heuristic proofs or document why the monotonicity
  guarantee must be relaxed.
- Update `tests/unit/test_metrics_token_budget_spec.py::test_convergence_bound_holds`
  so the convergence proof aligns with the current algorithm, keeping the test
  active without an `xfail` guard.
- Restore deterministic expectations for
  `tests/unit/test_ranking_idempotence.py::test_rank_results_idempotent` and
  remove its `xfail` marker.
- Ensure `tests/unit/test_relevance_ranking.py::test_calculate_semantic_similarity`
  exercises the real scoring implementation and no longer relies on an
  `xfail`.
- Make `tests/unit/test_relevance_ranking.py::test_external_lookup_uses_cache`
  fast and reliable so it runs without an `xfail` marker.
- Document the updated proofs, simulations, or benchmark data in
  `SPEC_COVERAGE.md` and linked specs where applicable.

## Status
Open
