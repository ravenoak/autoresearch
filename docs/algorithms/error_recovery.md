# Error Recovery via Exponential Backoff

The `retry_with_backoff` helper in
[`error_recovery`](../../src/autoresearch/error_recovery.py)
retries failing actions with exponentially increasing delays. If each
attempt succeeds with probability `p > 0`, the number of attempts before
success follows a geometric distribution with mean `1/p`.

## Proof

Let `X` be the number of attempts. For independent trials,
`P(X = k) = (1 - p)^{k-1} p`. The expectation is

```
E[X] = \sum_{k=1}^{\infty} k (1 - p)^{k-1} p = 1/p.
```

Since `P(X < \infty) = 1`, retries eventually succeed with probability one.

## Simulation

Run `uv run scripts/simulate_error_recovery.py --p 0.3 --trials 1000`
to approximate `E[X]`. Results converge to `1/p` as trials increase.

Reference:
[Geometric distribution](https://en.wikipedia.org/wiki/Geometric_distribution).
