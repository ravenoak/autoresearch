# API

## Overview

The Autoresearch API assembles a FastAPI application that exposes query,
configuration, documentation, and monitoring endpoints. `routing.create_app`
initialises shared state, installs authentication and rate limiting
middleware, and registers versioned routes built around
`QueryRequestV1`/`QueryResponseV1`. The package draws configuration from
`ConfigLoader`, uses `RequestLogger` to track per-client usage, and streams
results while posting webhook callbacks. Related derivations live in:

- [API authentication](../algorithms/api_authentication.md)
- [Authentication proof sketch](../algorithms/api-authentication.md)
- [Auth error paths](../algorithms/api_auth_error_paths.md)
- [API rate limiting](../algorithms/api_rate_limiting.md)
- [API streaming](../algorithms/api_streaming.md)

## Schemas and Versioning

- `VersionedModel` exposes a `version` field while deferring validation so
  routers can reject deprecated or unknown schemas with precise HTTP codes.
- `SUPPORTED_VERSIONS` is `{ "1" }`; `DEPRECATED_VERSIONS` is empty.
- `validate_version` raises **410 Gone** for deprecated versions and
  **422 Unprocessable Entity** for unsupported values.

## Authentication and Permissions

- `AuthMiddleware` reloads API configuration on each request, then checks
  `api.api_keys`, `api.api_key`, or `api.bearer_token` for credentials.
- API keys map to roles and leverage `secrets.compare_digest` to avoid timing
  leaks; bearer tokens reuse `verify_bearer_token` for constant-time checks.
- The resolved role's permissions populate `request.state.permissions`.
- `require_permission` injects dependencies that call `enforce_permission`,
  returning **401 Unauthorized** with `WWW-Authenticate` headers when missing
  and **403 Forbidden** when insufficient.

## Routing and Endpoints

- `/query` validates request versions, runs synchronous queries, forwards
  responses to configured webhooks, and normalises errors via
  `format_error_for_api`.
- `/query/stream` delegates to `query_stream_endpoint` to stream JSON lines,
  emitting blank-line heartbeats every 15 seconds until a final payload
  arrives.
- `/query/batch` paginates batched requests and executes each query
  concurrently with `asyncio.TaskGroup`.
- `/query/async`, `/query/{id}`, and `DELETE /query/{id}` manage background
  tasks stored in `app.state.async_tasks`.
- `/config` (GET, PUT, POST, DELETE) surfaces live configuration, applies
  validated updates via `ConfigModel`, and notifies observers.
- `/capabilities` summarises reasoning modes, LLM backends, agent metadata,
  and storage/search capabilities from `StorageManager`.
- `/metrics` is available only when monitoring is enabled in configuration;
  otherwise `routes.router` omits the path.
- `/docs` and `/openapi.json` render customised documentation guarded by the
  `docs` permission.

## Rate Limiting and Logging

- `Limiter` defaults to SlowAPI's implementation when available and falls back
  to a stub that reuses `RequestLogger` counts per client IP.
- `dynamic_limit` reads `api.rate_limit` to derive SlowAPI-compatible strings.
- `RateLimitMiddleware` injects limit headers when SlowAPI is present;
  `FallbackRateLimitMiddleware` enforces simple thresholds otherwise.

## Algorithms

1. **Version validation:** `validate_version` rejects deprecated or unknown
   schema versions before any orchestration work begins.
2. **Authentication:** `AuthMiddleware.dispatch` loads configuration, extracts
   headers, resolves roles, stores permissions, and short-circuits with
   `WWW-Authenticate` errors when credentials are missing or invalid.
3. **Query execution:** `query_endpoint` runs orchestrator queries inside a
   tracing span, formats errors, and mirrors responses to per-request or
   global webhooks with retry backoff settings.
4. **Streaming:** `query_stream_endpoint` spawns a background executor that
   pushes cycle updates into an `asyncio.Queue`; the generator drains the
   queue, yields newline-delimited JSON, and emits blank lines as keepalives.
5. **Async management:** `/query/async` stores futures in
   `app.state.async_tasks`, `/query/{id}` polls completion, and `DELETE` cancels
   and removes outstanding work.
6. **Configuration updates:** PUT/POST merge incoming data into `ConfigModel`
   instances, notify observers, and preserve atomic swaps; DELETE reloads from
   disk to discard runtime edits.

## Invariants

- Every request populates `request.state.permissions`, `role`, and
  `www_authenticate` before reaching route handlers.
- Versioned routes call `validate_version` exactly once, ensuring **410** or
  **422** responses for deprecated or unsupported schemas.
- Streaming responses preserve enqueue order, interleave keepalive heartbeats,
  and end with a newline-terminated JSON object.
- Async query identifiers remain in `app.state.async_tasks` until completion or
  cancellation to avoid dangling futures.
