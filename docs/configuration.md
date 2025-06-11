# Configuration

Autoresearch is configured via `autoresearch.toml` and environment variables in `.env`. Changes to these files are detected automatically while the tool is running and the configuration is hot reloaded.

## Example

```toml
[llm]
provider = "openai"
```

See `src/autoresearch/config.py` for all available options.
