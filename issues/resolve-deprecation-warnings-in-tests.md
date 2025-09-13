# Resolve deprecation warnings in tests

## Context
Recent test runs emit numerous deprecation warnings from packages such as
Click and fastembed. Earlier runs also surfaced warnings from the deprecated
`rdflib_sqlalchemy` plugin, which has since been replaced with `oxrdflib`.
future releases and obscure test output.

The September 13, 2025 `task verify` run surfaced `RemovedIn20Warning` messages
from `rdflib_sqlalchemy` during cache tests, underscoring the need to update or
replace deprecated dependencies.

## Dependencies
None

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
