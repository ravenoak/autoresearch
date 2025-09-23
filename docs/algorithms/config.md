# Configuration

## Overview

`ConfigLoader` merges `ConfigModel` defaults with TOML configuration files and
environment overrides. Profile overrides are applied last, and the loader
returns a fully validated `ConfigModel` that includes nested sections for
storage, search, API, distributed execution, and per agent overrides.

## Algorithm

1. Load `.env` values (if present) and process environment variables whose
   names are prefixed with `AUTORESEARCH_` or contain double underscores.
2. Expand these keys into nested dictionaries and merge them into the parsed
   `core` section from the first available config file.
3. Assemble nested sections (`StorageConfig`, `APIConfig`, `DistributedConfig`,
   `AnalysisConfig`) using `_safe_model`, which filters invalid fields while
   preserving valid ones.
4. Collect enabled agents, derive top level booleans such as `distributed`, and
   attach per agent overrides in `agent_config`.
5. Apply the selected profile, instantiate `ConfigModel.from_dict`, and cache
   the resulting model for reuse until the configuration changes.

## Proof sketch

Each layer overrides the previous one deterministically, so the final
configuration depends only on the ordered sources. `ConfigModel.from_dict`
ensures partially invalid settings degrade gracefully by retaining valid
fields, while validators enforce ranking weights, token budgets, and eviction
policies before returning control to callers.[p1]

## Simulation

- [Config weight and validator simulation][p1]
- [tests/unit/test_config_loader_defaults.py][t]

## References

- [code](../../src/autoresearch/config/)
- [spec](../specs/config.md)
- [tests](../../tests/unit/test_config_loader_defaults.py)

## Related Issues

- [Resolve deprecation warnings in tests][issue]

[issue]: ../../issues/archive/resolve-deprecation-warnings-in-tests.md
[p1]: ../algorithms/config_weight_sum_simulation.md
[t]: ../../tests/unit/test_config_loader_defaults.py
