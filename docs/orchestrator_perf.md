# Orchestrator performance

The scheduling benchmark models an M/M/c queue where tasks arrive at rate
$\lambda$ and each of $c$ workers serves tasks at rate $\mu$. Utilization is
$\rho = \lambda / (c\mu)$ and requires $\rho < 1$ for stability. The average
queue length $L_q$ follows:

$$L_q = \frac{(\lambda/\mu)^c \rho}{c! (1-\rho)^2} P_0,$$

where

$$P_0 = \Bigg[ \sum_{n=0}^{c-1} \frac{(\lambda/\mu)^n}{n!} +
\frac{(\lambda/\mu)^c}{c! (1-\rho)} \Bigg]^{-1}.$$

Expected memory consumption is `tasks * mem_per_task`. The
`scripts/scheduling_resource_benchmark.py` script iterates over worker counts
and reports utilization, queue length, expected memory, and observed throughput.
Each run dispatches brief sleep calls to mimic I/O-bound workloads so that
throughput scales with available workers.

Tests validate that higher worker counts increase throughput and that memory
scales linearly with the number of tasks, guiding tuning decisions.

## Distributed scheduling latency

When tasks incur a network delay \(d\) before execution, the expected
completion time per task with \(c\) workers each serving at rate \(\mu\) is

$$T = d + \frac{1}{c\mu}.$$

Running `scripts/distributed_orchestrator_sim.py` with 100 tasks and
\(d = 5\,\text{ms}\) yields:

| workers | avg latency (s) | throughput (tasks/s) |
| ------- | --------------- | -------------------- |
| 1       | 0.585           | 78.54                |
| 2       | 0.364           | 138.67               |
| 4       | 0.313           | 135.87               |

Latency falls as more workers handle requests while throughput plateaus
because coordination overhead offsets parallel gains.
