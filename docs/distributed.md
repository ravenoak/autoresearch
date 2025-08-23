# Distributed Coordination

Autoresearch can dispatch agents across processes or nodes. The
`ProcessExecutor` uses Python's `multiprocessing` module, while
`RayExecutor` runs agents on a Ray cluster. Both executors share data
through a message broker:

- `memory`: in-process queues suitable for local testing.
- `redis`: uses a Redis instance for cross-node communication.
- `ray`: relies on Ray's distributed queue actor.

Configure the executor in `ConfigModel.distributed_config` and set the
`message_broker` field to one of the above options. The optional
`broker_url` provides the Redis connection string. For Ray, ensure a
cluster is running and specify its address in `distributed_config`.

When the distributed flag is enabled, claims are persisted by a storage
coordinator and agent results are aggregated asynchronously. Each broker
supports a `publish` method and a `queue` attribute with `put` and `get`
operations.
