# Synchronize Codex and generic setup scripts

## Context
`scripts/codex_setup.sh` installs development dependencies for Codex, while
`scripts/setup.sh` targets generic environments. Missing parity between these
scripts leaves out testing tools such as `pytest-bdd`, `freezegun`, and
`hypothesis`, leading `task check` and `task verify` to fail on fresh clones.

## Dependencies
- [document-task-cli-requirement](document-task-cli-requirement.md)
- [resolve-release-blockers-for-alpha](resolve-release-blockers-for-alpha.md)

## Acceptance Criteria
- `scripts/codex_setup.sh` and `scripts/setup.sh` both install `pytest`,
  `pytest-bdd`, `freezegun`, and `hypothesis`.
- `task check` runs without reinstalling removed test packages after either
  setup script.
- Documentation clarifies which script to use for Codex versus general
  contributors.
- Setup scripts finish within ten minutes.

## Status
Open
