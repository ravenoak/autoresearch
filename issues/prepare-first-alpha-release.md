# Prepare first alpha release

## Context

The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only.
Sourcing the PATH helper emitted by `./scripts/setup.sh --print-path` keeps
`task --version` at 3.45.4, and the `task check` bootstrap reconfirms Python
3.12.10 plus the expected development tooling before halting in `flake8`
because `src/autoresearch/api/routing.py` still assigns an unused `e` variable
and `src/autoresearch/search/storage.py` imports `StorageError` without using
it. 【744f05†L1-L7】【152f28†L1-L2】【48cdde†L1-L25】【910056†L1-L9】【cd3ade†L1-L3】
`uv run python scripts/lint_specs.py` already succeeds and
`docs/specs/monitor.md` plus `docs/specs/extensions.md` retain the required
`## Simulation Expectations` heading, so the spec-driven baseline remains
intact. 【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` finishes
with 136 passed, 2 skipped, 822 deselected, and 1 xfailed tests, confirming the
storage teardown fixes hold. 【714199†L1-L2】 Documentation builds now emit a
warning because `docs/testing_guidelines.md` links to `../wheels/gpu/README.md`
outside MkDocs' tree, so the release plan must include cleaning up that
reference. 【9eabf1†L1-L6】【F:docs/testing_guidelines.md†L90-L102】 All GitHub
Actions workflows remain `workflow_dispatch` only.
【F:.github/workflows/ci.yml†L1-L22】【F:.github/workflows/ranking-benchmark.yml†L1-L14】
【F:.github/workflows/release-images.yml†L1-L14】
`SPEC_COVERAGE.md` continues to map each module to specifications plus proofs,
simulations, or tests, so every component still aligns with the project's
spec-first mandate ahead of the release. 【F:SPEC_COVERAGE.md†L1-L120】 The
remaining work involves closing the lint regression, validating the resource
tracker tear-down under warnings-as-errors, hardening the deprecation sweep,
refreshing coverage with optional extras, and repairing the MkDocs warning
before drafting release notes and tagging v0.1.0a1.

### PR-sized tasks

- **Clear lint regressions** – Resolve
  `autoresearch/api/routing.py`'s unused `e` variable and the dead
  `StorageError` import so `task check` passes again.
  ([clean-up-flake8-regressions-in-routing-and-search-storage](clean-up-flake8-regressions-in-routing-and-search-storage.md))
- **Verify resource tracker teardown** – Re-run `task verify` (ideally with
  `PYTHONWARNINGS=error::DeprecationWarning`) to ensure the multiprocessing
  shutdown path remains stable.
  ([resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md))
- **Harden warnings-as-errors harness** – Implement the multi-PR remediation
  plan to capture deprecations, refactor callers, and pin or filter remaining
  warnings so future runs stay clean.
  ([resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md))
- **Refresh coverage with optional extras** – Execute
  `task coverage EXTRAS="nlp ui vss git distributed analysis llm parsers gpu"`
  once the suite passes and update `baseline/coverage.xml` plus docs status.
  ([rerun-task-coverage-after-storage-fix](rerun-task-coverage-after-storage-fix.md))
- **Repair MkDocs GPU wheels link** – Update the testing guidelines so
  `uv run --extra docs mkdocs build` completes without warnings.
  ([fix-testing-guidelines-gpu-link](fix-testing-guidelines-gpu-link.md))
- **Stage release artifacts** – Draft CHANGELOG.md notes, confirm packaging
  metadata, and plan the `v0.1.0a1` tag once the above tickets land.

## Dependencies

- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [rerun-task-coverage-after-storage-fix](rerun-task-coverage-after-storage-fix.md)
- [clean-up-flake8-regressions-in-routing-and-search-storage](clean-up-flake8-regressions-in-routing-and-search-storage.md)
- [fix-testing-guidelines-gpu-link](fix-testing-guidelines-gpu-link.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- `task docs` (or `uv run --extra docs mkdocs build`) completes after docs
  extras sync.
- Workflows remain manual or dispatch-only.

## Status
Open
