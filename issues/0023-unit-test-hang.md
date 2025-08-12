# Issue 23: Unit test suite hangs during verification

Running `task verify` triggers `uv run pytest tests/unit --cov=src --cov-report=term-missing --cov-append`.
The test suite progresses to about 42% and then stalls indefinitely. Manual interruption shows the process still running.

## Context
`task verify` is part of the standard development workflow. The hang prevents complete verification and suggests a problematic test or dependency.

Recent runs show the suite pausing during `test_ram_eviction`, which imports
heavy packages such as `bertopic`, `umap`, and `numba` via `search.context`.
These imports trigger just-in-time compilation and can take several minutes,
leading to the perceived hang.

## Acceptance Criteria
- Identify the test or dependency causing the hang.
- Ensure `task verify` completes within a reasonable time (under 5 minutes).
- Update documentation or configuration as needed to prevent recurrence.

## Status
Open

## Related
- #22
