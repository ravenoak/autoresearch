# Config Utils

Autoresearch uses configuration utilities to manage runtime settings.

- Validation: configurations are checked against Pydantic schema before use.
- Hot reload: file watcher reloads `autoresearch.toml` when it changes.
- Schema guarantees: presets and environment variables resolve to the
  `ConfigModel` schema, preventing invalid keys.

See also: [../specs/config-utils.md](../specs/config-utils.md).

## Simulation

Automated tests confirm config utils behavior.

- [Spec](../specs/config-utils.md)
- [Tests](../../tests/unit/test_config_reload.py)
