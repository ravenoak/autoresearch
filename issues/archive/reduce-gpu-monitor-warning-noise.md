# Reduce GPU monitor warning noise when dependencies are absent

## Context
Targeted storage tests initially emitted `WARNING` logs from
`autoresearch.resource_monitor` whenever `pynvml` or `nvidia-smi` was
unavailable. Running
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1`
without the GPU extras showed repeated warnings even though GPU metrics were
optional for these suites. The noise obscured real failures while providing
little value for CPU-only environments.

The monitor now logs missing GPU dependencies at `INFO` when GPU extras are
absent, and `STATUS.md` records the quieter default. Storage runs therefore
avoid spurious warnings on CPU-only setups. 【F:src/autoresearch/resource_monitor.py†L1-L118】【F:STATUS.md†L560-L579】

## Dependencies
- None

## Acceptance Criteria
- Update GPU monitoring to downgrade missing dependency warnings to `INFO`
  (or suppress them entirely) when the GPU extras are not installed.
- Ensure storage-focused unit tests complete without emitting GPU warning
  noise on CPU-only environments.
- Document the expected behavior in STATUS.md or TASK_PROGRESS.md if GPU
  metrics remain optional.

## Status
Archived
