# Fix task verify coverage hang

## Context
Recent attempts to run `task verify` stall during the coverage phase after
syncing all extras. Earlier runs halted around 26% of the unit suite with a
`KeyError` from the `tmp_path` fixture. On September 2, 2025, the command
still required manual interruption and exited with status 201 after
`tests/unit/distributed/test_coordination_properties.py::test_message_processing_is_idempotent`
triggered a `hypothesis.errors.DeadlineExceeded`. This prevents the project
from assessing overall test health before the 0.1.0a1 release.

On September 2, 2025, another run of `uv run task verify` hung during the
coverage task. The process produced no further output for several minutes and
was manually interrupted, leaving coverage reports incomplete.

On September 3, 2025, `task verify` again failed during coverage, raising a
`KeyError` from the `tmp_path` fixture before any report was generated. The
command required manual interruption.

In a fresh environment without the Go Task CLI, running
`uv run pytest tests/unit/test_version.py -q` raised
`ImportError: No module named 'pytest_bdd'`, showing the `[test]` extras were
missing and coverage could not start.
Invoking `uv run task check` on the same system failed with
`error: Failed to spawn: 'task'`, confirming the Go Task CLI was absent.

On September 3, 2025, running `task check` produced `error: unexpected argument '-' found`.
Exporting `.venv/bin` to `PATH` and executing `flake8`, `mypy`,
`scripts/check_spec_tests.py`, and `pytest -c /dev/null tests/unit/test_version.py
tests/unit/test_cli_help.py -q` succeeded, indicating the hang stems from the Taskfile layout
rather than test failures.

On September 5, 2025, running `task verify` after installing all extras produced no output
for several minutes during coverage.
The process was interrupted manually, exiting with status 2.

## Dependencies
None.

## Acceptance Criteria
- Identify the cause of the coverage hang during `task verify`.
- Ensure the coverage phase completes and produces reports without manual
  intervention.
- Document any new requirements or limitations in `STATUS.md`.

## Status
Open
