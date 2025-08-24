# API Usage

The HTTP API is served via FastAPI. Start the server with Uvicorn:

```bash
uvicorn autoresearch.api:app --reload
```

Once the server is running you can interact with the endpoints described below.

For details on orchestrator state transitions and the API contract see
[orchestrator_state.md](orchestrator_state.md).

## Configuration

API settings live in `autoresearch.toml` under `[api]` or via environment
variables. Common options include:

- `AUTORESEARCH_API__API_KEY`
- `AUTORESEARCH_API__API_KEYS`
- `AUTORESEARCH_API__BEARER_TOKEN`
- `AUTORESEARCH_API__ROLE_PERMISSIONS`
- `AUTORESEARCH_API__RATE_LIMIT`

Restart the server after changing these values.

## Endpoints

### `POST /query`

Send a research question and receive the answer, citations, reasoning steps and
a metrics summary.

**Request**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain machine learning"}'
```

Pass `stream=true` as a query parameter to receive incremental updates instead
of a single response:

```bash
curl -X POST 'http://localhost:8000/query?stream=true' \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain machine learning"}'
```

**Response**

```json
{
  "answer": "Machine learning is ...",
  "citations": ["https://example.com"],
  "reasoning": ["step 1", "step 2"],
  "metrics": {
    "cycles_completed": 1,
    "total_tokens": {"input": 5, "output": 7, "total": 12}
  }
}
```

### `POST /query/stream`

Stream incremental responses as each reasoning cycle completes. The endpoint
returns newline-delimited JSON objects.

```bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain AI"}'
```

### `POST /query/batch`

Execute multiple queries in one request with pagination support.

```bash
curl -X POST 'http://localhost:8000/query/batch?page=2&page_size=2' \
  -H "Content-Type: application/json" \
  -d '{"queries": [{"query": "q1"}, {"query": "q2"}, {"query": "q3"}, {"query": "q4"}]}'
```

Use the `page` and `page_size` query parameters to control which subset of
queries are processed. Both parameters start counting at 1. If omitted,
`page` defaults to `1` and `page_size` defaults to `10`.

### Webhook notifications

Include a `webhook_url` in the request body to have the final result sent via
`POST` to that URL:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "hi", "webhook_url": "http://localhost:9000/hook"}'
```

Additionally, any URLs listed under `[api].webhooks` in `autoresearch.toml`
receive the same payload after each query completes.

### `GET /metrics`

Return Prometheus metrics collected during query processing.

**Request**

```bash
curl http://localhost:8000/metrics
```

**Response**

```
# HELP autoresearch_queries_total Total number of queries processed
# TYPE autoresearch_queries_total counter
autoresearch_queries_total 1.0
...
```

### `GET /capabilities`

Return information about available agents, LLM backends and current settings.

```bash
curl http://localhost:8000/capabilities
```

**Response**

```json
{
  "version": "1.0.0",
  "llm_backends": ["mock"],
  "reasoning_modes": ["simple"],
  "current_config": {
    "reasoning_mode": "simple",
    "loops": 1,
    "llm_backend": "mock"
  }
}
```

### `GET /health`

Check whether the API server is running.

```bash
curl http://localhost:8000/health
```

### `GET /config`

Return the current configuration as JSON.

```bash
curl http://localhost:8000/config
```

### `POST /config`

Replace the entire configuration with the JSON body.

```bash
curl -X POST http://localhost:8000/config -H "Content-Type: application/json" \
     -d '{"loops": 2, "llm_backend": "mock"}'
```

**Response**

```json
{
  "loops": 2,
  "llm_backend": "mock",
  ...
}
```

### `PUT /config`

Update configuration values at runtime. Only fields present in the JSON body are
modified.

```bash
curl -X PUT http://localhost:8000/config -H "Content-Type: application/json" \
     -d '{"loops": 3}'
```

### `DELETE /config`

Reload configuration from disk and discard runtime changes.