- `/metrics` is registered only when `api.monitoring_enabled` is true, so
  deployments without monitoring expose no Prometheus endpoint.
- Rate limiting never increments counters when disabled and always injects
  limit headers when SlowAPI is active.

## Edge Cases

- Missing credentials with authentication enabled return **401 Unauthorized**
  and specify the required scheme.
- Clients lacking required permissions receive **403 Forbidden** regardless of
  credential type.
- Unknown async identifiers return **404** without mutating stored futures.
- Invalid pagination parameters in `/query/batch` raise **400 Bad Request**.

## Complexity

- Streaming `n` payloads performs `O(n)` work with `O(1)` additional memory.
- Batch pagination slices requests in `O(page_size)` time per call.
- Async status checks run in `O(1)` time per lookup.

## Proof Sketch

Authentication relies on constant-time comparisons and explicit permission
checks proven in [API authentication](../algorithms/api_authentication.md) and
[API authentication proof](../algorithms/api-authentication.md). Error
responses follow [auth error paths](../algorithms/api_auth_error_paths.md) and
rate limiting obeys [API rate limiting](../algorithms/api_rate_limiting.md).
Streaming order and liveness are justified by
[API streaming](../algorithms/api_streaming.md), while unit, integration, and
analysis tests cover version handling, async orchestration, webhook retries,
and documentation rendering.

## Simulation Expectations

- [api_auth_credentials_sim.py][s2] exercises valid, missing, and invalid
  credentials across roles.
- [api_stream_order_sim.py][s1] records streaming order, heartbeat cadence,
  and queue lengths, expecting metrics such as
  `{ "ordered": true, "heartbeats": 3, "operations": 7 }` for three-chunk
  runs.

## Traceability

- Modules
  - [src/autoresearch/api/__init__.py][m1]
  - [src/autoresearch/api/auth_middleware.py][m2]
  - [src/autoresearch/api/middleware.py][m3]
  - [src/autoresearch/api/routing.py][m4]
  - [src/autoresearch/api/streaming.py][m5]
  - [src/autoresearch/api/utils.py][m6]
- Scripts
  - [scripts/api_stream_order_sim.py][s1]
  - [scripts/api_auth_credentials_sim.py][s2]
- Tests
  - [tests/unit/test_api.py][t1]
  - [tests/unit/test_api_error_handling.py][t2]
  - [tests/unit/test_api_imports.py][t3]
  - [tests/unit/test_api_auth_middleware.py][t4]
  - [tests/unit/test_api_auth_deps.py][t5]
  - [tests/unit/test_webhooks_logging.py][t12]
  - [tests/integration/test_api.py][t14]
  - [tests/integration/test_api_additional.py][t15]
  - [tests/integration/test_api_auth.py][t6]
  - [tests/integration/test_api_auth_middleware.py][t7]
  - [tests/integration/test_api_auth_permissions.py][t16]
  - [tests/integration/test_api_docs.py][t9]
  - [tests/integration/test_api_streaming.py][t8]
  - [tests/integration/test_api_streaming_webhook.py][t10]
  - [tests/integration/test_api_versioning.py][t17]
  - [tests/integration/test_api_hot_reload.py][t18]
  - [tests/analysis/test_api_streaming_sim.py][t11]
  - [tests/analysis/test_api_stream_order_sim.py][t13]

[m1]: ../../src/autoresearch/api/__init__.py
[m2]: ../../src/autoresearch/api/auth_middleware.py
[m3]: ../../src/autoresearch/api/middleware.py
[m4]: ../../src/autoresearch/api/routing.py
[m5]: ../../src/autoresearch/api/streaming.py
[m6]: ../../src/autoresearch/api/utils.py
[t1]: ../../tests/unit/test_api.py
[t2]: ../../tests/unit/test_api_error_handling.py
[t3]: ../../tests/unit/test_api_imports.py
[t4]: ../../tests/unit/test_api_auth_middleware.py
[t5]: ../../tests/unit/test_api_auth_deps.py
[t6]: ../../tests/integration/test_api_auth.py
[t7]: ../../tests/integration/test_api_auth_middleware.py
[t8]: ../../tests/integration/test_api_streaming.py
[t9]: ../../tests/integration/test_api_docs.py
[t10]: ../../tests/integration/test_api_streaming_webhook.py
[t11]: ../../tests/analysis/test_api_streaming_sim.py
[t12]: ../../tests/unit/test_webhooks_logging.py
[t13]: ../../tests/analysis/test_api_stream_order_sim.py
[t14]: ../../tests/integration/test_api.py
[t15]: ../../tests/integration/test_api_additional.py
[t16]: ../../tests/integration/test_api_auth_permissions.py
[t17]: ../../tests/integration/test_api_versioning.py
[t18]: ../../tests/integration/test_api_hot_reload.py
[s1]: ../../scripts/api_stream_order_sim.py
[s2]: ../../scripts/api_auth_credentials_sim.py
