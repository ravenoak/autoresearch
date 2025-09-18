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
extras, `uv run python scripts/check_env.py` now reports the expected toolchain
when executed via `uv`, but the base shell still lacks the Task CLI.
【55fd29†L1-L18】【cb3edc†L1-L10】【8a589e†L1-L2】 The storage eviction regression is
fixed—`uv run --extra test pytest tests/unit/test_storage_eviction_sim.py -q`
passes—but the broader `uv run --extra test pytest tests/unit -k "storage" -q
--maxfail=1` invocation aborts with a segmentation fault in
`tests/unit/test_storage_manager_concurrency.py::test_setup_thread_safe`.
We must harden the threaded setup path and restore the Task CLI before rerunning
the warnings sweep under Task with `PYTHONWARNINGS=error::DeprecationWarning`.
Without the `[test]` extras Pytest still emits
`PytestConfigWarning: Unknown config option: bdd_features_base_dir` during the
storage simulations, so ensuring the extras are installed remains part of the
cleanup. 【0fcfb0†L1-L74】【3c1010†L1-L2】

## Dependencies
- [address-storage-setup-concurrency-crash](address-storage-setup-concurrency-crash.md)

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings, including a
  `task verify` run with `PYTHONWARNINGS=error::DeprecationWarning`.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
