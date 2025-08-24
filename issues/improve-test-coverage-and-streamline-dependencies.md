# Improve test coverage and streamline dependencies

## Context
Attempts to run `task install` and `task verify` stalled when large GPU and
machine learning packages like `torch` and CUDA began downloading. Without a
successful install, the test suite and `coverage html` could not run to
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
