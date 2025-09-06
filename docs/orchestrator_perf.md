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

## Mitigation strategies

- Backpressure caps the number of in-flight tasks when queues grow too long.
- Adaptive worker pools expand or shrink based on backlog and utilization.

[bench]: ../src/autoresearch/orchestrator_perf.py#L71-L112
