# Configuration

Autoresearch is configured via `autoresearch.toml` and environment variables in `.env`. Changes to these files are detected automatically while the tool is running and the configuration is hot reloaded. A sample configuration is provided under [`examples/autoresearch.toml`](../examples/autoresearch.toml).

## Example

```toml
[llm]
provider = "openai"
```

Common options include:

- `llm_backend` – which LLM adapter to use (`lmstudio`, `openai`, etc.).
- `loops` – number of reasoning cycles to run.
- `search_backends` – list of search providers.
- `tracing_enabled` – toggle OpenTelemetry tracing.
- `storage.duckdb.path` – path for the DuckDB database.

See `src/autoresearch/config.py` for all available options.

## Tracing

OpenTelemetry tracing is disabled by default. Enable it in `autoresearch.toml`:

```toml
[core]
tracing_enabled = true
```

The same option can be set via the environment variable
`CORE__TRACING_ENABLED=true`.
