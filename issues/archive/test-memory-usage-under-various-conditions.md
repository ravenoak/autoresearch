# Issue 7: Test memory usage under various conditions

Track the task "Test memory usage under various conditions" from Phase 2 of `TASK_PROGRESS.md`.
See [TASK_PROGRESS.md](../TASK_PROGRESS.md) for overall status.

## Context
Evaluate memory consumption for light, typical, and heavy workloads to
detect leaks or excessive growth.

## Acceptance Criteria
- Memory usage measured across workload levels
- Tests fail on leaks or excessive growth
- Memory profiles documented

## Status
Done – see tests/integration/test_query_latency_memory_tokens.py

## Related
- #1
- #5
