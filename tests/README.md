# Test Suite

## Running integration tests

The integration suite exercises the CLI and API without contacting
external services. Run a fast subset with:

```bash
uv run pytest tests/integration -m 'not slow'
```

Tests marked `requires_ui`, `requires_vss`, or `requires_distributed` skip
unless their respective extras are installed.

## Required services and data

- HTTP calls, including webhook notifications, are mocked using
  `pytest-httpx`; ensure the package is installed.
- Configuration tests write temporary TOML files via `tomli-w`.
- Baseline JSON files in `tests/integration/baselines/` hold expected
  metrics and token counts for comparison.
- Some tests rely on `owlrl` and `oxrdflib` for RDF reasoning and
  persistence. Ensure `oxrdflib` is installed for persistent RDF storage.
- Fixtures such as `example_autoresearch_toml` and `example_env_file` provide
  temporary configuration and environment data. Use `tmp_path` and
  `monkeypatch` to isolate side effects in tests.
- Redis-backed scenarios use the `requires_distributed` marker. The
  `redis_client` fixture connects to a local server or spins up a
  lightweight `fakeredis` instance. Tests skip when neither service is
  available or the `.[distributed]` extra is missing.
- Tests tagged `requires_vss` depend on the DuckDB VSS extension but fall back
  to a stub implementation when the `vss` extra is not installed.

No external databases or network services need to be running. Temporary
artifacts are created under `tmp_path` and cleaned automatically.

