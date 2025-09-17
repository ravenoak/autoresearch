# Restore distributed coordination simulation exports

## Context
Running `uv run --extra test pytest tests/unit -q` on September 17, 2025
fails during collection because `scripts/distributed_coordination_sim.py`
no longer exports `elect_leader` or `process_messages`. Property-based tests
(`tests/unit/distributed/test_coordination_properties.py` and
`tests/unit/test_distributed_coordination_props.py`) import those helpers to
validate the leader election and message ordering proofs documented in
`docs/algorithms/distributed_coordination.md`. The specification still cites
this script as the reference implementation, so the missing exports break the
Doc/spec/test alignment and prevent `task verify` from running to completion.
Pytest now raises `ImportError: cannot import name 'elect_leader'` for both
distributed property suites, confirming the helpers must be reinstated before
`tests/unit` can collect. 【382418†L1-L23】【F:scripts/distributed_coordination_sim.py†L67-L200】【F:docs/algorithms/distributed_coordination.md†L66-L90】

## Dependencies
None.

## Acceptance Criteria
- Reintroduce `elect_leader` and `process_messages` in
  `scripts/distributed_coordination_sim.py` with implementations that match
  the formulas and invariants described in
  `docs/algorithms/distributed_coordination.md`.
- Update or add targeted unit tests if needed so the Hypothesis properties in
  `tests/unit/distributed/test_coordination_properties.py` and
  `tests/unit/test_distributed_coordination_props.py` pass with the `[test]`
  extras installed.
- Document the restored helpers or reference the relevant section in
  `docs/algorithms/distributed_coordination.md` so the specification and
  implementation remain synchronized.
- Confirm `uv run --extra test pytest tests/unit -q` completes without
  import errors in a fresh environment with the `[test]` extras.

## Status
Open
