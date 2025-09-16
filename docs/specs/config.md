# Config

## Overview

Configuration loading and hot-reload utilities for Autoresearch. `ConfigLoader`
locates configuration files, merges environment overrides (including `.env`
values), instantiates `ConfigModel`, and optionally watches files for changes.
Helper APIs expose the active configuration, temporary overrides, and profile
management. See [config hot reload](../algorithms/config_hot_reload.md) for the
underlying watcher model.

## Models

### ConfigModel

- Pydantic container for runtime switches such as `backend`, `llm_backend`,
  token budgeting, tracing flags, and agent orchestration parameters.
- Wraps nested models (`StorageConfig`, `SearchConfig`, `APIConfig`,
  `DistributedConfig`, `AnalysisConfig`) and per-agent overrides via
  `agent_config`.
- Applies validators that canonicalise `graph_eviction_policy`, enforce
  positive `token_budget` values, and convert string reasoning modes before
  instances are exposed to callers.
- Stores observer hooks, profile selection, and monitoring thresholds while
  ignoring extra keys through `SettingsConfigDict(extra="ignore")`.

### SearchConfig

- Chooses backends, embedding providers, result limits, and concurrency
  controls for retrieval.
- Coordinates hybrid ranking via `semantic_similarity_weight`,
  `bm25_weight`, and `source_credibility_weight`. Missing weights inherit
  defaults, and `_normalize_ranking_weights` ensures they remain positive and
  sum to `1.0`, raising `ConfigError` when user supplied totals exceed one.
- Provides toggles for user feedback, search history, and context awareness.
  `ContextAwareSearchConfig` tunes expansion, entity recognition, and topic
  modelling weights while respecting per-field bounds.
- `LocalFileConfig` and `LocalGitConfig` capture connector specific paths,
  extensions, and history depth.

### StorageConfig

- Describes DuckDB index options, vector extension availability, RDF store
  settings, and ontology reasoning limits.
- `validate_rdf_backend` constrains `rdf_backend` to supported engines and
  surfaces actionable errors when misconfigured.

### AgentConfig and APIConfig

- `AgentConfig` records enablement and per-agent model overrides.
- `APIConfig` manages webhook addresses, authentication, rate limits, and role
  permissions for HTTP exposure.

### DistributedConfig and AnalysisConfig

- `DistributedConfig` toggles Ray based execution, broker selection, and worker
  counts for distributed runs.
- `AnalysisConfig` currently advertises whether Polars based pipelines are
  enabled.

## Algorithms

### load_config

1. Collect variables from `.env`, OS environment, and prefixed keys such as
   `AUTORESEARCH_*` or `section__nested` pairs.
2. Search `autoresearch.toml`, `config/autoresearch.toml`, or supplied paths
   for the first existing configuration file.
3. Parse TOML content, logging errors via `ConfigError`.
4. Merge environment overrides into the parsed structure, expanding storage,
   API, distributed, analysis, and agent sections.
5. Instantiate nested models and validators, collecting valid values even when
   some fields fail validation.
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

## Validators

- `normalize_ranking_weights` renormalises ranking weights, fills unspecified
  fields in proportion to defaults, and rejects totals above `1.0`.
- `validate_rdf_backend` restricts storage engines to known RDF backends.
- `validate_reasoning_mode` lowercases or casts inputs into `ReasoningMode`
  enumerations, reporting invalid strings.
- `validate_token_budget` coerces numeric strings, rejects non-integer values,
  and raises when non-positive limits are supplied.
- `validate_eviction_policy` accepts friendly names, normalises case, and maps
  them to canonical graph eviction policy tokens.

## Invariants

- `ConfigLoader` behaves as a process-wide singleton unless `new_for_tests` or
  `temporary_instance` is used, ensuring consistent state during normal
  operation.
- Environment variables override file values without mutating the original
  parsed dictionary.
- Search ranking weights always sum to `1.0`, missing entries inherit defaults,
  and totals above `1.0` raise `ConfigError` before normalization.[p1]
- Zeroed ranking weights rebalance to equal shares so hybrid search remains
  deterministic.[p1]
- Token budgets must be positive integers or omitted; non-positive or malformed
  values surface `ConfigError` instead of clipping silently.[p1]
- Graph eviction policies are validated and case-normalised so downstream
  components receive canonical identifiers.[p1]
- Observer notifications always receive validated `ConfigModel` instances.
- Watch threads stop cleanly and clear `app.state.watch_ctx` during shutdown.
- Active profiles inherit base settings and only override declared keys.

## Proof Sketch

`ConfigLoader` adheres to the atomic reload guarantees outlined in
[config hot reload](../algorithms/config_hot_reload.md). Parsing occurs before
state swaps, observers run after validation, and context overrides ensure
callers within `temporary_config` observe a consistent snapshot. Validators on
`ConfigModel` and `SearchConfig` enforce canonical states prior to publishing
updates, preventing downstream drift.

## Simulation Expectations

- [Config weight and validator simulation][p1] demonstrates ranking weight,
  eviction policy, and token budget invariants remain enforced across
  configuration reloads.
- Hot-reload simulations toggle configuration values and record transitions in
  [config_hot_reload_metrics.json][r1], verifying that observers receive updated
  state exactly once per change.

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
- Proofs and simulations
  - [tests/analysis/config_hot_reload_metrics.json][r1]
  - [docs/algorithms/config_weight_sum_simulation.md][p1]

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
[p1]: ../algorithms/config_weight_sum_simulation.md
