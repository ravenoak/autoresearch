# Issue 23: Unit test suite hangs during verification

Running `task verify` triggers `uv run pytest tests/unit --cov=src --cov-report=term-missing --cov-append`.
The test suite progresses to about 42% and then stalls indefinitely. Manual interruption shows the process still running.

## Context
`task verify` is part of the standard development workflow. The hang prevents complete verification and suggests a problematic test or dependency.

Recent runs show the suite pausing during `test_ram_eviction`, which imports
heavy packages such as `bertopic`, `umap`, and `numba` via `search.context`.
These imports trigger just-in-time compilation and can take several minutes,
leading to the perceived hang.

### Latest observation

After commits 4e955dc and 7e0da5c introduced lazy imports, `task verify`
now runs to completion but takes ~12 minutes and fails
`tests/unit/test_monitor_cli.py::test_monitor_prompts_and_passes_callbacks`
(exit code 1). The hang is eliminated, but runtime exceeds the 5-minute
target.

## Acceptance Criteria
- Identify the test or dependency causing the hang.
- Ensure `task verify` completes within a reasonable time (under 5 minutes).
- Update documentation or configuration as needed to prevent recurrence.

## Status
Closed – Stubbed heavy topic-model dependencies and fixed monitor CLI
callbacks to prevent non-zero exits. `task verify` now finishes in about
four minutes without hanging or failing tests.

This resolves the prolonged runtime.

## Related
- #22
- #26
