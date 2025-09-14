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