```bash
curl -X DELETE http://localhost:8000/config
```

### `POST /query/async`

Run a query in the background and return an identifier. Queries are
scheduled as `asyncio.Task` objects within the server's event loop, and the
task ID can be used to poll for completion or cancel the work.

```bash
curl -X POST http://localhost:8000/query/async \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain AI"}'
```

**Response**

```json
{"query_id": "123e4567-e89b-12d3-a456-426614174000"}
```

Check the result with `GET /query/<id>`:

```bash
curl http://localhost:8000/query/<id>
```

Example response while running:

```json
{"status": "running"}
```

When complete:

```json
{
  "answer": "AI explanation",
  "citations": [],
  "reasoning": [],
  "metrics": {}
}
```

### `DELETE /query/<id>`

Cancel a running asynchronous query and remove it from the server. The task is
cancelled using `Task.cancel()` and deleted from the in-memory registry.

```bash
curl -X DELETE http://localhost:8000/query/<id>
```

Returns `canceled` when the task is terminated. If the query already
completed, the task will have been removed and the endpoint responds with
**404**.

 

## Authentication

Enable API key authentication by setting `[api].api_key` in `autoresearch.toml`
or the environment variable `AUTORESEARCH_API__API_KEY`. Clients must include
this key in the `X-API-Key` header for every request.

```bash
export AUTORESEARCH_API__API_KEY=mysecret
curl -H "X-API-Key: $AUTORESEARCH_API__API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' http://localhost:8000/query
```

Alternatively, set `[api].bearer_token` or `AUTORESEARCH_API__BEARER_TOKEN` to
enable bearer token authentication. Pass this token in the `Authorization` header:

```bash
export AUTORESEARCH_API__BEARER_TOKEN=mytoken
curl -H "Authorization: Bearer $AUTORESEARCH_API__BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' http://localhost:8000/query
```

Generate random tokens with `generate_bearer_token`:

```python
from autoresearch.api.utils import generate_bearer_token
token = generate_bearer_token()
```

Token comparison uses constant-time verification to guard against timing
attacks.

When multiple API keys with different roles are needed, define `[api].api_keys`
as a mapping from key to role:

```toml
[api]
api_keys = {admin = "secret1", user = "secret2"}
```

Include the desired key in the `X-API-Key` header. The associated role will be
available as `request.state.role` inside the application.

If both API keys and a bearer token are configured, either credential grants
access. When both headers are sent, a valid bearer token overrides an incorrect
`X-API-Key` value. The documentation routes `/docs` and `/openapi.json` require
the `docs` permission and are protected when authentication is enabled.

### Headers

Use these HTTP headers when authentication is enabled:

- `X-API-Key`: API key from `[api].api_key` or the `[api].api_keys` mapping.
- `Authorization: Bearer <token>`: bearer token from `[api].bearer_token`.

Requests with missing or invalid credentials receive a **401 Unauthorized**
response. Authenticated clients lacking permission receive **403 Forbidden**.

### Role permissions

Use `[api].role_permissions` to restrict which endpoints each role can call.
Permissions are `query`, `docs`, `metrics`, `capabilities`, `config` and
`health`.

```toml
[api.role_permissions]
admin = ["query", "docs", "metrics", "capabilities", "config", "health"]
user = ["query", "docs"]
```

By default `user` can submit queries and view documentation, while `admin`
has access to all endpoints.

## Throttling

Rate limiting is configured via `[api].rate_limit` or the environment variable
`AUTORESEARCH_API__RATE_LIMIT`. This value specifies the number of requests per
minute allowed for each client IP. Set to `0` to disable throttling.

The implementation uses [SlowAPI](https://pypi.org/project/slowapi/), so limits
are enforced per client IP address.

When the limit is exceeded the API returns **429 Too Many Requests** and
includes a `Retry-After` header specifying when you may try again.

```bash
export AUTORESEARCH_API__RATE_LIMIT=2
curl -d '{"query": "test"}' http://localhost:8000/query
```

