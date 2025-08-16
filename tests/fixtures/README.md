# Fixture Usage

This directory provides reusable fixtures for building test contexts.

## Configuration helpers

- `config_loader` – returns a `ConfigLoader` backed by a minimal `autoresearch.toml`.
- `config` – loads the minimal configuration and patches required environment variables.
- `config_context` – writes a representative configuration file and sample
  data directory. The returned `ConfigContext` bundles the loader, loaded
  `ConfigModel`, and the data directory.

## Storage helpers

- `dummy_storage` – registers a minimal `autoresearch.storage` stub so tests
  can import the storage module without hitting real backends.

### Composing scenarios

Fixtures can be combined to craft richer test cases:

```python
def test_with_extra_data(config_context):
    cfg = config_context.config
    data_dir = config_context.data_dir
    (data_dir / "extra.txt").write_text("example")
    cfg.loops = 3
    # ... proceed with test using cfg and data_dir
```

Extend the `config_context` setup or modify the generated files to suit
complex testing needs.
