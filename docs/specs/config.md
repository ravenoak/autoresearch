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

Reloading a modified file updates ``state.active`` atomically while preserving
unchanged fields. Tests exercise reload paths, and the simulation
increments a value from 1 to 2, recording metrics in
``config_hot_reload_metrics.json`` to verify success and fallback
behavior when files disappear.

## Simulation Expectations

The hot-reload simulation updates a value from 1 to 2 and records metrics in
``config_hot_reload_metrics.json``.

[r1]: ../../tests/analysis/config_hot_reload_metrics.json
