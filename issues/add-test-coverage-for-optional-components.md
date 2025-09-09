# Add test coverage for optional components

## Context
Current coverage only reflects a small targeted subset of tests.
Integration, behavior, and feature-specific suites that rely on optional
extras such as `[nlp]`, `[ui]`, and `[vss]` remain unexecuted. Without
exercising these paths, regressions may slip into optional modules and
overall coverage stays far below the 90% project goal.

The August 31, 2025 coverage run failed during unit tests, so suites using
optional extras never executed. On September 9, 2025, coverage remains
stuck at 32% because `task verify` fails early in
`tests/unit/test_cache.py::test_cache_is_backend_specific`.

## Dependencies
None.

## Acceptance Criteria
- Enable running tests that require each optional extra (`[nlp]`, `[ui]`,
  `[vss]`, `[git]`, `[distributed]`, `[analysis]`, `[llm]`, `[parsers]`).
- Expand behavior and integration suites to cover optional components.
- `task verify` executes all marked tests without timeouts.
- Line coverage reaches at least 90% when all extras are installed.

## Status
Open
