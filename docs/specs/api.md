# API

## Overview

The Autoresearch API assembles a FastAPI application that exposes query,
configuration, documentation, and monitoring endpoints. `routing.create_app`
initialises `StorageManager`, enters the configuration watch context, and
installs `AuthMiddleware` plus the active rate limiting middleware before
mounting the router built around `QueryRequestV1`/`QueryResponseV1`. Shared
state stores the `ConfigLoader`, `RequestLogger`, limiter, and async task
registry so routes can reload configuration, track usage, and dispatch
webhooks. Related derivations live in:

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

- `AuthMiddleware.dispatch` reloads the current configuration via
  `ConfigLoader.load_config()` so file edits take effect before credential
  checks.
- When `[api].api_keys` is populated the middleware iterates each candidate and
  compares it with `secrets.compare_digest`; otherwise it checks a single
  `api_key`. Missing or invalid keys short-circuit with **401** responses that
  carry an `API-Key` challenge.
- If a bearer token is configured the middleware verifies it with
  `verify_bearer_token`. Bearer credentials can satisfy authentication on their
  own. When a token is present but invalid the middleware returns **401** even
  if the accompanying API key was correct.
- The resolved role, permissions, and active challenge scheme are recorded on
  `request.scope["state"]`. Downstream dependencies call `enforce_permission`,
  which returns **401** with the stored challenge when credentials are absent
  and **403** when permissions are insufficient.
- When no credentials are configured the middleware leaves the role as
  `anonymous` and grants an empty permission set so open deployments remain
  usable.

## Routing and Endpoints

- **POST /query** (`query`): Handles synchronous queries and toggles streaming
  when the `stream` query parameter is truthy.
- **POST /query/stream** (`query`): Streams newline-delimited JSON and emits
  heartbeat blank lines every 15 seconds.
- **POST /query/batch** (`query`): Executes paginated batches concurrently
  using `asyncio.TaskGroup`.
- **POST /query/async** (`query`): Starts background work and returns an async
  identifier stored in `app.state.async_tasks`.
- **GET /query/{query_id}** (`query`): Reports async status or emits the final
  payload before clearing stored futures.
- **DELETE /query/{query_id}** (`query`): Cancels async work and removes task
  state.
- **GET /health** (`health`): Reports readiness once storage and configuration
  loaders finish.
- **GET /capabilities** (`capabilities`): Lists reasoning modes, storage and
  search metadata, agent descriptors, and the active configuration subset.
- **GET /config** (`config`): Returns the active configuration as JSON.
- **PUT /config** (`config`): Merges updates, validates them, and notifies
  observers.
- **POST /config** (`config`): Replaces configuration after validation.
- **DELETE /config** (`config`): Reloads configuration from disk and
  broadcasts the new model.
- **GET /metrics** (`metrics`): Exports Prometheus metrics when monitoring is
  enabled; `routes.py` removes the route otherwise.
- **GET /docs** (`docs`): Serves Swagger UI with CDN-backed assets.
- **GET /openapi.json** (`docs`): Provides the OpenAPI schema and metadata.

- `POST /query` validates the request version, applies optional overrides
  (`reasoning_mode`, `loops`, `llm_backend`) directly to the shared config,
  enables tracing, runs the orchestrator, and formats errors with
  `format_error_for_api`. Results and failures are forwarded to per-request or
  global webhooks using configurable retry and backoff values.
- `POST /query/batch` paginates via `page` and `page_size`, then reuses
  `query_endpoint` for each slice within an `asyncio.TaskGroup`. The response
  order matches the original batch.
- `POST /query/async` clones the config (`ConfigModel.model_copy(deep=True)`),
  launches `run_query_async`, and stores the resulting future under a UUID.
  Futures live in `app.state.async_tasks`.
- `GET /query/{query_id}` returns JSON status while the future is pending,
  serialises `QueryResponse` or `QueryResponseV1` results when complete, and
  removes the stored future. `DELETE` cancels the task and responds with plain
  text.
- `POST /query/stream` and `POST /query?stream=true` share
  `query_stream_endpoint`, which pushes partial responses into an `asyncio`
  queue and yields newline-delimited JSON interleaved with keepalive blanks
  until completion.
- Configuration routes rely on `ConfigLoader` to validate updates, replace
  state, broadcast observer notifications, and map `ValidationError` instances
  to structured `HTTPException` responses.
