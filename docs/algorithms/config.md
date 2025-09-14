# Configuration

## Overview
The config package loads settings from files and environment variables.

## Algorithm
`ConfigLoader` merges defaults with profile data, watching files for
changes to support live reload.

## Proof sketch
Merging operates on ordered layers; each layer overrides the previous,
ensuring deterministic results.

## Simulation
`tests/unit/test_config_loader_defaults.py` exercises merging and reload
behaviour.

## References
- [code](../../src/autoresearch/config/)
- [spec](../specs/config.md)
- [tests](../../tests/unit/test_config_loader_defaults.py)

## Related Issues
- [Resolve deprecation warnings in tests][issue]

[issue]: ../../issues/resolve-deprecation-warnings-in-tests.md
