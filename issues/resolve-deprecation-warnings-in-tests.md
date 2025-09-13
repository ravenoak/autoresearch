# Resolve deprecation warnings in tests

## Context
Recent test runs emit deprecation warnings from packages such as Click and
fastembed. The `weasel.util.config` module triggers a warning because it imports
`click.parser.split_arg_string`, which will move in Click 9.0. These warnings may
become errors in future releases and obscure test output.

`rdflib_sqlalchemy` warnings were eliminated on September 13, 2025 by switching
to `oxrdflib`.

## Dependencies
None

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
