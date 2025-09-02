# Orchestrator Performance

Efficient orchestration depends on balancing scheduling throughput with
resource limits. The distributed simulation measures how many tasks can be
completed per second and the CPU and memory costs of that workload.

## Formulas

- **Throughput:** `throughput = total_tasks / duration_seconds`
- **CPU usage:** Average process CPU percentage reported by the resource
  monitor.
- **Memory usage:** Maximum resident set size in megabytes.

## Assumptions

- Tasks are CPU bound and split across processes, enabling near-linear
  scaling when additional workers are available.
- Sampling uses a short 50 ms interval to minimize monitoring overhead.
- GPU statistics are optional and may report zeros when unavailable.

## Tuning Guidance

- Increase `--workers` until CPU utilization approaches the number of
  cores. Additional workers beyond that point may offer diminishing
  throughput gains.
- Adjust `--tasks` and `--loops` to keep total work large enough to amortize
  startup costs.
- Watch memory usage when tasks hold significant state; the monitor reports
  megabytes consumed by the parent process.
