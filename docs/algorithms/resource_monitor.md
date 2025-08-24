# Resource Monitor

The `ResourceMonitor` samples CPU, memory, and GPU usage to expose
time-series metrics.

## Sampling Model

With a sampling interval `i` over runtime `T`, the monitor records
`n = T / i` observations. Average CPU `C` and memory `M` are

- `C = (1/n) \sum_{k=1}^{n} c_k`
- `M = (1/n) \sum_{k=1}^{n} m_k`

Each observation costs `O(1)`, so monitoring overhead grows linearly with
`n`.

## References

- [Prometheus Metrics Overview](https://prometheus.io/docs/concepts/metric_types/)
- [tests/integration/test_monitor_metrics.py](../../tests/integration/test_monitor_metrics.py)

