# CLI Utils

Formatting helpers for command line output and queries.

## Verbosity
- `Verbosity` enum controls global output detail.
- Levels map to explicit priorities (`quiet` = 0, `normal` = 1, `verbose` = 2)
  so threshold comparisons use numeric ordering.
- `set_verbosity` syncs environment and global state.
- `print_error` honours the quiet threshold, while `print_warning` requires at
  least normal verbosity.

## Utilities
- `visualize_rdf_cli` renders knowledge graphs.
- `sparql_query_cli` runs SPARQL with optional reasoning.
- `visualize_query_cli` executes a query and saves an image.

## References
- [`cli_utils.py`](../../src/autoresearch/cli_utils.py)
- [../specs/cli-utils.md](../specs/cli-utils.md)

## Simulation

Automated tests confirm cli utils behavior.

- [Spec](../specs/cli-utils.md)
- [Tests](../../tests/unit/test_cli_utils_extra.py)
