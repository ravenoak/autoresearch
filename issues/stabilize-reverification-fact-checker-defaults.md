# Stabilize reverification fact checker defaults

## Context
`uv run --extra test pytest` fails in
`tests/unit/orchestration/test_reverify.py::test_reverify_extracts_claims_and_retries`
with a `FactChecker` validation error. The reverification pipeline now
requires explicit configuration even in tests, so the suite blocks alpha
readiness until sensible defaults are restored.
【7be155†L104-L170】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- FactChecker defaults load without validation errors when reverification runs
  without explicit configuration.
- Unit and behavior tests covering reverification pass without fixture-specific
  overrides.
- Documentation summarises the new defaults in `docs/v0.1.0a1_preflight_plan.md`
  or successor release notes.

## Status
Resolved – defaults load without validation errors and opt-out is documented.

## Resolution
- Reverification builds FactChecker kwargs from `ConfigModel.verification` and
  injects deterministic defaults when missing.
- Setting `verification.fact_checker.enabled` to `false` now skips the loop,
  letting fixtures opt out without patching the agent.
- `docs/release_plan.md` records the configuration contract and test coverage
  was expanded in `tests/unit/orchestration/test_reverify.py`.