- `create_app` mounts the router, registers `handle_rate_limit` for
  `RateLimitExceeded`, and stores the loader, limiter, request logger, and
  async task dictionary on `app.state`.

## Rate Limiting and Logging

- Both middleware variants rely on `RequestLogger.log` to track per-IP counts.
  When SlowAPI is available `RateLimitMiddleware` also delegates to
  `Limiter.limiter.hit` to enforce quotas.
- `dynamic_limit` renders `[api].rate_limit` as a `limits` string and falls back
  to `1000000/minute` when throttling is disabled so parsers still succeed.
- Each request stores `(limit, [ip])` on `request.state.view_rate_limit`, and
  either middleware injects standard headers through the limiter or stub.
  `handle_rate_limit` is registered as the exception handler for
  `RateLimitExceeded`.

## Algorithms

1. **Version validation:** `validate_version` rejects deprecated or unknown
   schema versions before any orchestration work begins.
2. **Authentication:** `AuthMiddleware.dispatch` reloads configuration and
   validates API keys plus bearer tokens in constant time. It records the
   resolved role, permissions, and active challenge scheme on the request,
   then returns the appropriate `WWW-Authenticate` header when checks fail.
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
- The application lifespan enters the configuration watch context during
  startup and stops it on shutdown to keep `ConfigLoader` state consistent.
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
  - [tests/analysis/test_api_stream_order_sim.py][t15]
  - [tests/analysis/test_api_streaming_sim.py][t16]
  - [tests/integration/test_api_extra.py][t17]
  - [tests/integration/test_api_additional.py][t18]
  - [tests/integration/test_api_auth.py][t19]
  - [tests/integration/test_api_auth_middleware_extra.py][t20]
  - [tests/integration/test_api_auth_permissions.py][t21]
  - [tests/integration/test_api_docs.py][t22]
  - [tests/integration/test_api_hot_reload.py][t23]
  - [tests/integration/test_api_streaming.py][t24]
  - [tests/integration/test_api_streaming_webhook.py][t25]
  - [tests/integration/test_api_versioning.py][t26]
  - [tests/unit/legacy/test_api.py][t27]
  - [tests/unit/legacy/test_api_auth_deps.py][t28]
  - [tests/unit/legacy/test_api_auth_middleware.py][t29]
  - [tests/unit/legacy/test_api_error_handling.py][t30]
  - [tests/unit/legacy/test_api_imports.py][t31]
  - [tests/unit/legacy/test_webhooks_logging.py][t32]
  - [tests/unit/legacy/test_property_api_rate_limit_bounds.py][t33]

[m1]: ../../src/autoresearch/api/__init__.py
[m2]: ../../src/autoresearch/api/auth_middleware.py
[m3]: ../../src/autoresearch/api/middleware.py
[m4]: ../../src/autoresearch/api/routing.py
[m5]: ../../src/autoresearch/api/streaming.py
[m6]: ../../src/autoresearch/api/utils.py
[t15]: ../../tests/analysis/test_api_stream_order_sim.py
[t16]: ../../tests/analysis/test_api_streaming_sim.py
[t17]: ../../tests/integration/test_api_extra.py
[t18]: ../../tests/integration/test_api_additional.py
[s1]: ../../scripts/api_stream_order_sim.py
[s2]: ../../scripts/api_auth_credentials_sim.py

[t19]: ../../tests/integration/test_api_auth.py
[t20]: ../../tests/integration/test_api_auth_middleware_extra.py
[t21]: ../../tests/integration/test_api_auth_permissions.py
[t22]: ../../tests/integration/test_api_docs.py
[t23]: ../../tests/integration/test_api_hot_reload.py
[t24]: ../../tests/integration/test_api_streaming.py
[t25]: ../../tests/integration/test_api_streaming_webhook.py
[t26]: ../../tests/integration/test_api_versioning.py
[t27]: ../../tests/unit/legacy/test_api.py
[t28]: ../../tests/unit/legacy/test_api_auth_deps.py
[t29]: ../../tests/unit/legacy/test_api_auth_middleware.py
[t30]: ../../tests/unit/legacy/test_api_error_handling.py
[t31]: ../../tests/unit/legacy/test_api_imports.py
[t32]: ../../tests/unit/legacy/test_webhooks_logging.py
[t33]: ../../tests/unit/legacy/test_property_api_rate_limit_bounds.py
