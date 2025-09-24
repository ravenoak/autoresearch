# Refresh token budget monotonicity proof

## Context
The heuristics suite still marks
`tests/unit/test_heuristic_properties.py::test_token_budget_monotonicity`
with `xfail` even though `task verify` and the September 24 rerun of
`uv run --extra test pytest tests/unit -m "not slow" -rxX` now report the
case as XPASS.
The marker was introduced while we investigated non-monotonic updates in
`OrchestrationMetrics.suggest_token_budget`, so the remaining guard
blocks release gating from catching regressions early.
`docs/algorithms/token_budgeting.md` and `docs/specs/metrics.md`
already describe the convergence proof, yet neither document reconciles
the hypothesis counterexamples that originally justified the `xfail`.
The current behaviour appears to be *piecewise monotonic*: rounding and
the max-of-means derivation protect against budget collapse, but
short-term averages can still dip when a fresh spike pushes another
candidate out of the max window.

We therefore need to revisit the proof against actual code paths,
simulate the edge cases, and decide whether the heuristic should be
tightened or the specification amended. A Socratic review of the
derivation will let us contrast the original monotonicity claim with
observed behaviour, while the dialectical step requires challenging the
assumption that strict monotonicity is even appropriate for bursty
workloads.

## Dependencies
- [retire-stale-xfail-markers-in-unit-suite.md]
  (retire-stale-xfail-markers-in-unit-suite.md)

## Acceptance Criteria
- Reproduce the historical counterexample that motivated the `xfail` and
  document it in `docs/algorithms/token_budgeting.md` alongside the
  convergence proof. Highlight the assumptions that fail.
- Decide between tightening the heuristic or reframing the specification,
  for example by proving monotonicity under constrained margins, and
  record the dialectical reasoning in `docs/specs/metrics.md`.
- Add deterministic regression coverage in
  `tests/unit/test_heuristic_properties.py` (Hypothesis or targeted
  fixtures) so that XPASS promotions remain stable.
- Update `SPEC_COVERAGE.md` to map the refreshed proof or simulation to
  `autoresearch/orchestration/metrics.py`.
- Remove the `xfail` marker once the proof, simulation, and tests agree.
- Capture the result in `CHANGELOG.md` under the Unreleased section.

## Status
Open
