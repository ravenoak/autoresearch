# Prepare alpha release

## Context
The project targets an initial alpha release, but foundational pieces remain
incomplete. Environment reproducibility is fragile because setup details are
scattered. [docs/installation.md](../docs/installation.md) now provides the
canonical instructions. Tests are unstable and packaging steps lack
verification, so a consolidated plan is needed to coordinate these efforts.

## Milestone

- 0.1.0a1 (2026-03-01)

## Acceptance Criteria
- Record the following PR-sized tasks with linked issues and dependency notes:
  - Clarify environment bootstrap and make `docs/installation.md`
    the canonical reference (see `document-environment-bootstrap.md`).
  - Stabilize the integration test suite (see `stabilize-integration-tests.md`).
  - Verify packaging workflow and add fallback when DuckDB extensions cannot be
    downloaded (see `verify-packaging-workflow-and-duckdb-fallback.md`).
- Add coverage gates and regression checks in CI (see
  `add-coverage-gates-and-regression-checks.md`).
- Provide proofs or simulations for ranking algorithms and agent coordination
  (see `validate-ranking-algorithms-and-agent-coordination.md`).
- Ensure roadmap and release plan capture the updated sequencing and
  requirements.

## Dependencies

1. `document-environment-bootstrap.md` establishes the baseline setup.
2. `verify-packaging-workflow-and-duckdb-fallback.md` depends on the
   environment bootstrap.
3. `stabilize-integration-tests.md` follows packaging verification.
4. `add-coverage-gates-and-regression-checks.md` requires stable integration
   tests.
5. `validate-ranking-algorithms-and-agent-coordination.md` depends on coverage
   gates and integration tests.

## Status
Open
