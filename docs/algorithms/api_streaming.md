# API Streaming

The streaming endpoint delivers intermediate query results over an HTTP
connection. It runs the query in a background thread and forwards each cycle's
state to the client, then posts the final response to any configured webhooks.

## Back-pressure

- Intermediate results are placed on an `asyncio.Queue`.
- The HTTP generator removes one item at a time and yields it to the client as
  a JSON line.
- The queue is unbounded; the orchestrator never blocks when adding items. If a
  client stops reading, results accumulate in memory. Consumers should read from
  the stream to apply back-pressure and avoid unbounded growth.
- When the queue is idle for 15 seconds the generator yields a blank newline as
  a heartbeat to keep intermediaries from closing the connection.

## Queue growth model

The [API spec](../specs/api.md) notes that streaming posts intermediate
results while preserving invariants. With a stalled client, the producer keeps
enqueuing items. Let `\lambda` denote the production rate in messages per
second, `s` the average message size in bytes, and `t` the stall duration in
seconds. The queue length and memory use grow linearly:

- `q(t) = \lambda t`
- `m(t) = \lambda s t`

The [queue growth simulation](../../scripts/queue_growth_sim.py) validates this
model.

Example:

```
uv run scripts/queue_growth_sim.py --rate 5 --size 1024 --stall 10
queue length: 50 items
approx memory: 51200 bytes
```

## Timeout guarantees

- Webhook deliveries call `httpx.post` with the `api.webhook_timeout` value.
  Requests exceeding this limit are aborted and logged, but streaming continues.
- The HTTP stream relies on the server's connection timeout. Once the final
  result is queued, a `None` sentinel signals completion and the response
  closes promptly.

## Proof sketch

Assume each webhook attempt succeeds independently with probability `p` within
the configured timeout. With at most `r` retries, the probability of at least
one success is `1 - (1 - p)^{r+1}`. This lower bounds connection reliability
and shows diminishing returns as `r` grows. Expected delivery attempts are
bounded by the geometric series `<= (1 - (1 - p)^{r+1}) / p`.

The [simulation script](../../scripts/streaming_webhook_sim.py) models these
retries and validates the bound empirically.

## Simulation

Automated tests confirm api streaming behavior.

- [Spec](../specs/api.md)
- [Tests](../../tests/behavior/steps/api_streaming_steps.py)
- [Simulation script](../../scripts/streaming_webhook_sim.py)
- [Queue growth simulation](../../scripts/queue_growth_sim.py)
