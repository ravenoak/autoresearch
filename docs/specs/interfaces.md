# Interfaces

## Overview

Common project interfaces unify orchestration components. `CallbackMap` maps
hook names to callables. `QueryStateLike` defines the contract for state objects
shared across dialectical cycles.

## Algorithms

- Callback dispatch uses `CallbackMap` to invoke registered hooks.
- `QueryStateLike.update` merges agent results into the state.
- `QueryStateLike.synthesize` composes a `QueryResponse` from accumulated
  data.

## Invariants

- `cycle` monotonically increases and starts at zero.
- Implementations retain previously collected claims, sources, and metadata.
- `synthesize` must return a `QueryResponse` object.

## Proof Sketch

`QueryStateLike` requires `update` and `synthesize`, ensuring every state object
can absorb new information and produce final responses. Maintaining the `cycle`
attribute and preserving context uphold the invariants across orchestrator
steps.

## Simulation Expectations

Unit tests instantiate compliant and non-compliant objects. They verify
`QueryState` and a minimal toy implementation satisfy the protocol while a
partial implementation fails runtime checks.

## Traceability

- Modules
  - [src/autoresearch/interfaces.py][m1]
- Tests
  - [tests/unit/test_interfaces.py][t1]

[m1]: ../../src/autoresearch/interfaces.py
[t1]: ../../tests/unit/test_interfaces.py
