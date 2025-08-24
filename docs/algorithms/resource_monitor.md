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

## Variance and Quantiles

Sample variance for CPU and memory is

- `V_C = (1/(n-1)) \sum_{k=1}^{n} (c_k - C)^2`
- `V_M = (1/(n-1)) \sum_{k=1}^{n} (m_k - M)^2`

The empirical `p`-quantile `Q_p` is the `k = \lceil p n \rceil`th value after
sorting the observations. CPU and memory quantiles follow this definition
equally.

## Sampling Error

Assuming independent samples, the standard error of the mean is

- `SE_C = \sqrt{V_C / n}`
- `SE_M = \sqrt{V_M / n}`

For a quantile `Q_p` with density `f(Q_p)`, the asymptotic standard error is

- `SE_{Q_p} = \sqrt{p (1-p) / (n f(Q_p)^2)}`

These bounds approximate expected deviations between sample estimates and true
resource usage.

## References

- [Prometheus Metrics Overview](
  https://prometheus.io/docs/concepts/metric_types/)
- [tests/integration/test_monitor_metrics.py](
  ../../tests/integration/test_monitor_metrics.py)
- [Sample variance](https://en.wikipedia.org/wiki/Variance#Sample_variance)
- [Quantile](https://en.wikipedia.org/wiki/Quantile)
- [Standard error](https://en.wikipedia.org/wiki/Standard_error)

