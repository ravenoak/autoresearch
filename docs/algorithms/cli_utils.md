# CLI Utils

Formatting helpers for command line output and queries.

## Verbosity
- `Verbosity` enum controls global output detail.
- `set_verbosity` syncs environment and global state.
- `print_*` helpers respect the active level.

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
