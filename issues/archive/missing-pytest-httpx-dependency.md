# Missing pytest-httpx dependency in test environment

## Context
- Running `task verify` fails with `ModuleNotFoundError: No module named 'pytest_httpx'`.
- Environment setup instructions expect dev dependencies like `pytest-httpx` to be installed.
- Lack of this dependency prevents unit tests from running.

## Acceptance Criteria
- `pytest_httpx` is installed in the development environment.
- `task verify` proceeds past dependency installation and runs tests.
- Documentation and setup scripts remain in sync regarding required dev dependencies.

## Status
Archived
