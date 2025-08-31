# Interfaces

Shared typing helpers describe contracts between orchestration components.

## Callback map
- `CallbackMap` maps hook names to callables with arbitrary parameters.

## Query state protocol
- `QueryStateLike` requires a `cycle` attribute, an `update` method to absorb
  agent results, and `synthesize` to produce a `QueryResponse`.

## References
- [`interfaces.py`](../../src/autoresearch/interfaces.py)

## Simulation

Automated tests confirm interfaces behavior.

- [Spec](../specs/agents.md)
- [Tests](../../tests/behavior/features/query_interface.feature)
