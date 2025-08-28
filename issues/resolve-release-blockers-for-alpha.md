# Resolve release blockers for alpha

## Context
`task check` passes after installing missing test dependencies, but the Codex
setup script fails to provision `pytest`, `pytest-bdd`, `freezegun`, and
`hypothesis` by default. `task verify` also halts because `pdfminer.six` and
`python-docx` are absent. These gaps block tagging **0.1.0a1** and can be
addressed in parallel while other feature issues progress.

## Dependencies
- [add-orchestration-proofs-and-tests](add-orchestration-proofs-and-tests.md)
- [add-storage-proofs-and-simulations](add-storage-proofs-and-simulations.md)
- [configure-redis-service-for-tests](configure-redis-service-for-tests.md)
- [improve-test-coverage-and-streamline-dependencies](
  improve-test-coverage-and-streamline-dependencies.md)
- [plan-a2a-mcp-behavior-tests](plan-a2a-mcp-behavior-tests.md)
- [speed-up-task-check-and-reduce-dependency-footprint](
  speed-up-task-check-and-reduce-dependency-footprint.md)

## Acceptance Criteria
- `scripts/codex_setup.sh` installs and verifies `pytest`, `pytest-bdd`,
  `freezegun`, and `hypothesis` without manual intervention.
- `task verify` succeeds on a fresh clone by including `pdfminer.six` and
  `python-docx` in the appropriate extras.
- `STATUS.md` reflects the passing `task check` output and targeted tests.
- Release notes describe remaining known limitations before tagging **0.1.0a1**.

## Status
Open
