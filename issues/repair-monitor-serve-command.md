# Repair monitor serve command

## Context
Unit tests `tests/unit/test_main_monitor_commands.py::test_serve_a2a_command`
and `tests/unit/test_main_monitor_commands.py::test_serve_a2a_command_keyboard_interrupt`
fail, showing the monitor CLI `serve` subcommand exits with a non-zero status and
mishandles interrupts.

## Acceptance Criteria
- `serve` subcommand exits with status 0 when run normally.
- `serve` subcommand handles keyboard interrupts gracefully.
- `tests/unit/test_main_monitor_commands.py` passes.
- Documentation describes the `monitor serve` workflow.

## Status
Open
