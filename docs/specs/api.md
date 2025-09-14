# API

## Overview

FastAPI app aggregator for Autoresearch. See these algorithm references:
- [API authentication](../algorithms/api_authentication.md)
- [Error paths](../algorithms/api_auth_error_paths.md)
- [API rate limiting](../algorithms/api_rate_limiting.md)
- [API streaming](../algorithms/api_streaming.md)

Requests and responses use versioned schemas; the current
`QueryRequestV1` and `QueryResponseV1` models require a `version` field of
`"1"`. Deprecated versions return **410 Gone** while unknown versions
return **422 Unprocessable Entity**.

## Algorithms

- Implement core behaviors described above.

## Invariants

- Streamed responses emit chunks in request order.
- Heartbeats occur at least once per connection.
- The ``END`` sentinel terminates the stream.
- Webhook callbacks retry failed deliveries with exponential backoff.

## Edge Cases

- Zero chunks send only the ``END`` sentinel.
- Deprecated versions return **410 Gone** and unknown versions return
  **422 Unprocessable Entity**.

## Complexity

Streaming ``n`` chunks performs ``O(n)`` work and uses ``O(1)`` extra memory.

## Proof Sketch

Streaming a finite chunk list while recording data and heartbeats shows the
ordering and liveness invariants hold. Tests cover nominal and error paths, and
the simulation in `api_stream_order_sim.py` confirms ordered delivery,
heartbeat counts, and linear operations.

## Simulation Expectations

Streaming simulations send three chunks and record metrics such as
``{"ordered": true, "heartbeats": 3, "operations": 7}``.
