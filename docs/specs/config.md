# Config

## Overview

Configuration loading and hot-reload utilities for Autoresearch. `ConfigLoader`
locates configuration files, merges environment overrides (including `.env`
values), instantiates `ConfigModel`, and optionally watches files for changes.
Helper APIs expose the active configuration, temporary overrides, and profile
management. See [config hot reload](../algorithms/config_hot_reload.md) for the
underlying watcher model.

## Algorithms

### load_config

1. Collect variables from `.env`, OS environment, and prefixed keys such as
   `AUTORESEARCH_*` or `section__nested` pairs.
2. Search `autoresearch.toml`, `config/autoresearch.toml`, or supplied paths
   for the first existing configuration file.
3. Parse TOML content, logging errors via `ConfigError`.
4. Merge environment overrides into the parsed structure, expanding storage,
   API, distributed, analysis, and agent sections.
5. Instantiate `AgentConfig` entries, collecting valid values even when some
   fields fail validation.
6. Apply active profile overrides when `profiles.<name>` exists in the file or
   was previously selected with `set_active_profile`.
7. Create and return a `ConfigModel`; on validation failure, log the error and
   fall back to defaults.

### watch_changes / watching

1. Determine which configuration and `.env` paths exist and monitor their parent
   directories with `watchfiles.watch`.
2. Spawn a daemon thread that reloads the configuration when a watched file
   changes.
3. Update `self._config` with the fresh `ConfigModel` and notify registered
   observers.
4. Stop the watcher when the context manager exits or `stop_watching` is
   invoked.

### register_observer / notify_observers

1. Maintain a set of callables registered by clients.
2. On reload, call each observer with the new `ConfigModel` and surface
   exceptions as `ConfigError` to avoid silent failures.

### set_active_profile

1. Ensure profiles are loaded (calling `load_config` if necessary).
2. Validate that the requested profile exists; raise `ConfigError` with
   suggestions when unknown.
3. Record the active profile, invalidate cached configuration, and notify
   observers with the new `ConfigModel`.

### temporary_config / get_config

1. Use a `contextvars.ContextVar` to store a temporary configuration override.
2. `temporary_config` sets the variable for the duration of the context manager
   and restores the previous state on exit.
3. `get_config` returns the context override when present, otherwise defers to
   the singleton `ConfigLoader().config`.

## Invariants

- `ConfigLoader` behaves as a process-wide singleton unless `new_for_tests` or
  `temporary_instance` is used, ensuring consistent state during normal
  operation.
- Environment variables override file values without mutating the original
  parsed dictionary.
- Relevance ranking weights must not exceed a combined value of 1.0; a
  `ConfigError` is raised when overweight vectors are provided instead of
  silently renormalising them.
- Observer notifications always receive validated `ConfigModel` instances.
- Watch threads stop cleanly and clear `app.state.watch_ctx` during shutdown.
- Active profiles inherit base settings and only override declared keys.

## Proof Sketch

`ConfigLoader` adheres to the atomic reload guarantees outlined in
[config hot reload](../algorithms/config_hot_reload.md). Parsing occurs before
state swaps, observers run after validation, and context overrides ensure
callers within `temporary_config` observe a consistent snapshot. Tests cover
error handling, defaults, environment overrides, and watcher cleanup, providing
empirical confirmation of the invariants.

## Simulation Expectations

Hot-reload simulations toggle configuration values and record transitions from 1
to 2 in [config_hot_reload_metrics.json][r1], verifying that observers receive
updated state exactly once per change. Analysis tests exercise watcher threads
and ensure missing files fall back to defaults without crashing the process.

## Traceability

- Modules
  - [src/autoresearch/config/__init__.py][m1]
  - [src/autoresearch/config/loader.py][m2]
  - [src/autoresearch/config/models.py][m3]
  - [src/autoresearch/config/validators.py][m4]
- Tests
  - [tests/unit/test_config_env_file.py][t1]
  - [tests/unit/test_config_errors.py][t2]
  - [tests/unit/test_config_loader_defaults.py][t3]
  - [tests/unit/test_config_profiles.py][t4]
  - [tests/unit/test_config_reload.py][t5]
  - [tests/unit/test_config_validation_errors.py][t6]
  - [tests/unit/test_config_watcher_cleanup.py][t7]
  - [tests/behavior/features/configuration_hot_reload.feature][t8]
  - [tests/integration/test_config_hot_reload_components.py][t9]
  - [tests/analysis/test_config_hot_reload_sim.py][t10]

[m1]: ../../src/autoresearch/config/__init__.py
[m2]: ../../src/autoresearch/config/loader.py
[m3]: ../../src/autoresearch/config/models.py
[m4]: ../../src/autoresearch/config/validators.py
[t1]: ../../tests/unit/test_config_env_file.py
[t2]: ../../tests/unit/test_config_errors.py
[t3]: ../../tests/unit/test_config_loader_defaults.py
[t4]: ../../tests/unit/test_config_profiles.py
[t5]: ../../tests/unit/test_config_reload.py
[t6]: ../../tests/unit/test_config_validation_errors.py
[t7]: ../../tests/unit/test_config_watcher_cleanup.py
[t8]: ../../tests/behavior/features/configuration_hot_reload.feature
[t9]: ../../tests/integration/test_config_hot_reload_components.py
[t10]: ../../tests/analysis/test_config_hot_reload_sim.py
[r1]: ../../tests/analysis/config_hot_reload_metrics.json
