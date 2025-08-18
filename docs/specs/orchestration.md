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

## Traceability

- **Modules**
  - `src/autoresearch/orchestration/`
- **Tests**
  - [orchestration_system.feature](../../tests/behavior/features/orchestration_system.feature)
  - [agent_orchestration.feature](../../tests/behavior/features/agent_orchestration.feature)
  - [orchestrator_agents_integration.feature](../../tests/behavior/features/orchestrator_agents_integration.feature)
  - [orchestrator_agents_integration_extended.feature](../../tests/behavior/features/orchestrator_agents_integration_extended.feature)
  - [parallel_query_execution.feature](../../tests/behavior/features/parallel_query_execution.feature)

## Extending

Document new orchestration behaviors and reference the corresponding
feature files under **Traceability**.
