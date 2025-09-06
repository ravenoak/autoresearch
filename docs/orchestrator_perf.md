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

## Distributed throughput model

Assumptions follow the M/M/c queue with network delay in
[algorithms/distributed_perf.md](algorithms/distributed_perf.md):

- Tasks arrive at 100 tasks/s with a 5 ms network delay.
- Each worker processes 120 tasks/s.
- Arrivals and service times are exponential with utilization below one.

Formulas:

- Utilization `\rho = \lambda / (c\mu)`.
- Average queue length `L_q` and waiting time `W_q = L_q / \lambda`.
- Latency `T = d + W_q + 1/\mu`.
- Throughput equals `\lambda` when `\rho < 1`.

Results from
`uv run scripts/distributed_perf_sim.py --max-workers 4 --arrival-rate 100 \\
    --service-rate 120 --network-delay 0.005`:

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 100.00 | 55.000 | 4.17 |
| 2 | 100.00 | 15.084 | 0.18 |
| 3 | 100.00 | 13.555 | 0.02 |
| 4 | 100.00 | 13.362 | 0.00 |

Network delay dominates latency; additional workers cut queueing after two
processes.

## Arrival and service rate sensitivity

Assumptions:

- Service rate fixed at 100 tasks/s per worker.
- Network delay 5 ms.
- Arrival rates at 50, 75, and 90 tasks/s.

Formulas mirror the M/M/c model above.

### λ = 50 tasks/s, μ = 100 tasks/s

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 50.00 | 25.000 | 0.50 |
| 2 | 50.00 | 15.667 | 0.03 |
| 3 | 50.00 | 15.061 | 0.00 |
| 4 | 50.00 | 15.005 | 0.00 |

### λ = 75 tasks/s, μ = 100 tasks/s

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 75.00 | 45.000 | 2.25 |
| 2 | 75.00 | 16.636 | 0.12 |
| 3 | 75.00 | 15.197 | 0.01 |
| 4 | 75.00 | 15.024 | 0.00 |

### λ = 90 tasks/s, μ = 100 tasks/s

| workers | throughput (tasks/s) | latency (ms) | avg queue length |
| ------- | ------------------- | ------------ | ---------------- |
| 1 | 90.00 | 105.000 | 8.10 |
| 2 | 90.00 | 17.539 | 0.23 |
| 3 | 90.00 | 15.333 | 0.03 |
| 4 | 90.00 | 15.046 | 0.00 |

Rising arrival rates inflate latency for a single worker. Adding workers
restores sub-20 ms response times and limits queue growth.

### Future work

- Benchmark non-exponential arrivals to test robustness to bursts.
- Hook production metrics to compare predicted and observed queue lengths.

[bench]: ../src/autoresearch/orchestrator_perf.py#L71-L112
