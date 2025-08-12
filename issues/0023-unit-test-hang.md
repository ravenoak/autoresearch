# Issue 23: Unit test suite hangs during verification

Running `task verify` triggers `uv run pytest tests/unit --cov=src --cov-report=term-missing --cov-append`.
The test suite progresses to about 42% and then stalls indefinitely. Manual interruption shows the process still running.

## Context
`task verify` is part of the standard development workflow. The hang prevents complete verification and suggests a problematic test or dependency.

## Acceptance Criteria
- Identify the test or dependency causing the hang.
- Ensure `task verify` completes within a reasonable time (under 5 minutes).
- Update documentation or configuration as needed to prevent recurrence.

## Status
Open

## Related
- #22
