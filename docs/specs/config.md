# Config

## Overview

The `autoresearch.config` package loads runtime settings from TOML files and
environment overrides. `ConfigLoader` constructs a validated `ConfigModel`,
applies profile specific overrides, and optionally watches the inputs for hot
reloads. Validators ensure canonical values before configuration data reaches
other subsystems. See
[config hot reload](../algorithms/config_hot_reload.md) for timing and
concurrency guarantees.

## Models

### ContextAwareSearchConfig

- `enabled` toggles the context aware search pipeline. Query expansion, entity
  recognition, and topic modelling flags expose bounded float and integer
  fields with defaults matching `models.py`.
- History tracking stores at most `max_history_items` entries and weights prior
  interactions through `history_weight`.

### LocalFileConfig and LocalGitConfig

- `LocalFileConfig` records the root path and allowed extensions for file based
  retrieval.
- `LocalGitConfig` captures the repository path, tracked branches, and history
  depth for Git sources.

### SearchConfig

- Defaults to `backends=["serper"]` and leaves `embedding_backends` empty
  until configured.
- Limits retrieval through `max_results_per_query`, `max_workers`, and
  `http_pool_size`.
- Hybrid search controls (`hybrid_query`, `use_semantic_similarity`,
  `use_bm25`, `use_source_credibility`) gate ranking strategies.
- Ranking weights (`semantic_similarity_weight`, `bm25_weight`,
  `source_credibility_weight`) must stay non negative. The
  `_normalize_ranking_weights` validator rebases missing or zero entries to sum
  to `1.0`, and raises `ConfigError` when provided totals exceed one.[p1]
- Credibility heuristics use `domain_authority_factor` and
  `citation_count_factor`. Feedback support is toggled by `use_feedback` and
  weighted by `feedback_weight`.
- Nested models include `ContextAwareSearchConfig`, `LocalFileConfig`, and
  `LocalGitConfig` instances.

### StorageConfig

- Configures DuckDB path selection, vector extension enablement, and
  approximate nearest neighbour parameters (`hnsw_m`, `hnsw_ef_construction`,
  `hnsw_metric`, `hnsw_ef_search`, `hnsw_auto_tune`).
- Controls vector query behaviour with `vector_nprobe`, optional batch sizing,
  and optional timeouts.
- RDF stores define `rdf_backend`, `rdf_path`, and `ontology_reasoner`
  settings. Optional limits cover `ontology_reasoner_timeout` and
  `ontology_reasoner_max_triples`.
- Connection management uses `max_connections`. Secondary stores toggle Kuzu
  integration with `use_kuzu` and `kuzu_path`.
- `validate_rdf_backend` accepts only the backends enumerated in
  `validators.py`.

### AgentConfig

- Tracks per agent enablement and optional model overrides.

### APIConfig

- Lists webhook endpoints and handles timeout, retry, and backoff parameters.
- Authentication fields cover shared secrets (`api_key`), bearer tokens, and an
  optional `api_keys` to role mapping. Default `role_permissions` provide
  conservative access per role.
- `rate_limit` and `monitoring_enabled` govern API throttling and metrics
  exposure.

### DistributedConfig

- Stores distributed toggles (`enabled`), an optional Ray address, CPU budget,
  and broker information (`message_broker`, `broker_url`).

### AnalysisConfig

- Exposes a single `polars_enabled` flag for data analysis pipelines.

### ConfigModel

- Core runtime defaults include `backend`, `llm_backend`, `llm_pool_size`,
  `loops`, and `ram_budget_mb`. Missing `llm_backend` values inherit the
  selected `backend`.
- Token governance uses `token_budget`, `adaptive_max_factor`, and
  `adaptive_min_buffer`. Validators coerce numeric strings and reject
  non positive limits.[p1]
- Reliability controls include `circuit_breaker_threshold`,
  `circuit_breaker_cooldown`, and `max_errors`.
- Agent orchestration tracks `agents`, `primus_start`, `default_model`,
  `enable_agent_messages`, `enable_feedback`, `coalitions`, and the
  `graph_eviction_policy`, which normalises friendly names to canonical
  tokens.[p1]
- Reasoning and formatting settings cover `reasoning_mode`, `output_format`,
  `tracing_enabled`, `monitor_interval`, and CPU or memory warning and critical
  thresholds.
- Nested models embed `StorageConfig`, `SearchConfig`, `APIConfig`,
  `DistributedConfig`, and `AnalysisConfig`. Arbitrary JSON compatible entries
  flow through `user_preferences` and `agent_config` (keyed by agent name).
- `distributed` mirrors the distributed toggle, while `active_profile` stores
  the applied profile identifier.
- `SettingsConfigDict(extra="ignore")` drops unknown keys. `from_dict` applies
  the schema field by field when a bulk validation error occurs, preserving the
  valid subset of user supplied data.
- Field validators enforce reasoning mode membership, positive token budgets,
  and canonical eviction policies.

## Algorithms

### Singleton and lifecycle helpers

1. `ConfigLoader.__new__` returns a process wide singleton, unless a context
   specific loader is active in `_current_loader`.
2. `reset_instance` stops any watcher threads, clears the cached loader, and
   resets the context variable so tests start from a clean state.
3. `new_for_tests` builds an isolated loader with optional search or `.env`
   paths, registers it in `_current_loader`, and returns it to callers.
4. `temporary_instance` yields a fresh loader inside a context manager and
   restores the singleton afterwards.
5. Instances support context manager usage (`__enter__`, `__exit__`) and a
   `close` method that stops watchers before clearing the cached configuration.
6. The `config` property lazily loads and memoises a `ConfigModel` via
   `load_config`.

