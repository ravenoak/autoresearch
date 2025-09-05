# Api

## Overview

FastAPI app aggregator for Autoresearch. See these algorithm references:
- [API authentication](../algorithms/api_authentication.md)
- [Error paths](../algorithms/api_auth_error_paths.md)
- [API rate limiting](../algorithms/api_rate_limiting.md)
- [API streaming](../algorithms/api_streaming.md)

## Algorithms

- Implement core behaviors described above.

## Invariants

- Streamed responses emit chunks in request order.
- Heartbeats occur at least once per connection.
- The ``END`` sentinel terminates the stream.

## Proof Sketch

Basic checks assert streamed chunks remain ordered and emit periodic
heartbeats.

## Proof Steps

1. Produce a finite chunk list.
2. Iterate over the stream collecting data and heartbeats.
3. Assert collected chunks match the expected sequence and a heartbeat occurs.
4. Verify success in [api_streaming_metrics.json][r1].

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines. Streaming endpoints
send heartbeat lines every 15 seconds to keep connections open and retry
webhook deliveries up to three times with exponential backoff. The simulation
confirms ordering and heartbeat delivery by streaming three chunks and recording
metrics in [api_streaming_metrics.json][r1]. Streaming scenarios post
intermediate cycle results to configured webhooks alongside final responses.

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
[r1]: ../../tests/analysis/api_streaming_metrics.json
