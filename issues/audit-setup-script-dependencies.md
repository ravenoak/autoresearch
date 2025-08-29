# Audit setup script dependencies

## Context
Setup scripts install different extras, leading to divergent environments and
missing packages. A comprehensive inventory is needed to ensure `scripts/setup.sh`
and the Codex bootstrap script install consistent dependency sets and record
DuckDB extension paths.

**Extras inventory:** minimal, nlp, ui, vss, parsers, git, distributed, analysis,
llm, test, full, dev, dev-minimal, build. Both setup scripts install the `dev`
and `test` extras by default and accept additional extras via `AR_EXTRAS`. The
environment check now validates all packages from these development and test
extras.

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
