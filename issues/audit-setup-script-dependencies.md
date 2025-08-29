# Audit setup script dependencies

## Context
Setup scripts install different extras, leading to divergent environments and
missing packages. A comprehensive inventory is needed to ensure `scripts/setup.sh`
and the Codex bootstrap script install consistent dependency sets and record
DuckDB extension paths.

## Dependencies
- [synchronize-codex-and-generic-setup-scripts](synchronize-codex-and-generic-setup-scripts.md)
- [fix-task-check-dependency-removal-and-extension-bootstrap](archive/fix-task-check-dependency-removal-and-extension-bootstrap.md)

## Acceptance Criteria
- Enumerate all extras and optional dependencies in `pyproject.toml`.
- `scripts/setup.sh` and the Codex bootstrap script install the same extras for
  development and testing.
- Documentation outlines when to use each script and which extras they install.
- `scripts/check_env.py` passes after running either setup script.

## Status
Open
