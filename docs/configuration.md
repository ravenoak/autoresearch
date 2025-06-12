# Configuration

Autoresearch is configured via `autoresearch.toml` and environment variables in `.env`. Changes to these files are detected automatically while the tool is running and the configuration is hot reloaded.

## Example

```toml
[llm]
provider = "openai"
```

See `src/autoresearch/config.py` for all available options.

## Tracing

OpenTelemetry tracing is disabled by default. Enable it in `autoresearch.toml`:

```toml
[core]
tracing_enabled = true
```

The same option can be set via the environment variable
`CORE__TRACING_ENABLED=true`.
