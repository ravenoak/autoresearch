# Improve test coverage and streamline dependencies

## Context
Current `task install` completes with minimal dependencies, but `task verify`
fails due to `flake8` errors, preventing `coverage html` from running to
identify low-coverage modules. The existing baseline at
`baseline/coverage.xml` shows roughly twenty-two percent coverage, leaving most
modules untested.

## Acceptance Criteria
- `task install` completes without heavyweight GPU or ML dependencies by
default.
- `task verify` and `coverage html` run to completion on a fresh clone.
- Unit tests in `tests/unit` cover previously untested modules.
- Integration and behavior scenarios exercise uncovered workflows.
- `baseline/coverage.xml` updates once overall coverage meets at least ninety
percent.

## Status
Open
