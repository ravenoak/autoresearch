# API

## Overview

FastAPI app aggregator for Autoresearch. See these algorithm references:
- [API authentication](../algorithms/api_authentication.md)
- [Error paths](../algorithms/api_auth_error_paths.md)
- [API rate limiting](../algorithms/api_rate_limiting.md)
- [API streaming](../algorithms/api_streaming.md)

Requests and responses use versioned schemas; the current
`QueryRequestV1` and `QueryResponseV1` models require a `version` field of
`"1"`.

## Algorithms

- Implement core behaviors described above.

## Invariants

- Streamed responses emit chunks in request order.
- Heartbeats occur at least once per connection.
- The ``END`` sentinel terminates the stream.
- Webhook callbacks retry failed deliveries with exponential backoff.

## Proof Sketch

Streaming a finite chunk list while recording data and heartbeats shows the
ordering and liveness invariants hold. Tests cover nominal and error paths,
and the simulation in [api_streaming_metrics.json][r1] confirms ordered
delivery and heartbeat retries.

## Simulation Expectations

Streaming simulations send three chunks and record metrics in
[api_streaming_metrics.json][r1].

## Traceability


- Modules
  - [src/autoresearch/api/][m1]
- Tests
  - [tests/unit/test_api.py][t1]
  - [tests/unit/test_api_error_handling.py][t2]
  - [tests/unit/test_api_imports.py][t3]
  - [tests/unit/test_api_auth_middleware.py][t4]
  - [tests/unit/test_api_auth_deps.py][t5]
  - [tests/integration/test_api_auth.py][t6]
  - [tests/integration/test_api_auth_middleware.py][t7]
  - [tests/integration/test_api_streaming.py][t8]
  - [tests/integration/test_api_streaming_webhook.py][t10]
  - [tests/integration/test_api_docs.py][t9]
  - [tests/analysis/test_api_streaming_sim.py][t11]
  - [tests/unit/test_webhooks_logging.py][t12]

[m1]: ../../src/autoresearch/api/
[t1]: ../../tests/unit/test_api.py
[t2]: ../../tests/unit/test_api_error_handling.py
[t3]: ../../tests/unit/test_api_imports.py
[t4]: ../../tests/unit/test_api_auth_middleware.py
[t5]: ../../tests/unit/test_api_auth_deps.py
[t6]: ../../tests/integration/test_api_auth.py
[t7]: ../../tests/integration/test_api_auth_middleware.py
[t8]: ../../tests/integration/test_api_streaming.py
[t10]: ../../tests/integration/test_api_streaming_webhook.py
[t9]: ../../tests/integration/test_api_docs.py
[t11]: ../../tests/analysis/test_api_streaming_sim.py
[t12]: ../../tests/unit/test_webhooks_logging.py
[r1]: ../../tests/analysis/api_streaming_metrics.json
