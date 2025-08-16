# Refactor Orchestrator to instance-level circuit breaker

The orchestrator currently uses a class-level `_cb_manager` that persists across
queries and tests, leading to shared state and cross-test interference. A prior
refactor attempt moved `_cb_manager` toward instance state but left methods and
tests inconsistent, causing unit failures.

## Context
- `_cb_manager` lives on the `Orchestrator` class in
 `src/autoresearch/orchestration/orchestrator.py`.
- Shared state bleeds between queries and tests.
- Refactoring requires allocating a new circuit breaker manager per query and
 propagating this change through dependent modules and tests.

## Acceptance Criteria
- `_cb_manager` is an instance attribute initialized for each query.
- Orchestrator methods and any downstream consumers are updated accordingly.
- Tests are updated to assume instance-scoped circuit breaker state.
- `task test:unit` completes successfully with no cross-test interference.

## Status
Archived

