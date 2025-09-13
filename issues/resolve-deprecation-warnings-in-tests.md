# Resolve deprecation warnings in tests

## Context
Recent test runs emit numerous deprecation warnings from packages such as
RDFlib SQLAlchemy, Click, and fastembed. These warnings may become errors in
future releases and obscure test output.

The September 13, 2025 `task verify` run surfaced `RemovedIn20Warning` messages
from `rdflib_sqlalchemy` during cache tests, underscoring the need to update or
pin dependencies to supported versions.

## Dependencies
None

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
