# CLI Helpers

Utility functions in `cli_helpers` keep the command interface friendly.

## Similar command suggestion
- `find_similar_commands` uses `difflib.get_close_matches` to propose up to
  three alternatives.
- Complexity: `O(n * m)` where `n` is the number of commands and `m` the
  length of the command name.

## Agent group parsing
- `parse_agent_groups` splits comma-separated strings and trims whitespace.
- Complexity is `O(k)` for `k` characters across all groups.

## Missing table reporting
- `report_missing_tables` sorts table names and prints guidance to the
  console.

## Command not found handling
- `handle_command_not_found` collects available commands, suggests similar
  ones, and exits with code `1`.

## References
- [`cli_helpers.py`](../../src/autoresearch/cli_helpers.py)
