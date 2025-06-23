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

## Authentication

Set the `AUTORESEARCH_API_KEY` environment variable to enable API key
authentication. Clients must include this key in the `X-API-Key` header for
every request.

```bash
export AUTORESEARCH_API_KEY=mysecret
curl -H "X-API-Key: $AUTORESEARCH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' http://localhost:8000/query
```

## Throttling

Requests can be rate limited by setting `AUTORESEARCH_RATE_LIMIT` to the number
of requests allowed per minute for each client IP. The feature is disabled when
the variable is unset or set to `0`.

```bash
export AUTORESEARCH_RATE_LIMIT=2
curl -d '{"query": "test"}' http://localhost:8000/query
```

