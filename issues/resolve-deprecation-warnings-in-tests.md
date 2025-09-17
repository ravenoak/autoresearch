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
`uv run --extra test pytest tests/unit -q` currently fails because
`scripts/distributed_coordination_sim.py` no longer exports the helpers that
the distributed property tests import. Once those exports return we can rerun
the warnings sweep under Task.

## Dependencies
None

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings, including a
  `task verify` run with `PYTHONWARNINGS=error::DeprecationWarning`.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
