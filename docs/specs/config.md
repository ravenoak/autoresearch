# Config

## Overview

Configuration loader for Autoresearch. It merges defaults, environment
variables, and profile files. See
[config hot reload algorithm](../algorithms/config_hot_reload.md) for reload
behavior.

## Algorithms

1. Read defaults and overlay environment variables and profile data.
2. Parse the active file into structured state.
3. Watch the file and atomically swap ``state.active`` on valid changes.

## Invariants

- ``state.active`` equals the last successfully parsed config file.
- Reloads are atomic; readers never observe partially written state.
- Unknown or malformed fields leave prior values unchanged.

## Proof Sketch

Reloading a modified file updates ``state.active`` atomically while preserving
unchanged fields. Tests exercise reload paths, and the simulation
increments a value from 1 to 2, recording metrics in
[config_hot_reload_metrics.json][r1] to verify success and fallback
behavior when files disappear.

## Simulation Expectations

The hot-reload simulation updates a value from 1 to 2 and records metrics in
[config_hot_reload_metrics.json][r1].

## Traceability


- Modules
  - [src/autoresearch/config/][m1]
- Tests
  - [tests/unit/test_config_env_file.py][t1]
  - [tests/unit/test_config_errors.py][t2]
  - [tests/unit/test_config_loader_defaults.py][t3]
  - [tests/behavior/features/configuration_hot_reload.feature][t4]
  - [tests/integration/test_config_hot_reload_components.py][t5]
  - [tests/analysis/test_config_hot_reload_sim.py][t6]

[m1]: ../../src/autoresearch/config/
[t1]: ../../tests/unit/test_config_env_file.py
[t2]: ../../tests/unit/test_config_errors.py
[t3]: ../../tests/unit/test_config_loader_defaults.py
[t4]: ../../tests/behavior/features/configuration_hot_reload.feature
[t5]: ../../tests/integration/test_config_hot_reload_components.py
[t6]: ../../tests/analysis/test_config_hot_reload_sim.py
[r1]: ../../tests/analysis/config_hot_reload_metrics.json
