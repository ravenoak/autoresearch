# Errors

Unified error hierarchy with context-rich messages.

## Base class
- `AutoresearchError` records a message, cause, and extra context.

## Specialized errors
- `ConfigError`, `AgentError`, `LLMError`, `StorageError`,
  `SearchError`, `OrchestrationError`, `ValidationError`,
  `TimeoutError`, `NotFoundError`, and `BackupError` provide
  domain-specific details.

## Context formatting
- Extra keyword arguments appear in messages as key-value pairs.
- Exception chaining retains the original cause via `__cause__`.

## References
- [`errors.py`](../../src/autoresearch/errors.py)
- [../specs/errors.md](../specs/errors.md)

## Simulation

Automated tests confirm errors behavior.

- [Spec](../specs/errors.md)
- [Tests](../../tests/unit/test_config_validation_errors.py)
