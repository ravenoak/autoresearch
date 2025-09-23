# Restore spec lint template compliance

## Context
Running `task check` now fails during `lint-specs` because
`scripts/lint_specs.py` reports missing headings in
`docs/specs/monitor.md` and `docs/specs/extensions.md`. The monitor
spec labels its simulation section as "Simulation Evidence" instead of
"Simulation Expectations", while the extensions spec omits the
standard `## Algorithms`, `## Invariants`, `## Proof Sketch`, and
`## Simulation Expectations` headings that the lint tool enforces.
`task check` stops after these errors, so no tests or coverage commands
run until the spec documents are realigned with the template.
【4076c9†L1-L2】

Spec lint now passes: `uv run python scripts/lint_specs.py` returns
successfully and both `docs/specs/monitor.md` and
`docs/specs/extensions.md` include the required `## Simulation Expectations`
heading, clearing the gate that blocked `task check`.
【b7abba†L1-L1】【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】

## Dependencies
- None

## Acceptance Criteria
- `docs/specs/monitor.md` restores the required headings, including a
  `## Simulation Expectations` section that documents expected
  simulation inputs and outputs.
- `docs/specs/extensions.md` adopts the full spec template with
  `## Algorithms`, `## Invariants`, `## Proof Sketch`, and
  `## Simulation Expectations` headings populated with the existing
  offline-determinism content and any supporting formulas or decision
  tables.
- `uv run python scripts/lint_specs.py` and `task check` complete without spec
  lint failures.
- STATUS.md records the spec lint fix so the release log reflects the
  restored compliance.

## Status
Archived
