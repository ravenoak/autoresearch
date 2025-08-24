# Resource Monitor

The `ResourceMonitor` samples CPU, memory, GPU, and token counts to expose
time-series metrics. The `monitor` CLI uses these helpers to print the current
snapshot in JSON or table form.

## Sampling Model

With a sampling interval `i` over runtime `T`, the monitor records
`n = T / i` observations. Average CPU `C` and memory `M` are

- `C = (1/n) \sum_{k=1}^{n} c_k`
- `M = (1/n) \sum_{k=1}^{n} m_k`

Each observation costs `O(1)`, so monitoring overhead grows linearly with
`n`.

Typical metrics include:

- `cpu_percent` and `memory_percent`
- `memory_used_mb` and `process_memory_mb`
- `gpu_percent` and `gpu_memory_mb`
- `tokens_in_total` and `tokens_out_total`

## References

- [Prometheus Metrics Overview](https://prometheus.io/docs/concepts/metric_types/)
- [tests/integration/test_monitor_metrics.py](../../tests/integration/test_monitor_metrics.py)

