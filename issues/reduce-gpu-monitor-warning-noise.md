# Reduce GPU monitor warning noise when dependencies are absent

## Context
Targeted storage tests emit `WARNING` logs from
`autoresearch.resource_monitor` whenever `pynvml` or `nvidia-smi` is
unavailable. Running
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1`
without the GPU extras shows repeated warnings even though GPU metrics are
optional for these suites. The noise obscures real failures while providing
little value for CPU-only environments. 【1ffd0e†L33-L54】

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
Open
