# Dialectical Agent Coordination

The dialectical cycle rotates a Synthesizer \(S\), Contrarian \(C\), and
FactChecker \(F\). Each agent proposes a scalar belief \(b\). After each
loop, synthesis updates with

\(b_s^{t+1} = (b_s^t + b_c^t + b_f^t)/3\).

The Contrarian perturbs the belief with noise \(\varepsilon_t\), and the
FactChecker pulls toward the ground truth \(g\):

\(b_c^{t+1} = b_s^t - \varepsilon_t\),
\(b_f^{t+1} = b_s^t + \alpha (g - b_s^t)\).

The mean update forms a linear system whose spectral radius is
\((1 - \alpha)/3\). Choosing \(0 < \alpha \leq 1\) ensures geometric
convergence to \(g\). The `scripts/dialectical_coordination_demo.py`
script runs many trials and reports the mean and deviation of final
syntheses, showing robustness to noise.

In matrix form, letting \(x^t = [b_s^t, b_c^t, b_f^t]^T\) and ignoring
noise, the policy is

\[
x^{t+1} = A x^t + u, \quad
A = \begin{bmatrix}
  \tfrac{1}{3} & \tfrac{1}{3} & \tfrac{1}{3} \\
  1 & 0 & 0 \\
  1 - \alpha & 0 & \alpha
\end{bmatrix},
u = \begin{bmatrix} 0 \\ 0 \\ \alpha g \end{bmatrix}.
\]

The eigenvalues of \(A\) have largest magnitude \((1 - \alpha)/3 < 1\),
so repeated application converges to \([g, g, g]^T\) in expectation.

Assumptions
- Agents share scalar beliefs and update synchronously.
- Noise \(\varepsilon_t\) has zero mean and bounded variance.

Alternatives
- Debate models that optimize policies with reinforcement learning [1].
- Majority voting without adversarial contrast [2].

Conclusions
- Dialectical coordination converges quickly when \(\alpha\) controls
  fact-checker influence; variability stays low across trials, yielding
  stable answers.

## Distributed coordination

The simulation [distributed_coordination_analysis.py][dca]
spawns 1, 2, and 4 workers under `ResourceMonitor`. Metrics in
[distributed_metrics.json][dmj] show:

- 1 node: CPU 0.0% memory 136.4 MB
- 2 nodes: CPU 29.0% memory 140.4 MB
- 4 nodes: CPU 39.1% memory 140.5 MB

These observations highlight the overhead as node count increases.

## References
1. G. Irving et al. "AI Safety via Debate." https://arxiv.org/abs/1805.00899
2. Y. Du et al. "Improving Factuality with Multi-Agent Debate."
   https://arxiv.org/abs/2402.06720

[dca]: ../../tests/analysis/distributed_coordination_analysis.py
[dmj]: ../../tests/analysis/distributed_metrics.json
