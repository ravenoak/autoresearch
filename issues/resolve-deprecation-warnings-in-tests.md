# Resolve deprecation warnings in tests

## Context
Recent test runs emitted deprecation warnings from packages such as Click and
fastembed. The `weasel.util.config` module used to trigger a warning because it
imported `click.parser.split_arg_string`, which will move in Click 9.0. These
warnings may become errors in future releases and obscure test output.

`rdflib_sqlalchemy` warnings were eliminated on September 13, 2025 by switching
to `oxrdflib`.

On September 17, 2025, targeted retries with
`PYTHONWARNINGS=error::DeprecationWarning`
showed no remaining warnings in the CLI helper suite or distributed perf
comparison test. The `sitecustomize.py` shim that rewrites
`weasel.util.config` appears to be working, and the Click bump to 8.2.1 removed
the original warning. After resyncing the `dev-minimal`, `test`, and `docs`
extras, `uv run python scripts/check_env.py` in a fresh container now flags the
Go Task CLI plus unsynced development and test tooling (e.g., `black`,
`flake8`, `fakeredis`, `hypothesis`) until `task install` or `uv sync` installs
the extras. 【cd57a1†L1-L24】 The storage teardown regression is fixed—the patched
monitor metrics test now passes—so the unit suite advances to the storage
eviction simulation. 【04f707†L1-L3】 `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` currently fails at
`tests/unit/test_storage_eviction_sim.py::test_under_budget_keeps_nodes`
because `_enforce_ram_budget` prunes nodes even when the mocked RAM usage stays
within the budget. 【d7c968†L1-L164】 We must repair that regression and restore
the Task CLI before rerunning the warnings sweep under Task with
`PYTHONWARNINGS=error::DeprecationWarning`. Without the `[test]` extras Pytest
also emits `PytestConfigWarning: Unknown config option: bdd_features_base_dir`
during the storage simulations, so ensuring the extras are installed is part of
the cleanup. 【fa283d†L43-L53】

## Dependencies
- [fix-storage-eviction-under-budget-regression](fix-storage-eviction-under-budget-regression.md)

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings, including a
  `task verify` run with `PYTHONWARNINGS=error::DeprecationWarning`.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
