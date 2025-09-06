# Distributed Coordination

Autoresearch can dispatch agents across processes or nodes. The
`ProcessExecutor` uses Python's `multiprocessing` module, while
`RayExecutor` runs agents on a Ray cluster. Both executors share data
through a message broker:

- `memory`: in-process queues suitable for local testing.
- `redis`: uses a Redis instance for cross-node communication.
- `ray`: relies on Ray's distributed queue actor.

Configure the executor in `ConfigModel.distributed_config` and set the
`message_broker` field to one of the above options. The optional
`broker_url` provides the Redis connection string. For Ray, ensure a
cluster is running and specify its address in `distributed_config`.

When the distributed flag is enabled, claims are persisted by a storage
coordinator and agent results are aggregated asynchronously. Each broker
supports a `publish` method and a `queue` attribute with `put` and `get`
operations.

## Orchestrator Simulation

The `distributed_orchestrator_sim.py` script models scheduling and resource
usage for a pool of worker processes. Each task incurs a dispatch delay and an
execution time, giving a simple formula for end-to-end latency:

- `avg_latency_s = mean(completion - dispatch_start)`
- `throughput = tasks / total_duration`
- `cpu_percent` and `memory_mb` are sampled by `ResourceMonitor`.

### Methodology

1. Start `ResourceMonitor` with a 50 ms sampling interval.
2. For each task, wait for `network_latency` seconds to simulate dispatch, then
   execute a sleep of `task_time` seconds on a worker.
3. Record start and completion times to compute average scheduling latency.
4. Aggregate throughput and resource metrics after all tasks finish.

### Example Results

Running the command below produced the metrics that follow:

```
uv run scripts/distributed_orchestrator_sim.py --workers 2 --tasks 20 \
    --network-latency 0.01 --task-time 0.01
```

```
{
  "avg_latency_s": 0.075,
  "throughput": 97.16,
  "cpu_percent": 0.0,
  "memory_mb": 45.06
}
```

These formulas and metrics help tune worker counts and latency budgets when
deploying the distributed orchestrator.

## Performance benchmark

Assumptions:

- 100 tasks per run with 5 ms network latency.
- Task times varied: 5, 10, and 20 ms.

Formulas:

- `avg_latency_s = mean(completion - dispatch_start)`
- `throughput = tasks / total_duration`
- `memory_mb` sampled by `ResourceMonitor`

| task_time (ms) | workers | avg_latency_ms | throughput | memory_mb |
| -------------- | ------- | -------------- | ---------- | --------- |
| 5 | 1 | 13.76 | 72.67 | 49.76 |
| 5 | 2 | 8.52 | 117.43 | 50.01 |
| 5 | 3 | 7.62 | 131.15 | 50.01 |
| 5 | 4 | 7.02 | 142.45 | 50.13 |
| 10 | 1 | 17.15 | 58.29 | 49.65 |
| 10 | 2 | 12.24 | 81.72 | 50.02 |
| 10 | 3 | 8.84 | 113.17 | 49.90 |
| 10 | 4 | 7.38 | 135.51 | 50.02 |
| 20 | 1 | 26.62 | 37.57 | 49.92 |
| 20 | 2 | 16.18 | 61.82 | 50.17 |
| 20 | 3 | 11.73 | 85.23 | 49.97 |
| 20 | 4 | 9.49 | 105.33 | 50.10 |

Longer task times inflate latency and cap throughput. Scaling workers restores
performance and keeps memory use near 50 MB.

### Future work

- Benchmark with bursty task arrivals to mimic real traffic.
- Expose a hook to suppress GPU warnings when no accelerator is present.
