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

[bench]: ../src/autoresearch/orchestrator_perf.py#L71-L112
