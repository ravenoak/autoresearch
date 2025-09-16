# CLI Helpers

## Overview

Utility helpers shared by CLI entry points. They provide fuzzy matching for
commands (default similarity cutoff ``0.6``), parse agent group arguments,
enforce API headers, and surface storage state warnings with consistent Rich
output.

## Algorithms

### find_similar_commands

1. Call `difflib.get_close_matches` with up to three suggestions, a configurable
   cutoff, and the default threshold ``0.6`` when callers omit it.
2. Return the matches as a list to keep the API stable for CLI consumers and
   tests.

### parse_agent_groups

1. Split each string on commas.
2. Strip whitespace, discard empty agent names, and preserve group ordering.
3. Append only non-empty groups so the caller receives concrete team
   assignments and maintains the original ordering of group entries.

### require_api_key

1. Check for an `X-API-Key` header in the provided mapping.
2. Raise `HTTPException(status_code=401)` with a `detail` of `"Missing API key"`
   and a `WWW-Authenticate: API-Key` header when the key is absent.
3. Return `None` without side effects when the header is present.

### report_missing_tables

1. Exit immediately when the input sequence is empty.
2. Sort table names, join them with commas, and render either to the provided
   `Console` (including a yellow "Suggestion" line) or through `print_error`
   with the same schema initialization guidance.

### handle_command_not_found

1. Emit a formatted error for the unknown command via `print_error`.
2. Collect subcommand names from the active Click/Typer context.
3. Suggest similar commands via `find_similar_commands`, announce them with
   `print_info(symbol=False)` when any exist, and display each example through
   `print_command_example`.
4. Raise `typer.Exit(code=1)` after printing the `typer.secho` help hint
   "Run 'autoresearch --help' to see all available commands." to stop
   execution.

## Invariants

- `find_similar_commands` never returns more than three suggestions and respects
  the cutoff threshold.
- `parse_agent_groups` returns only non-empty, trimmed agent names and preserves
  original ordering.
- `require_api_key` always raises `HTTPException` with the documented detail and
  header when the key is missing.
- `require_api_key` performs no work when the header is present, ensuring
  idempotent authorization checks.
- `report_missing_tables` sorts table names consistently and never emits output
  when the input is empty.
- `handle_command_not_found` always raises `typer.Exit` after printing
  suggestions (when any) and the canonical help reminder.

## Complexity

- `find_similar_commands`: `O(n × m)` for `n` command strings of length `m`.
- `parse_agent_groups`: `O(k)` for `k` characters across the inputs.
- `require_api_key`: `O(1)` key lookup.

## Proof Sketch

- Python's `difflib` enforces the upper bound on matches, guaranteeing the
  invariant for `find_similar_commands`.
- A signature-level test verifies the default `threshold=0.6` contract for
  `find_similar_commands`.
- `parse_agent_groups` filters falsy values before appending, so empty groups
  are impossible.
- `require_api_key` checks a single dictionary key and raises immediately,
  ensuring no downstream code executes without credentials.
- `report_missing_tables` shares the same guidance regardless of whether a
  `Console` is supplied, keeping messages deterministic.
- `handle_command_not_found` finishes by raising `typer.Exit`, preventing the
  CLI from continuing in an invalid state.

## Simulation Expectations

Unit tests cover signature defaults, threshold handling, group parsing edge
cases, missing header errors, sorted table reporting, and friendly suggestions
for mistyped commands.

## Proof Obligations

- `find_similar_commands` and `parse_agent_groups` behaviors are asserted in
  fuzziness and parsing tests within [tests/unit/test_cli_helpers.py][t1].
- `require_api_key` guard rails are verified through missing and present header
  simulations in [tests/unit/test_cli_helpers.py][t1].
- `report_missing_tables` rendering paths and `handle_command_not_found`
  suggestion flows are exercised end-to-end in
  [tests/unit/test_cli_helpers.py][t1].

## Traceability

- Modules
  - [src/autoresearch/cli_helpers.py][m1]
- Tests
  - [tests/unit/test_cli_helpers.py][t1]

[m1]: ../../src/autoresearch/cli_helpers.py
[t1]: ../../tests/unit/test_cli_helpers.py