### load_config

1. Read key value pairs from `.env` (when present) and the process environment.
   Keys prefixed with `AUTORESEARCH_` or containing `__` expand into nested
   dictionaries.
2. Search `search_paths` (defaulting to `autoresearch.toml` and
   `config/autoresearch.toml`) for the first existing file. When found, record
   its modification time and parse it with `tomllib`. Parsing failures raise
   `ConfigError` with the source path.
3. Merge environment overrides into the `core` section. If `backend` is set and
   `llm_backend` is missing, copy the backend value.
4. Assemble `StorageConfig` settings from `storage.duckdb`, `storage.rdf`, and
   top level `storage` keys. Apply environment overrides for the `storage`
   namespace.
5. Extract API, distributed, analysis, user preference, and agent dictionaries
   from the parsed file. A helper `_safe_model` instantiates each nested model
   and filters out invalid fields when validation errors occur.
6. Collect enabled agent names to seed the `agents` list and build an
   `agent_config` mapping of `AgentConfig` instances.
7. When `distributed.enabled` exists, propagate its boolean into the top level
   `distributed` field so callers can check a single flag.
8. Store declared profiles and apply the active profile. If the requested name
   is unknown, raise `ConfigError` listing valid choices. Applied profiles copy
   keys into the core settings and persist the selected name.
9. Construct and return `ConfigModel.from_dict(core_settings)`. This method
   preserves valid fields when the initial validation fails. Unexpected errors
   fall back to a default `ConfigModel` after logging.

### validate_config

- Invokes `load_config` and reports `(True, [])` for success. Validation or
  runtime failures return `(False, [error message])`.

### Observer management

- `register_observer` and `unregister_observer` manage a set of callbacks.
- `notify_observers` invokes each observer with the new `ConfigModel`. Raised
  exceptions are wrapped in `ConfigError` to avoid silent failures.

### watch_changes and watching

1. Optionally register an observer callback and bail out if a watcher thread is
   already running.
2. Collect existing config files and the `.env` path. Watch their parent
   directories with `watchfiles.watch`, and track the absolute paths that
   should trigger reloads.
3. Launch a daemon thread (`ConfigWatcher`) with a stop event. The first
   invocation registers an `atexit` hook to halt the watcher on process exit.
4. On relevant filesystem events, reload the configuration, replace the cached
   model, and notify observers. Reload errors raise `ConfigError`.
5. `stop_watching` sets the stop event, joins the thread, and logs shutdown. The
   `watching` context manager wraps `watch_changes` and ensures watchers stop on
   exit.

### set_active_profile and available_profiles

- `set_active_profile` loads profiles on demand, validates the requested name,
  clears the cached configuration, and notifies observers with the refreshed
  `ConfigModel`.
- `available_profiles` exposes the cached profile names, loading the
  configuration if necessary.

### temporary_config and get_config

1. `_current_config` stores per context overrides via `ContextVar`.
2. `temporary_config` sets a temporary `ConfigModel` inside a context manager
   and restores the previous state afterward.
3. `get_config` returns the current override when present, otherwise delegates
   to the singleton `ConfigLoader().config`.

## Validators

- `normalize_ranking_weights` fills missing ranking weights in proportion to
  defaults, rejects totals above `1.0`, and rebases zeroed configurations to an
  even split.[p1]
- `validate_rdf_backend` accepts only supported RDF backends and raises
  `ConfigError` with the allowed list on invalid input.
- `validate_reasoning_mode` normalises strings to lowercase before resolving
  them to `ReasoningMode` enums. Invalid values include the allowed set in the
  error payload.
- `validate_token_budget` coerces numeric strings to integers and rejects
  non positive or non integer values.[p1]
- `validate_eviction_policy` tolerates friendly casing and maps known strings to
  canonical policy tokens, raising `ConfigError` for unknown policies.[p1]

## Invariants

- `ConfigLoader` behaves as a singleton unless tests activate a temporary
  instance, ensuring deterministic state across the process.
- Environment overrides from `.env`, `AUTORESEARCH_*`, and double underscore
  keys apply to a copy of the parsed data and never mutate the raw TOML.
- `llm_backend` mirrors `backend` when no explicit model override is provided.
- Search ranking weights sum to `1.0`. Missing entries inherit proportional
  defaults and totals above `1.0` raise `ConfigError` before normalisation.[p1]
- Zeroed ranking weights rebalance to equal shares so hybrid search remains
  deterministic.[p1]
- Token budgets must be positive integers or omitted. Invalid entries raise
  `ConfigError` instead of being clamped.[p1]
- Graph eviction policies normalise to canonical identifiers before reaching
  downstream consumers.[p1]
- Observers always receive validated `ConfigModel` instances. Exceptions bubble
  up as `ConfigError` to prevent silent failures.
- Watch threads honour the stop event and join cleanly when `stop_watching` or
  `close` runs.

## Proof Sketch

`ConfigLoader` parses candidate configurations into dictionaries, merges
environment overrides, and instantiates `ConfigModel.from_dict`. The helper
retains validated fields even if some entries fail, preventing partial writes
from breaking the active state. Watchers reload into temporary objects before
swapping the cached reference, so observers only see validated models. The
validators enforce token budgets, ranking weights, RDF engines, and eviction
policies before data reaches other modules.

## Simulation Expectations

- [Config weight and validator simulation][p1] demonstrates ranking weights,
  eviction policy canonicalisation, and token budget guards across reloads.
- Hot reload simulations track watcher notifications in
  [config_hot_reload_metrics.json][r1], confirming observers receive each update
  exactly once.

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
