# Distributed Overhead and Scalability

Network delay `d`, service time `s`, and failure probability `p` drive overhead.
Each task executes once on success and once more on failure. The expected number
of executions per task is

$$E[e] = \frac{1}{1-p}.$$

Average latency combines dispatch and service time with retry overhead:

$$T = (d + s) E[e] = \frac{d + s}{1 - p}.$$

With `w` workers the throughput upper bound becomes

$$\Theta \le \frac{w (1 - p)}{d + s}.$$

This complements the [distributed orchestrator performance](distributed_perf.md)
model by adding failure cost.
