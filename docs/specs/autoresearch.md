# Autoresearch Package

## Overview

`__init__` wires global metadata and lazy imports for distributed features.

## Algorithms

- Patch `pydantic.root_model` into `sys.modules` to satisfy clients.
- Load `__version__` from package metadata, falling back to a default.
- `__getattr__` intercepts access to distributed symbols and imports
  `autoresearch.distributed` on demand.

## Invariants

- `__version__` is always defined.
- Only names in `_DISTRIBUTED_ATTRS` are lazily loaded.
- `pydantic.root_model` resolves during import.

## Proof Sketch

`tests/integration/test_a2a_interface_extra.py` asserts that `pydantic.root_model`
exists. `tests/unit/legacy/test_distributed.py` imports distributed symbols,
triggering `__getattr__` without errors.

## Simulation Expectations

- Importing `publish_claim` after `import autoresearch` succeeds.
- Unknown attributes raise `AttributeError`.

## Traceability

- Code: [src/autoresearch/__init__.py][m1]
- Tests:
  - [tests/integration/test_a2a_interface_extra.py][t1]
  - [tests/unit/legacy/test_distributed.py][t2]

[m1]: ../../src/autoresearch/__init__.py
[t1]: ../../tests/integration/test_a2a_interface_extra.py
[t2]: ../../tests/unit/legacy/test_distributed.py
