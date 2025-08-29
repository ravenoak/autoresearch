# Config Utils

Configuration utilities validate settings, support hot reload, and
enforce schema guarantees so downstream components receive consistent
state.

## Validation

The utilities wrap the loader in error handling and surface validation
errors with clear messages. Values are checked against the
`ConfigModel` before activation.

## Hot Reload

Watchers monitor configuration sources and trigger a reload when files
change. New snapshots replace the current configuration only after they
pass validation, ensuring uninterrupted operation.

## Schema Guarantees

The utilities rely on `ConfigModel` to provide a stable schema.
Consumers can rely on typed attributes even as the configuration
changes at runtime.
