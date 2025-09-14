# Main Entrypoints

## Overview
The main package exposes CLI commands for running orchestration tasks.

## Algorithm
It routes subcommands to handlers, initialising configuration and the
orchestrator before executing actions.

## Proof sketch
Argument parsing uses `argparse` which guarantees a finite parse tree, so
command dispatch terminates.

## Simulation
`tests/unit/test_main_cli.py` runs key commands and checks exit statuses.

## References
- [code](../../src/autoresearch/main/)
- [spec](../specs/main.md)
- [tests](../../tests/unit/test_main_cli.py)

## Related Issues
- [Prepare first alpha release][issue]

[issue]: ../../issues/prepare-first-alpha-release.md
