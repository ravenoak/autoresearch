# Fix config CLI command tests

## Context
`config` subcommands were initializing storage and tests used Click's runner, causing failures.

## Acceptance Criteria
- Config initialization and validation run without storage setup.
- Unit tests for config commands pass using Typer's `CliRunner`.

## Status
Archived
