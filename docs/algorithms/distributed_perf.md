# Distributed orchestrator performance

This spec models a distributed orchestrator as an M/M/c queue with an added
network delay `d` before each task reaches a worker.

## Assumptions

- Tasks arrive every `d` seconds, so the arrival rate is `\lambda = 1/d`.
- Each of `c` workers processes a task in `s` seconds (`\mu = 1/s`).
- Arrivals and service times are exponentially distributed.
- The system is stable only if the utilization `\rho = \lambda / (c\mu)` is
  less than one.

## Equations

The probability of zero tasks in the system is

$$P_0 = \Bigg[ \sum_{n=0}^{c-1} \frac{(\lambda/\mu)^n}{n!} +
\frac{(\lambda/\mu)^c}{c! (1-\rho)} \Bigg]^{-1}.$$ 

The average queue length is

$$L_q = \frac{(\lambda/\mu)^c \rho}{c! (1-\rho)^2} P_0.$$ 

The average waiting time is `W_q = L_q / \lambda`, yielding an average latency

$$T = d + W_q + \frac{1}{\mu}.$$ 

Throughput equals the arrival rate `\lambda` when `\rho < 1`. See
[orchestrator performance](../orchestrator_perf.md) for background.
