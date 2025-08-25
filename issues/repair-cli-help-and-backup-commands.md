# Repair CLI help and backup commands

## Context
Several unit tests under `tests/unit/test_cli_help.py` and `tests/unit/test_main_backup_commands.py`
fail with exit code 1. Help text misses options such as `--interactive`, `--visualize`, `--loops`,
and `--ontology`. Backup subcommands cannot create, list, restore, schedule, or recover backups
without raising errors.

## Acceptance Criteria
- CLI help lists interactive, visualize, loops, ontology, and layout flags.
- Backup commands handle create, list, restore, schedule, recover, and keyboard interrupts.
- `tests/unit/test_cli_help.py` and `tests/unit/test_main_backup_commands.py` pass.

## Status
Open
