# Warnings Baseline Logs

This directory stores the timestamped output from `task verify:warnings:log`,
which wraps `task verify:warnings` and records the full stdout/stderr stream for
later triage.

## Refreshing the baseline on a clean environment

1. Remove the existing virtual environment to avoid stale packages:
   `rm -rf .venv`.
2. Recreate the environment with the frozen lockfile and required extras:
   `uv sync --frozen --extra dev-minimal --extra test`.
3. Capture the latest warnings run:
   `task verify:warnings:log`.

The wrapper streams output to the terminal while archiving it under
`baseline/logs/verify-warnings-YYYYMMDDTHHMMSSZ.log`. The exit code matches the
underlying `task verify:warnings` invocation, so CI will still fail if warnings
cause the run to abort.

## Interpreting the archived logs

- Each log preserves ordering across stdout and stderr, making it safe to diff
  runs over time or search for repeated failure signatures.
- Look for `DeprecationWarning`, `FAILED`, `ERROR`, and pytest summary blocks to
  assign owners for follow-up work.
- When a warning is resolved, keep the historical log but update
  `issues/resolve-deprecation-warnings-in-tests.md` with the new status so the
  remediation plan stays current.
