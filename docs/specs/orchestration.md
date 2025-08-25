# Orchestration Module Specification

The orchestration package (`src/autoresearch/orchestration/`) coordinates
agents and reasoning loops. It manages agent rotation, state transfer
and error handling while providing detailed logging and token counting.

## Key behaviors

- Rotate agents through thesis→antithesis→synthesis cycles and track the
  Primus agent across queries.
- Integrate multiple agents, propagating state and capturing errors.
- Support multiple reasoning loops and modes while preserving agent
  state.
- Run agent groups in parallel and synthesize their results.
- Record token usage and emit structured debug logs.
- Metrics helpers depend on callables (e.g., `time.time`) so tests can swap
  implementations without using `types.SimpleNamespace`.

## Traceability

- Modules
  - [src/autoresearch/orchestration/][m1]
- Tests
  - [tests/behavior/features/agent_orchestration.feature][t1]
  - [tests/behavior/features/orchestration_system.feature][t2]
  - [tests/behavior/features/orchestrator_agents_integration.feature][t3]
  - [tests/behavior/features/orchestrator_agents_integration_extended.feature][t4]
  - [tests/behavior/features/parallel_query_execution.feature][t5]

[m1]: ../../src/autoresearch/orchestration/
[t1]: ../../tests/behavior/features/agent_orchestration.feature
[t2]: ../../tests/behavior/features/orchestration_system.feature
[t3]: ../../tests/behavior/features/orchestrator_agents_integration.feature
[t4]: ../../tests/behavior/features/orchestrator_agents_integration_extended.feature
[t5]: ../../tests/behavior/features/parallel_query_execution.feature
