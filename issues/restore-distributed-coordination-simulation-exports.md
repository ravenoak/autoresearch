# Restore distributed coordination simulation exports

## Context
`scripts/distributed_coordination_sim.py` now exports `elect_leader` and
`process_messages`, and direct imports confirm the helpers follow the proof in
`docs/algorithms/distributed_coordination.md`.
【F:scripts/distributed_coordination_sim.py†L1-L200】【049a40†L1-L3】 The unit
suite still fails before the property tests run because monitor CLI metrics
tests patch `ConfigLoader.load_config` to return `type("C", (), {})()`. The
autouse `cleanup_storage` fixture invokes `storage.teardown(remove_db=True)`
during teardown and raises `AttributeError: 'C' object has no attribute
'storage'`, so `uv run pytest tests/unit -q` aborts early and never reaches the
distributed scenarios. 【d541c6†L1-L58】【35a0a9†L63-L73】 We must keep this ticket
open until the storage teardown regression is resolved and the property suites
can execute again.

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
