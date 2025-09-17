# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-17 the Go Task CLI is still absent in a fresh environment, so running
`uv run task check` fails until contributors install Task manually. Targeted
search and extension suites now pass:
`uv run --extra test pytest`
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::`
`test_load_extension_download_unhandled_exception -q` succeeds, and
`tests/unit/search/test_ranking_formula.py::`
`test_rank_results_weighted_combination` exercises the documented convex
weights without raising `ConfigError`. However, running
`uv run --extra test pytest tests/unit -q` now fails during collection because
`scripts/distributed_coordination_sim.py` no longer exports
`elect_leader` or `process_messages`, so the distributed coordination
properties cannot import the reference helpers. `uv run mkdocs build` still
fails because docs extras are not present, and the missing Task CLI prevents
`task check`/`task verify` from running end-to-end. These gaps block the
release checklist and require targeted fixes before we can draft reliable
release notes.

Running `uv sync --extra dev-minimal --extra test` followed by
`uv run python scripts/check_env.py` now reports only the missing Go Task CLI
in the evaluation container. 【024fb5†L1-L13】【f56f62†L1-L24】 Targeted unit and
integration checks continue to pass where helpers exist:
`tests/unit/test_config_validation_errors.py::test_weights_must_sum_to_one`,
`tests/unit/test_vss_extension_loader.py::TestVSSExtensionLoader::
test_load_extension_download_unhandled_exception`,
`tests/unit/search/test_ranking_formula.py::test_rank_results_weighted_combination`,
`tests/integration/test_ranking_formula_consistency.py`, and
`tests/integration/test_optional_extras.py` all succeed with the `[test]`
extras installed. 【127cf4†L1-L3】【af6378†L1-L2】【75e1fd†L1-L2】【50b44e†L1-L2】
【7a8f55†L1-L2】 Full unit collection still aborts with ImportError until the
distributed simulation exports return, and `uv run mkdocs build` continues to
fail because `mkdocs` is not on the PATH in a minimal environment.
【b4944c†L1-L23】【6bcbaa†L1-L3】 These regressions remain the final blockers
before we can draft changelog entries and cut the first alpha tag.

## Dependencies
- [restore-distributed-coordination-simulation-exports](
  restore-distributed-coordination-simulation-exports.md)
- [resolve-resource-tracker-errors-in-verify](
  resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](
  resolve-deprecation-warnings-in-tests.md)
- [document-docs-build-prerequisites](document-docs-build-prerequisites.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- Workflows remain manual or dispatch-only.

## Status
Open
