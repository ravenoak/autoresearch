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

## Timeout guarantees

- Webhook deliveries call `httpx.post` with the `api.webhook_timeout` value.
  Requests exceeding this limit are aborted and logged, but streaming continues.
- The HTTP stream relies on the server's connection timeout. Once the final
  result is queued, a `None` sentinel signals completion and the response
  closes promptly.

## Simulation

Automated tests confirm api streaming behavior.

- [Spec](../specs/api.md)
- [Tests](../../tests/behavior/steps/api_streaming_steps.py)
