# CLI Backup

Typer commands for managing storage backups.

## Validation
- `_validate_dir` ensures a path exists or can be created.
- `_validate_file` confirms backup paths point to files.

## Commands
- `backup_create` writes backups with optional compression and limits.
- `backup_restore` confirms and restores selected backups.
- `backup_list` shows available backups in a table.
- `backup_schedule` runs periodic backups until interrupted.
- `backup_recover` performs point-in-time recovery.

## References
- [`cli_backup.py`](../../src/autoresearch/cli_backup.py)
- [../specs/cli-backup.md](../specs/cli-backup.md)

## Simulation

Automated tests confirm cli backup behavior.

- [Spec](../specs/cli-backup.md)
- [Tests](../../tests/targeted/test_cli_backup_validation.py)
