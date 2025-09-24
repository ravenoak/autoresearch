# Stabilize storage eviction property

## Context
`tests/unit/test_storage_eviction.py::test_enforce_ram_budget_reduces_usage_property`
remains marked with `xfail` and still reports as XFAIL under the
September 24 run of `uv run --extra test pytest tests/unit -m "not slow"
-rxX`. The reason cites "Eviction property generation unstable" even
though `docs/algorithms/storage_eviction.md` presents a proof that the
RAM budget enforcement always terminates below the target threshold. The
implementation in `src/autoresearch/storage.py` recently added
`_enforce_ram_budget` guardrails for zero metrics, yet property-based
generation can still emit sequences that break the invariant.

A dialectical review must determine whether the proof requires refined
assumptions (for example, minimum node sizes) or if the algorithm needs
additional bookkeeping. Socratic probing of the counterexamples—such as
graphs with zero-weight nodes or repeated evictions of the same entity—
will surface the missing invariants before the release staging proceeds.

## Dependencies
- _None_

## Acceptance Criteria
- Reproduce and document the counterexample currently triggering the
  property `xfail`, linking the reasoning in
  `docs/algorithms/storage_eviction.md` and
  `docs/specs/storage.md`.
- Update `_enforce_ram_budget` (or related helpers) to address the
  counterexample, ensuring deterministic convergence under the stated
  assumptions.
- Strengthen `tests/unit/test_storage_eviction.py` with targeted fixtures
  or Hypothesis strategies and remove the `xfail` marker.
- Capture the resolution in `SPEC_COVERAGE.md` and summarize it in the
  Unreleased section of `CHANGELOG.md`.
- Add a regression scenario to `scripts/storage_eviction_sim.py` or a new
  simulation helper demonstrating the fixed invariant.

## Status
Open
