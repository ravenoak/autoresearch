# Distributed Workflows

## Coordination

Redis-backed workflows coordinate agents across processes using a list
queue (see `broker.py`). Each
call to `publish` serializes the message to JSON and appends it with
`RPUSH`, preserving order. Workers block with `BLPOP` so at most one
consumer retrieves each entry and FIFO semantics hold.

## Latency and Throughput

Queue operations run in `O(1)` time, so latency is dominated by network
hops. Given average network round trip `t_n` and payload size `s`, enqueue
delay is `t_n`, while dequeue waits `t_n` plus any blocking time until data
arrives.

## Failure Recovery

Connection failures raise `redis.exceptions.RedisError`. The error recovery
workflow retries the operation and surfaces a warning when the client
remains unavailable.

## Checklist

Trace these behaviors against the [distributed specification][spec].

- [ ] Message queues perform `O(1)` operations and scale linearly with
  workers.
- [ ] `ProcessExecutor` schedules `A` agents over `L` loops in `O(L * A)`
  time.
- [ ] On worker failure, shutdown drains `M` messages across `P` workers in
  `O(M / P + P)` time without losing data.

## Related Issue

See [add-redis-distributed-workflows-specification][issue] for the
discussion that introduced this specification.

[spec]: ../specs/distributed.md
[issue]: ../../issues/add-redis-distributed-workflows-specification.md

## Simulation

Automated tests confirm distributed workflows behavior.

- [Spec](../specs/distributed.md)
- [Tests](../../tests/behavior/features/distributed_execution.feature)
