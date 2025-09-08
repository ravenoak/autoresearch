# Scheduler benchmark

This benchmark models a simple queue where tasks arrive at rate \(\lambda\).
Each agent handles tasks at rate \(\mu\). We assume Poisson arrivals and
exponential service times so the system behaves like an M/M/c queue with
\(c\) identical agents.

## Assumptions
- Poisson task arrivals at \(\lambda = 5\) tasks per second.
- Each agent processes tasks at \(\mu = 2\) tasks per second.
- Agents share a single queue and work independently.

## Queueing formulas
Throughput is bounded by the lesser of arrival rate and total service
capacity:

\(T(c) = \min(\lambda, c\mu)\)

Average latency uses an M/M/c approximation where per-agent utilization must be
below 1:

\(L(c) = 1 / (\mu - \lambda / c)\)

## Results
Throughput scales linearly until capacity is reached:

```mermaid
plot
    title Estimated throughput
    x-axis workers
    y-axis tasks/sec
    line
        throughput : 1,2,4,8; 2,4,5,5
```

Latency diverges when arrivals near capacity. Saturated cases (one or two
workers) are omitted below:

```mermaid
plot
    title Estimated latency
    x-axis workers
    y-axis seconds
    line
        latency : 4,8; 1.33,0.73
```

## Follow-up
Latency diverges when arrival rate approaches capacity, suggesting further
benchmarking. See [benchmark-scheduler-queue-saturation][queue-issue] for a
detailed plan and [simulate-distributed-orchestrator-performance]
[orchestrator-issue] for broader orchestrator benchmarks.

[queue-issue]: ../issues/benchmark-scheduler-queue-saturation.md
[orchestrator-issue]: ../issues/archive/simulate-distributed-orchestrator-performance.md
