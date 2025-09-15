# API

## Overview

FastAPI app aggregator for Autoresearch. See these algorithm references:
- [API authentication](../algorithms/api_authentication.md)
- [Constant-time auth proof](../algorithms/api-authentication.md)
- [Error paths](../algorithms/api_auth_error_paths.md)
- [API rate limiting](../algorithms/api_rate_limiting.md)
- [API streaming](../algorithms/api_streaming.md)

Requests and responses use versioned schemas. The current
`QueryRequestV1` and `QueryResponseV1` models require a `version` field of
`"1"`. Deprecated versions return **410 Gone** while unknown versions
return **422 Unprocessable Entity**.

## Authentication

Clients must include a valid API key or bearer token.

- ``X-API-Key`` headers map to roles defined in ``api.api_keys``.
- ``Authorization: Bearer <token>`` headers are checked against
  ``api.bearer_token``.
- Each role's permissions come from ``api.role_permissions``.
- Missing or invalid credentials return **401 Unauthorized**.
- Insufficient permissions return **403 Forbidden**.
- Credentials are validated before request bodies are read.

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
ordering and liveness invariants hold. Tests cover nominal and error paths,
and the simulation in [api_stream_order_sim.py][s1] confirms ordered
delivery, heartbeat counts, and linear operations. The
[api-authentication](../algorithms/api-authentication.md) proof outlines
constant-time credential checks, and [api_auth_credentials_sim.py][s2]
exercises valid and invalid tokens and roles.

## Simulation Expectations

Streaming simulations send three chunks and record metrics such as
``{"ordered": true, "heartbeats": 3, "operations": 7}``.

## Traceability

- Modules
  - [src/autoresearch/api/][m1]
- Scripts
  - [scripts/api_stream_order_sim.py][s1]
  - [scripts/api_auth_credentials_sim.py][s2]
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
  - [tests/analysis/test_api_stream_order_sim.py][t13]

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
[s1]: ../../scripts/api_stream_order_sim.py
[s2]: ../../scripts/api_auth_credentials_sim.py
[t13]: ../../tests/analysis/test_api_stream_order_sim.py
