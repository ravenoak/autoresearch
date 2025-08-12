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

`task verify` was re-run on the current environment and again stalled at
42% for several minutes before being manually interrupted. The long pause
occurs while `narwhals` and other transitive dependencies are imported via
`bertopic`, suggesting the heavy import chain remains unresolved.

Potential approaches include marking the affected test as `slow`, lazily
importing the topic-modelling stack, or isolating the dependency behind a
feature flag so that the majority of the unit suite can complete quickly.

## Acceptance Criteria
- Identify the test or dependency causing the hang.
- Ensure `task verify` completes within a reasonable time (under 5 minutes).
- Update documentation or configuration as needed to prevent recurrence.

## Status
Open

## Related
- #22
