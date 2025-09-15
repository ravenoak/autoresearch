# Cli Helpers

## Overview

Small helper utilities used by the CLI for error handling and command
parsing.

## Algorithms

### find_similar_commands
1. Uses `difflib.get_close_matches` to compare the input command against a
   sequence of valid commands.
2. Returns up to three commands whose similarity ratio is above the
   threshold.

### parse_agent_groups
1. Split each group string on commas.
2. Trim whitespace from names and discard empty results.
3. Collect non-empty lists in input order.

### report_missing_tables
1. If the list is empty, exit early.
2. Sort table names and join with commas.
3. Print an error or send output to a provided console.

### handle_command_not_found
1. Emit an error noting the unknown command.
2. Gather available commands from the Click/Typer context.
3. Suggest similar commands using `find_similar_commands`.
4. Exit with code 1.

## Invariants

- `find_similar_commands` returns at most three entries and obeys the
  threshold.
- `parse_agent_groups` yields groups of non-empty, trimmed names in input
  order.
- `report_missing_tables` sorts table names and never emits output when none
  are missing.
- `handle_command_not_found` always raises `typer.Exit` and lists suggestions
  only when candidates exist.

## Complexity

- `find_similar_commands`: `O(n × m)` for `n` commands of length `m`.
- `parse_agent_groups`: `O(k)` for `k` characters across groups.

## Proof Sketch

- `find_similar_commands` delegates to Python's standard `difflib`, which
  bounds results and filters by similarity score.
- `parse_agent_groups` only appends lists that contain at least one name,
  ensuring no empty groups.
- `report_missing_tables` checks for falsy input and sorts names before
  formatting, guaranteeing stable output.
- `handle_command_not_found` raises `typer.Exit` after printing, so the CLI
  cannot continue in an invalid state.

## Simulation Expectations

Unit tests exercise threshold handling, empty group parsing, sorted table
reporting, and the single-execution contract for command dispatch errors.

## Traceability

- Modules
  - [src/autoresearch/cli_helpers.py][m1]
- Tests
  - [tests/unit/test_cli_helpers.py][t1]

[m1]: ../../src/autoresearch/cli_helpers.py
[t1]: ../../tests/unit/test_cli_helpers.py
