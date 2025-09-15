# API

## Overview
The API package wires FastAPI routers, authentication middleware, request
logging, and configuration hot reloading. `routing.create_app` loads the
configuration, starts storage, installs rate limiting, and registers
versioned routes for queries, streaming, configuration management, and
documentation.

## Algorithm
1. `AuthMiddleware` loads the latest `ConfigModel`, extracts credentials, and
   stores `request.state.permissions`.
2. `require_permission` halts requests without the requisite capability,
   returning **401** or **403** where appropriate.
3. Route handlers call `validate_version` for versioned models before invoking
   the orchestrator or configuration helpers.
4. Query handlers optionally clone the configuration with request overrides,
   run orchestrator queries inside tracing spans, and deliver webhook
   notifications with retries.
5. Streaming endpoints create an `asyncio.Queue`, stream newline-delimited
   JSON, and emit blank heartbeat lines on idle cycles.
6. Async endpoints manage futures in `app.state.async_tasks`, returning status
   JSON until results resolve or cancellation succeeds.
7. Configuration routes use `ConfigLoader` to merge, replace, or reload
   models, surfacing `HTTPException` errors when validation fails.

## Route Coverage
- **POST /query** (`query`): Synchronous queries or `?stream=true` streaming.
- **POST /query/stream** (`query`): Dedicated streaming endpoint.
- **POST /query/batch** (`query`): Paginated batches with `asyncio.TaskGroup`.
- **POST /query/async** (`query`): Background queries with task identifiers.
- **GET /query/{query_id}** (`query`): Async status or final payload.
- **DELETE /query/{query_id}** (`query`): Cancels async tasks and prunes state.
- **GET /health** (`health`): Reports readiness after startup.
- **GET /capabilities** (`capabilities`): Exposes modes, storage, search, and
  agent descriptors.
- **GET /config** (`config`): Returns current configuration.
- **PUT /config** (`config`): Merges updates and notifies observers.
- **POST /config** (`config`): Replaces configuration after validation.
- **DELETE /config** (`config`): Reloads configuration from disk.
- **GET /metrics** (`metrics`): Prometheus endpoint when monitoring is
  enabled.
- **GET /docs** (`docs`): Swagger UI behind docs permission.
- **GET /openapi.json** (`docs`): OpenAPI schema and descriptive metadata.

## Proof sketch
- Authentication: constant-time comparisons and permission enforcement ensure
  only authorised clients reach handlers.
- Version handling: `validate_version` rejects unsupported schemas before
  orchestration begins.
- Async management: futures remain in `app.state.async_tasks` until retrieval
  or cancellation, preventing leaks.
- Configuration safety: `ConfigLoader` validation guarantees only well-formed
  models reach observers, preserving runtime stability.

## Simulation
- [scripts/api_auth_credentials_sim.py][sim-credentials] exercises credential
  success and failure cases.
- [scripts/api_stream_order_sim.py][sim-stream-order] verifies streaming order
  and heartbeat cadence.

## References
- [Code](../../src/autoresearch/api/)
- [Spec](../specs/api.md)
- Tests:
  - [tests/unit/test_api.py][test-api-unit]
  - [tests/unit/test_api_auth_middleware.py][test-api-auth-mw]
  - [tests/integration/test_api_docs.py][test-api-docs]
  - [tests/integration/test_api_streaming.py][test-api-streaming]

[sim-credentials]: ../../scripts/api_auth_credentials_sim.py
[sim-stream-order]: ../../scripts/api_stream_order_sim.py
[test-api-unit]: ../../tests/unit/test_api.py
[test-api-auth-mw]: ../../tests/unit/test_api_auth_middleware.py
[test-api-docs]: ../../tests/integration/test_api_docs.py
[test-api-streaming]: ../../tests/integration/test_api_streaming.py
