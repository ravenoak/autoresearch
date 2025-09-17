# Restore distributed coordination simulation exports

## Context
`scripts/distributed_coordination_sim.py` now exports `elect_leader` and
`process_messages`, and direct imports confirm the helpers follow the proof in
`docs/algorithms/distributed_coordination.md`.
【F:scripts/distributed_coordination_sim.py†L1-L200】【049a40†L1-L3】 The
storage teardown regression has been cleared—the patched
`ConfigLoader.load_config` scenario now passes—so the unit suite progresses
far enough to hit the storage eviction simulation. 【04f707†L1-L3】 The latest
run halts at `tests/unit/test_storage_eviction_sim.py::
test_under_budget_keeps_nodes`, where `_enforce_ram_budget` prunes nodes even
though the mocked RAM usage stays within budget. 【d7c968†L1-L164】 That failure
prevents the distributed property suite from executing during the targeted
`-k "storage"` run. A focused invocation of
`tests/unit/distributed/test_coordination_properties.py` still passes,
confirming the helpers behave as expected once the suite reaches them, so we
remain blocked only by the eviction regression. 【d3124a†L1-L2】

## Dependencies
- [fix-storage-eviction-under-budget-regression](
  fix-storage-eviction-under-budget-regression.md)

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
