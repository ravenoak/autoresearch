# Message Broker Options

Autoresearch can coordinate distributed workers through a pluggable broker layer.
The default `memory` broker uses an in-process queue and requires no external
services. Lightweight alternatives include:

## Ray distributed queue

- **Pros**: integrates with Ray executors and scales with the object store.
- **Cons**: requires the optional `distributed` extra and a running Ray
  cluster.

Ray-backed brokers now wrap the runtime queue behind a shared
`MessageQueueProtocol`, letting the storage coordinator and result aggregator
share logic with Redis and in-memory brokers. When Ray is not installed the
typed shim falls back to a synchronous stub so local testing and strict mypy
checks stay aligned without additional `type: ignore` directives.

## Redis

- **Pros**: simple to deploy, minimal overhead, widely available.
- **Cons**: provides only basic persistence unless configured, single point of failure.

Enable the prototype Redis broker by adding the following to your configuration:

```toml
[distributed]
message_broker = "redis"
broker_url = "redis://localhost:6379/0"
```

Install the optional `redis` dependency and start a Redis server before running
in this mode.

## NATS

- **Pros**: extremely lightweight and performant.
- **Cons**: limited persistence features, smaller ecosystem.

## RabbitMQ

- **Pros**: mature AMQP broker with robust routing capabilities.
- **Cons**: heavier to operate compared to Redis or NATS.
