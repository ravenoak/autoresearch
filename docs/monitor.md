# Monitoring

Autoresearch exposes system and node metrics via Prometheus. The
`SystemMonitor` collects CPU and memory statistics, while the
`NodeHealthMonitor` reports connectivity to Redis and Ray and provides a
simple health indicator.

Set `api.monitoring_enabled` to `true` to expose the `/metrics` endpoint on
the API server.

```python
from autoresearch.monitor.node_health import NodeHealthMonitor

monitor = NodeHealthMonitor(
    redis_url="redis://localhost:6379/0", port=8000
)
monitor.start()
```

The monitor runs an HTTP server that serves `/metrics` and performs checks
at a fixed interval. Gauges include `autoresearch_redis_up`,
`autoresearch_ray_up`, and `autoresearch_node_health`. Use Prometheus to
scrape the metrics and set alerts when values drop to `0`.

When API authentication is enabled, include the `X-API-Key` header:

```bash
curl -i -H "X-API-Key: $AUTORESEARCH_API_KEY" \
  http://localhost:8000/metrics
```

Missing keys produce:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: API-Key
{"detail": "Missing API key"}
```

## CLI usage

Run the monitor command to print current CPU and memory usage:

```bash
uv run autoresearch monitor
```

The command outputs a single JSON object containing `cpu_percent`,
`memory_percent`, token counters, and more. Query and token counters are
initialised to `0` when no queries have been executed so they always appear
in the output. Pass `--watch` to refresh the metrics continuously.
