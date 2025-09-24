# Stabilize ranking weight property

## Context
The unit suite still marks `tests/unit/test_property_search_ranking.py::
test_rank_results_orders_by_weighted_scores` with `xfail`, and the
September 24 run of `uv run --extra test pytest tests/unit -m "not slow"
-rxX` reports it as XFAIL alongside the XPASS for
`tests/unit/test_ranking_idempotence.py::test_rank_results_idempotent`.
The proof in `docs/algorithms/relevance_ranking.md` asserts that sorting
by the weighted score is idempotent, yet the property test covers the
same invariants and continues to fail intermittently. The implementation
in `src/autoresearch/search/core.py` still relies on floating point
comparisons without an explicit tie-breaker, so rankings with equal
scores can flip between runs.

We need a focused effort to reconcile the specification, tests, and
implementation. The dialectical review should question whether the proof
requires additional constraints (for example, stable sorting with a
secondary key) or if the production ranking must be hardened. A
Socratic walkthrough of the failure cases—especially ties where BM25 and
semantic scores cancel—will clarify the necessary correction before the
alpha release work moves forward.

## Dependencies
- _None_

## Acceptance Criteria
- Implement deterministic tie-breaking or score quantization in
  `src/autoresearch/search/core.py` so ranking outputs are stable across
  runs.
- Update `docs/algorithms/relevance_ranking.md` to incorporate the new
  assumptions or derivation and record the dialectical analysis that led
  to the change.
- Extend the regression coverage in
  `tests/unit/test_property_search_ranking.py` to capture the corrected
  behavior and remove the `xfail` marker.
- Sync `SPEC_COVERAGE.md` for the affected search modules to reference
  the refreshed proof or simulation artifacts.
- Note the stabilization in `CHANGELOG.md` under the Unreleased section.

## Resolution
- Reviewed the Unreleased changelog entries covering score quantization,
  deterministic tie-breaking, and overweight vector validation, which
  document the fixes closing this ticket.
- Confirmed `tests/unit/test_property_search_ranking.py` now exercises
  deterministic fixtures without an `xfail` marker and that
  `docs/algorithms/relevance_ranking.md` and `SPEC_COVERAGE.md` reflect
  the updated proof.
- No outstanding ranking regressions remain after dependent issues were
  archived alongside this change.

## Status
Archived
