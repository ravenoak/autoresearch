# Orchestrator Performance

Efficient orchestration depends on balancing scheduling throughput with
resource limits. The distributed simulation models message handling across
worker processes and records CPU and memory use.

## Methodology

- Workers square integers to mimic message processing.
- `messages` defines items sent per loop and `loops` controls repetition.
- `ResourceMonitor` samples CPU and memory every 50 ms.
- Metrics include total messages processed, elapsed time, throughput, CPU
  percentage, and memory footprint.

## Formulas

- **Throughput:** `throughput = total_messages / duration_seconds`
- **CPU usage:** mean process CPU percent reported by the monitor.
- **Memory usage:** maximum resident set size in megabytes.

## Assumptions

- Messages are CPU bound and split across processes, enabling near-linear
  scaling as worker count increases.
- Sampling uses a short 50 ms interval to minimize monitoring overhead.
- GPU statistics are optional and may report zeros when unavailable.

## Tuning Guidance

- Increase `--workers` until CPU utilization approaches the number of cores.
  Extra workers beyond that point show diminishing throughput gains.
- Adjust `--messages` and `--loops` so total work amortizes startup costs.
- Watch memory usage when messages hold significant state; the monitor reports
  megabytes consumed by the parent process.
