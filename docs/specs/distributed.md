# Distributed

Distributed execution utilities. See [distributed coordination][dc] for
coalition and scheduling details.

[dc]: ../algorithms/distributed_coordination.md

## Acceptance Criteria

- Message queues perform `O(1)` operations; with `P` workers throughput scales
  linearly, achieving about 9\,800 msg/s with four workers.
- `ProcessExecutor` schedules `A` agents over `L` loops with complexity
  `O(L * A)`.
- On worker failure, shutdown drains `M` queued messages across `P` workers in
  `O(M / P + P)` time without data loss.

## Traceability

- `../../tests/unit/test_distributed.py`
- `../../tests/unit/test_distributed_extra.py`
- `../../tests/integration/test_distributed_agent_storage.py`
