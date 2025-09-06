# Orchestrator performance

The benchmark uses `benchmark_scheduler` from
[src/autoresearch/orchestrator_perf.py][bench] to measure throughput of a simple
scheduler. Tasks sleep for one millisecond and allocate no memory. For each
worker count we derive latency as the inverse of observed throughput and model
arrivals at ninety five percent of capacity to estimate expected queue length.

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 823.69 | 1.214 | 18.05 |
| 2 | 1648.93 | 0.606 | 17.59 |
| 4 | 3270.70 | 0.306 | 16.94 |
| 8 | 5551.16 | 0.180 | 16.04 |

Throughput scales nearly linearly while latency falls. Queue length remains high
when arrivals approach capacity, signaling saturation risk.

## High-load scheduling benchmark

We simulated 100 tasks with 0.5 MB each, arriving at 45 tasks/s while each
worker served 50 tasks/s. A single worker ran near saturation, but adding
workers scaled throughput and drained the queue.

| workers | utilization | throughput (tasks/s) | avg queue length |
| ------- | ----------- | ------------------- | ---------------- |
| 1 | 0.90 | 802.03 | 8.10 |
| 2 | 0.45 | 1586.84 | 0.23 |
| 3 | 0.30 | 2236.15 | 0.03 |
| 4 | 0.23 | 2846.91 | 0.00 |

Expanding the worker pool sharply reduced queueing. If workers cannot scale or
arrivals spike, mitigation relies on admission control.

## Distributed throughput model

Assumptions follow the M/M/c queue with network delay in
[algorithms/distributed_perf.md](algorithms/distributed_perf.md). Tasks arrive
at rate `\lambda` with network delay `d`, each worker processes `\mu` tasks/s,
and arrivals and service times are exponential with utilization below one.

Formulas:

- Utilization `\rho = \lambda / (c\mu)`.
- Average queue length `L_q` and waiting time `W_q = L_q / \lambda`.
- Latency `T = d + W_q + 1/\mu`.
- Throughput equals `\lambda` when `\rho < 1`.

We varied arrival and service rates using
`uv run scripts/distributed_perf_sim.py --max-workers 4 --network-delay 0.005`.

### Arrival 50 tasks/s, service 80 tasks/s

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 50.00 | 38.33 | 1.04 |
| 2 | 50.00 | 18.85 | 0.07 |
| 3 | 50.00 | 17.64 | 0.01 |
| 4 | 50.00 | 17.51 | 0.00 |

### Arrival 80 tasks/s, service 100 tasks/s

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 80.00 | 55.00 | 3.20 |
| 2 | 80.00 | 16.90 | 0.15 |
| 3 | 80.00 | 15.24 | 0.02 |
| 4 | 80.00 | 15.03 | 0.00 |

### Arrival 120 tasks/s, service 150 tasks/s

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 120.00 | 38.33 | 3.20 |
| 2 | 120.00 | 12.94 | 0.15 |
| 3 | 120.00 | 11.82 | 0.02 |
| 4 | 120.00 | 11.69 | 0.00 |

Higher service rates relative to arrivals shrink queues and drive latency
toward the 5 ms network delay.

## Mitigation strategies

- Expand worker pools to dilute utilization when backlog grows.
- Throttle arrivals to keep utilization below capacity during spikes.
- Enforce queue limits with backpressure to bound memory use.
- Shed load when limits are exceeded to protect the orchestrator.

[bench]: ../src/autoresearch/orchestrator_perf.py#L71-L112

## Follow-up benchmarks and monitoring

- Benchmark scenarios with non-exponential arrivals to stress test bursty
  workloads.
- Expose queue length and latency metrics via a monitoring hook to detect
  saturation in production.
