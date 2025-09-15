# Cli Helpers

## Overview

Utility helpers shared by CLI entry points. They provide fuzzy matching for
commands, parse agent group arguments, enforce API headers, and surface storage
state warnings with consistent Rich output.

## Algorithms

### find_similar_commands

1. Call `difflib.get_close_matches` with a maximum of three suggestions and a
   configurable cutoff.
2. Return the matches as a list to keep the API stable for tests.

### parse_agent_groups

1. Split each string on commas.
2. Strip whitespace and discard empty agent names.
3. Append only non-empty groups to preserve input ordering.

### require_api_key

1. Check for an `X-API-Key` header in the provided mapping.
2. Raise `HTTPException(status_code=401)` with a `WWW-Authenticate: API-Key`
   header when missing.
3. Return `None` when the header is present.

### report_missing_tables

1. Exit immediately when the input sequence is empty.
2. Sort table names, join them with commas, and render either to the provided
   `Console` or through `print_error` with a suggestion.

### handle_command_not_found

1. Emit a formatted error for the unknown command.
2. Collect subcommand names from the active Click/Typer context.
3. Suggest similar commands via `find_similar_commands` and show examples.
4. Raise `typer.Exit(code=1)` to stop execution.

## Invariants

- `find_similar_commands` never returns more than three suggestions and respects
  the cutoff threshold.
- `parse_agent_groups` returns only non-empty, trimmed agent names and preserves
  original ordering.
- `require_api_key` always raises `HTTPException` with a `WWW-Authenticate`
  header when the key is missing.
- `report_missing_tables` sorts table names consistently and never emits output
  when the input is empty.
- `handle_command_not_found` always raises `typer.Exit` after printing
  suggestions (when any).

## Complexity

- `find_similar_commands`: `O(n × m)` for `n` command strings of length `m`.
- `parse_agent_groups`: `O(k)` for `k` characters across the inputs.
- `require_api_key`: `O(1)` key lookup.

## Proof Sketch

- Python's `difflib` enforces the upper bound on matches, guaranteeing the
  invariant for `find_similar_commands`.
- `parse_agent_groups` filters falsy values before appending, so empty groups
  are impossible.
- `require_api_key` checks a single dictionary key and raises immediately,
  ensuring no downstream code executes without credentials.
- `report_missing_tables` shares the same branch regardless of whether a
  `Console` is supplied, keeping messages deterministic.
- `handle_command_not_found` finishes by raising `typer.Exit`, preventing the
  CLI from continuing in an invalid state.

## Simulation Expectations

Unit tests cover threshold handling, group parsing edge cases, missing header
errors, sorted table reporting, and friendly suggestions for mistyped
commands.

## Traceability

- Modules
  - [src/autoresearch/cli_helpers.py][m1]
- Tests
  - [tests/unit/test_cli_helpers.py][t1]

[m1]: ../../src/autoresearch/cli_helpers.py
[t1]: ../../tests/unit/test_cli_helpers.py
