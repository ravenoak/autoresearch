# Resolve deprecation warnings in tests

## Context
Recent test runs emit numerous deprecation warnings from packages such as
RDFlib SQLAlchemy, Click, and fastembed. These warnings may become errors in
future releases and obscure test output.

## Dependencies
None

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
