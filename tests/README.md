# Test Suite

## Running integration tests

The integration suite exercises the CLI and API without contacting
external services. Run a fast subset with:

```bash
uv run pytest tests/integration -m 'not slow and not requires_ui and not requires_vss'
```

## Required services and data

- HTTP calls, including webhook notifications, are mocked using
  `pytest-httpx`; ensure the package is installed.
- Configuration tests write temporary TOML files via `tomli-w`.
- Baseline JSON files in `tests/integration/baselines/` hold expected
  metrics and token counts for comparison.
- Some tests rely on `owlrl` and `rdflib_sqlalchemy` for RDF reasoning and
  persistence; install these packages to avoid failures during integration runs.

No external databases or network services need to be running. Temporary
artifacts are created under `tmp_path` and cleaned automatically.

