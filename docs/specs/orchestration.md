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

## Assumptions and results

- Circuit breaker treats critical and recoverable errors as unit increments and
  halves for transient ones. Property tests show three critical failures open
  the breaker and a success after cooldown closes it.
- Parallel execution launches at most `cpu_count - 1` threads. Randomized group
  simulations confirm metrics reflect the number of groups executed.
- Targeted metrics tests guard against coverage regressions by asserting at
  least 80% line coverage for helper functions.

## Traceability

- Modules
  - [src/autoresearch/orchestration/][m1]
  - [docs/algorithms/orchestration.md][d1]
- Tests
  - [tests/behavior/features/agent_orchestration.feature][t1]
  - [tests/behavior/features/orchestration_system.feature][t2]
  - [tests/behavior/features/orchestrator_agents_integration.feature][t3]
  - [tests/behavior/features/orchestrator_agents_integration_extended.feature][t4]
  - [tests/behavior/features/parallel_query_execution.feature][t5]
  - [tests/unit/test_orchestrator_circuit_breaker_property.py][t6]
  - [tests/unit/test_orchestrator_parallel_property.py][t7]
  - [tests/targeted/test_orchestration_metrics.py][t8]

[m1]: ../../src/autoresearch/orchestration/
[d1]: ../../docs/algorithms/orchestration.md
[t1]: ../../tests/behavior/features/agent_orchestration.feature
[t2]: ../../tests/behavior/features/orchestration_system.feature
[t3]: ../../tests/behavior/features/orchestrator_agents_integration.feature
[t4]: ../../tests/behavior/features/orchestrator_agents_integration_extended.feature
[t5]: ../../tests/behavior/features/parallel_query_execution.feature
[t6]: ../../tests/unit/test_orchestrator_circuit_breaker_property.py
[t7]: ../../tests/unit/test_orchestrator_parallel_property.py
[t8]: ../../tests/targeted/test_orchestration_metrics.py
