# Orchestrator State Specification

The orchestrator manages a `QueryState` that evolves through a small set of
states. Transitions are triggered by state mutation methods and lead to a
final synthesized response.

![State machine](diagrams/orchestrator_state.puml)

## State transitions

- `Initialized` --`update`--> `Updated`
- `Updated` --`add_error`--> `Error`
- `Error` --`update`--> `Updated`
- `Updated` --`synthesize`--> `Finalized`

## Invariants

- `cycle` starts at 0 and never decreases.
- `error_count` begins at 0 and increments with each `add_error` call.
- `last_updated` increases on every `update`.
- `synthesize` uses accumulated `claims`, `sources`, and `results`.

## Traceability

- `src/autoresearch/orchestration/state.py`
- `../tests/integration/test_orchestrator_state_transitions.py`
