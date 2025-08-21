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

## References
1. G. Irving et al. "AI Safety via Debate." https://arxiv.org/abs/1805.00899
2. Y. Du et al. "Improving Factuality with Multi-Agent Debate."
   https://arxiv.org/abs/2402.06720
