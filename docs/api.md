# API Usage

The HTTP API is served via FastAPI. Start the server with Uvicorn:

```bash
uvicorn autoresearch.api:app --reload
```

Once the server is running you can interact with the endpoints described below.

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
queries are processed. Both parameters start counting at 1.

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

When multiple API keys with different roles are needed, define `[api].api_keys`
as a mapping from key to role:

```toml
[api]
api_keys = {admin = "secret1", user = "secret2"}
```

Include the desired key in the `X-API-Key` header. The associated role will be
available as `request.state.role` inside the application.

### Role permissions

Use `[api].role_permissions` to restrict which endpoints each role can call.
Permissions are `query`, `metrics` and `capabilities`.

```toml
[api.role_permissions]
admin = ["query", "metrics", "capabilities"]
user = ["query"]
```

By default `user` can only submit queries while `admin` has access to all
endpoints.

## Throttling

Rate limiting is configured via `[api].rate_limit` or the environment variable
`AUTORESEARCH_API__RATE_LIMIT`. This value specifies the number of requests per
minute allowed for each client IP. Set to `0` to disable throttling.

The implementation uses [SlowAPI](https://pypi.org/project/slowapi/), so limits
are enforced per client IP address.

```bash
export AUTORESEARCH_API__RATE_LIMIT=2
curl -d '{"query": "test"}' http://localhost:8000/query
```

