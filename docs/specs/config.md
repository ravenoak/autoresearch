# Config

## Overview

Specification for config module. See [config hot reload
algorithm](../algorithms/config_hot_reload.md) for reload behavior.

## Algorithms

- Implement core behaviors described above.

## Invariants

- ``state.active`` equals the last successfully parsed config file.
- Reloads are atomic; readers never observe partially written state.
- Unknown or malformed fields leave prior values unchanged.

## Proof Sketch

Reload simulations show configuration updates occur atomically and preserve
prior values.

## Proof Steps

1. Write baseline configuration and capture active state.
2. Modify the file and trigger a reload.
3. Compare active state to modified file; ensure unmodified fields persist.
4. Confirm metrics in [config_hot_reload_metrics.json][r1] report success.

## Simulation Expectations

Unit and behavior tests cover nominal and edge cases for these routines.
The hot-reload simulation validates these invariants by updating a config
value from 1 to 2 and recording metrics in [config_hot_reload_metrics.json][r1].
The watcher logs an error and keeps the previous configuration active when a
source file is removed.

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
