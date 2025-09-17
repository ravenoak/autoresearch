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
the original warning. We still need an end-to-end `task verify` run with Go
Task installed to confirm the absence of warnings across the full suite, but
`uv run pytest tests/unit -q` now fails in teardown when monitor CLI metrics
tests patch `ConfigLoader.load_config` to return `type("C", (), {})()`. The
autouse `cleanup_storage` fixture raises `AttributeError: 'C' object has no
attribute 'storage'`, so the suite aborts before we can rerun the warnings
sweep under Task. 【d541c6†L1-L58】【35a0a9†L63-L73】

## Dependencies
None

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings, including a
  `task verify` run with `PYTHONWARNINGS=error::DeprecationWarning`.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
