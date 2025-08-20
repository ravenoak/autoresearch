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

## Scheduling Complexity

- `ProcessExecutor.run_query` dispatches each agent through a multiprocessing
  pool per loop, giving time complexity `O(L * A)` for `L` loops over `A`
  agents ([executors.py](../../src/autoresearch/distributed/executors.py)).

## Failure Recovery

- `ProcessExecutor.shutdown` publishes `stop` actions and joins background
  processes so queues drain safely
  ([executors.py](../../src/autoresearch/distributed/executors.py)).

## Simulation

A benchmark using the same `multiprocessing.Manager().Queue` as
`InMemoryBroker` processed 10\,000 messages in 0.869 s, about 11\,500 msg/s,
while an empty `get` raised a timeout after 0.1 s. These figures approximate
message throughput and queue timeouts for the in-memory broker implementation.
