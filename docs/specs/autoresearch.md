# Autoresearch Package

## Overview

Initialises the Autoresearch library and exposes version metadata and
optional distributed helpers.

## Algorithms

- Registers `pydantic.root_model` to avoid import errors.
- Defines `__version__` from package metadata.
- Lazily loads distributed functions via `__getattr__`.

## Invariants

- `__version__` matches the installed package version.
- Missing distributed extras raise `AttributeError` after warning.

## Proof Sketch

[docs/algorithms/__init__.md](../algorithms/__init__.md) details the
initialisation rules. Unit tests confirm version agreement and graceful
failure when extras are absent.

## Simulation Expectations

- `tests/unit/test_version.py` verifies version consistency.
- Accessing unavailable distributed attributes emits a warning.

## Traceability

- Code: [src/autoresearch/__init__.py][m1]
- Tests: [tests/unit/test_version.py][t1]

[m1]: ../../src/autoresearch/__init__.py
[t1]: ../../tests/unit/test_version.py
