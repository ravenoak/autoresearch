# Monitoring

Autoresearch exposes system and node metrics via Prometheus. The
`SystemMonitor` collects CPU and memory statistics, while the
`NodeHealthMonitor` reports connectivity to Redis and Ray and provides a
simple health indicator.

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
