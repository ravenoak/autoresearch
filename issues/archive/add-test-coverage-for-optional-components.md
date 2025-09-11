# Add test coverage for optional components

## Context
Current coverage only reflects a small targeted subset of tests.
Integration, behavior, and feature-specific suites that rely on optional
extras such as `[nlp]`, `[ui]`, and `[vss]` remain unexecuted. Without
exercising these paths, regressions may slip into optional modules and
overall coverage stays far below the 90% project goal.

The August 31, 2025 coverage run failed during unit tests, so suites using
optional extras never executed. On September 9, 2025, `uv run --extra test
pytest` reports 33 failing tests, primarily in authentication modules,
preventing full coverage measurement. Optional extras remain untested
and coverage sits near 32%.

## Dependencies
None.

## Acceptance Criteria
- Enable running tests that require each optional extra (`[nlp]`, `[ui]`,
  `[vss]`, `[git]`, `[distributed]`, `[analysis]`, `[llm]`, `[parsers]`).
- Expand behavior and integration suites to cover optional components.
- `task verify` executes all marked tests without timeouts.
- Line coverage reaches at least 90% when all extras are installed.

## Status
Archived
