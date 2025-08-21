# Distributed Coordination

Agents operating in parallel need mechanisms for coalition formation,
efficient scheduling, and resilient failure recovery. The distributed
utilities in `src/autoresearch/distributed` provide these primitives.

## Coalition Formation

- `ResultAggregator` collects agent messages from a broker queue to form a
  shared state. See
  [coordinator.py](../../src/autoresearch/distributed/coordinator.py).
- `StorageCoordinator` persists claims from agents, enabling a common
  knowledge base across processes.

## Message Throughput

- Queue operations on the `multiprocessing.Queue` backing `InMemoryBroker`
  run in constant time. With `P` worker processes and average service time
  `t_s`, throughput is bounded by `P / t_s` messages per second.

## Scheduling Complexity

- `ProcessExecutor.run_query` dispatches each agent through a multiprocessing
  pool per loop. For `L` loops over `A` agents with `P` workers, dispatching
  costs `O(L * A / P)` while pool management adds `O(L * P)`, yielding overall
  complexity `O(L * A)`
  ([executors.py](../../src/autoresearch/distributed/executors.py)).

## Failure Recovery

- `ProcessExecutor.shutdown` publishes `stop` actions and joins background
  processes so queues drain safely. Draining `M` queued messages across `P`
  workers and joining those processes bounds recovery time by `O(M / P + P)`
  ([executors.py](../../src/autoresearch/distributed/executors.py)).

## Simulation

A stress test using the `multiprocessing.Manager().Queue` backing
`InMemoryBroker` processed 10\,000 messages in 1.015 s, about 9\,854 msg/s.
When one worker crashed after 5\,000 messages, the remaining workers drained
the queue in 1.017 s, about 9\,834 msg/s. An empty `get` raised a timeout
after 0.1 s, providing an upper bound on failure detection latency.
