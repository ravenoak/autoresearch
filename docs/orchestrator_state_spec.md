# Orchestrator State Specification

The orchestrator progresses through a linear set of phases. The diagram below
shows the allowed transitions.

![Orchestrator states](diagrams/orchestrator_state.puml)

## Invariants

- `start()` may only be invoked when the orchestrator is idle.
- `launch()` must follow `start()` and transitions the state to running.
- `finish()` may only be invoked from the running state and leads to complete.
- `fail()` may only be invoked from the running state and leads to error.
- The complete and error states are terminal and permit no further changes.

Tests: see
[tests/integration/test_orchestrator_state_spec.py]
(../tests/integration/test_orchestrator_state_spec.py).

