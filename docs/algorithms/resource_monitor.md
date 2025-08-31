# Resource Monitor

The `ResourceMonitor` samples CPU, memory, GPU, and token counts to expose
time-series metrics. The `monitor` CLI uses these helpers to print the current
snapshot in JSON or table form. Gauges reset to zero on startup so repeated
runs begin with clean metrics. Reset global counters between tests to avoid
cross-test contamination.

## Sampling Model

With a sampling interval `i` over runtime `T`, the monitor records
`n = T / i` observations. Average CPU `C` and memory `M` are

- `C = (1/n) \sum_{k=1}^{n} c_k`
- `M = (1/n) \sum_{k=1}^{n} m_k`

Variance captures spread in the observations. For CPU `S_C^2` and memory
`S_M^2` the unbiased estimators are

- `S_C^2 = (1/(n - 1)) \sum_{k=1}^{n} (c_k - C)^2`
- `S_M^2 = (1/(n - 1)) \sum_{k=1}^{n} (m_k - M)^2`

The `p`-quantile `Q_p` is approximated by sorting values and selecting
`x_{\lceil pn \rceil}`.

Sampling error of the mean decreases with more observations. The standard
error (expected deviation from the true mean) is

- `SE(C) = \sqrt{S_C^2 / n}`
- `SE(M) = \sqrt{S_M^2 / n}`

A 95% confidence interval for the CPU mean is `C \pm 1.96 * SE(C)`.

Each observation costs `O(1)`, so monitoring overhead grows linearly with
`n`.

Typical metrics include:

- `cpu_percent` and `memory_percent`
- `memory_used_mb` and `process_memory_mb`
- `gpu_percent` and `gpu_memory_mb`
- `tokens_in_total` and `tokens_out_total`

## References

- [Prometheus Metrics Overview]
- [tests/integration/test_monitor_metrics.py]
- [Sample Variance](https://en.wikipedia.org/wiki/Variance#Sample_variance)
- [Quantile](https://en.wikipedia.org/wiki/Quantile)
- [Standard Error](https://en.wikipedia.org/wiki/Standard_error)

[Prometheus Metrics Overview]: https://prometheus.io/docs/concepts/metric_types/
[tests/integration/test_monitor_metrics.py]: ../../tests/integration/test_monitor_metrics.py

## Simulation

Automated tests confirm resource monitor behavior.

- [Spec](../specs/resource-monitor.md)
- [Tests](../../tests/unit/test_resource_monitor_gpu.py)
