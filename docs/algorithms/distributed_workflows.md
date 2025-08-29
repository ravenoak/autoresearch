# Distributed Workflows

Redis-backed workflows coordinate agents across processes using a simple
list queue (see [broker.py](../../src/autoresearch/distributed/broker.py)).
Each call to `publish` serializes the message to JSON and appends it to the
queue with `RPUSH`, preserving order. Workers block with `BLPOP`, ensuring
at-most-one consumer retrieves each entry and maintaining FIFO semantics.

## Latency and Throughput

Queue operations run in `O(1)` time, so latency is dominated by network
hops. Given average network round trip `t_n` and payload size `s`, expected
enqueue delay is `t_n`, while dequeue waits `t_n` plus any blocking time
until data arrives.

## Failure Recovery

Connection failures raise a `redis.exceptions.RedisError`. The error
recovery workflow retries the operation and surfaces a warning when the
client remains unavailable.

## Related Issue

See [add-redis-distributed-workflows-specification][issue] for the
discussion that introduced this specification.

[issue]: ../../issues/add-redis-distributed-workflows-specification.md
