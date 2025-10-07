# Config Utils

## Overview

Configuration helper utilities for the Streamlit app.

## Algorithms

- Start from embedded defaults.
- Load the base configuration file.
- Merge selected profiles in the order provided.
- Apply environment variable overrides.
- Validate and freeze the resolved state.

## Invariants

- Merge order yields deterministic values.
- Profiles override only declared keys.
- Validation ensures required fields and types.
- The resolved configuration is immutable.

## Failure Modes

- Unknown profile name.
- Missing or unreadable configuration file.
- Conflicting environment override.
- Invalid value that fails validation.

## Proof Sketch

Deterministic layering ensures that any combination of profiles produces the
same state regardless of evaluation path. Validation checks run after each
merge, preventing propagation of invalid data. Immutability prevents later
mutation from violating assumptions.

## Simulation Expectations

- Default profile alone yields baseline settings.
- Base plus a user profile merges expected overrides.
- Multiple profiles composed in order preserve precedence.
- Conflicting profiles raise validation errors.

Unit tests cover nominal and edge cases for these routines.

## Traceability

- Modules
  - [src/autoresearch/config_utils.py][m1]
- Docs
  - [docs/algorithms/config_utils.md][d1]
- Tests
  - [tests/unit/legacy/test_config_env_file.py][t1]
  - [tests/unit/legacy/test_config_errors.py][t2]
  - [tests/unit/legacy/test_config_loader_defaults.py][t3]
  - [tests/unit/legacy/test_config_profiles.py][t4]
  - [tests/unit/legacy/test_config_reload.py][t5]
  - [tests/unit/legacy/test_config_utils.py][t6]
  - [tests/unit/legacy/test_config_validation_errors.py][t7]
  - [tests/unit/legacy/test_config_validators_additional.py][t8]
  - [tests/unit/legacy/test_config_watcher_cleanup.py][t9]
  - [tests/unit/legacy/test_streamlit_app_edgecases.py][t10]
  - [tests/unit/legacy/test_streamlit_utils.py][t11]

[m1]: ../../src/autoresearch/config_utils.py
[d1]: ../algorithms/config_utils.md
[t1]: ../../tests/unit/legacy/test_config_env_file.py
[t2]: ../../tests/unit/legacy/test_config_errors.py
[t3]: ../../tests/unit/legacy/test_config_loader_defaults.py
[t4]: ../../tests/unit/legacy/test_config_profiles.py
[t5]: ../../tests/unit/legacy/test_config_reload.py
[t6]: ../../tests/unit/legacy/test_config_utils.py
[t7]: ../../tests/unit/legacy/test_config_validation_errors.py
[t8]: ../../tests/unit/legacy/test_config_validators_additional.py
[t9]: ../../tests/unit/legacy/test_config_watcher_cleanup.py
[t10]: ../../tests/unit/legacy/test_streamlit_app_edgecases.py
[t11]: ../../tests/unit/legacy/test_streamlit_utils.py
