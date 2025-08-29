# Resolve release blockers for alpha

## Context
`task check` and `task verify` now pass after dependency retention and coverage
validation were addressed. The Codex setup script still needs to ensure `pytest`,
`pytest-bdd`, `freezegun`, and `hypothesis` install automatically, and
`.venv/bin/activate` must expose `task` without manual steps. Integration and
behavior suites remain largely untested. These gaps block tagging **0.1.0a1**
and can be addressed in parallel while other feature issues progress.

## Dependencies
- [add-orchestration-proofs-and-tests](add-orchestration-proofs-and-tests.md)
- [add-storage-proofs-and-simulations](add-storage-proofs-and-simulations.md)
- [fix-duckdb-schema-initialization](archive/fix-duckdb-schema-initialization.md)
- [configure-redis-service-for-tests](configure-redis-service-for-tests.md)
- [improve-test-coverage-and-streamline-dependencies](
  archive/improve-test-coverage-and-streamline-dependencies.md)
- [plan-a2a-mcp-behavior-tests](archive/plan-a2a-mcp-behavior-tests.md)
- [speed-up-task-check-and-reduce-dependency-footprint](
  speed-up-task-check-and-reduce-dependency-footprint.md)
- [document-task-cli-requirement](archive/document-task-cli-requirement.md)
- [handle-duckdb-extension-download-errors](archive/handle-duckdb-extension-download-errors.md)

## Acceptance Criteria
- `scripts/codex_setup.sh` installs and verifies `pytest`, `pytest-bdd`,
  `freezegun`, and `hypothesis` without manual intervention.
- `task check` completes without reinstalling removed test dependencies.
- `task verify` succeeds on a fresh clone by including `pdfminer.six` and
  `python-docx` in the appropriate extras.
- `STATUS.md` reflects the passing `task check` output and targeted tests.
- `check_coverage_docs.py` passes after syncing coverage numbers.
- Dry-run publish to TestPyPI succeeds.
- Release notes describe remaining known limitations before tagging **0.1.0a1**.

## Status
Open
