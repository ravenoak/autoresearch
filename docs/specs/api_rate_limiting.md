# API Rate Limiting

## Overview

Token bucket limits API requests per client. See [algorithm][alg] for proof and
convergence details.

## Algorithms

The bucket stores ``b(t)`` tokens with capacity ``C`` and refill rate ``R``.
After ``\Delta t`` seconds without requests the state evolves as

\[
b(t + \Delta t) = \min(C, b(t) + R \Delta t).
\]

Each request consumes one token; if ``b(t) = 0`` the request is denied.

## Invariants

- Token count stays within ``0 \le b(t) \le C``.
- Each request decrements the bucket by one.
- Refills never raise the bucket above ``C``.
- Requests with zero tokens are rejected.

## Proof Sketch

Assume the invariants hold at time ``t``. The refill equation keeps
``b(t)`` within bounds, and a request subtracts one token, preserving the
range. By induction no request sequence drives the count outside
``[0, C]``, so a client never exceeds its configured limit.

## Simulation

The snippet below refills an empty bucket until it reaches capacity.

```python
C, R = 5, 1
b = 0
for step in range(6):
    b = min(C, b + R)
    print(step, b)
# 0 1
# 1 2
# 2 3
# 3 4
# 4 5
# 5 5
```

Tokens rise linearly and stop at ``C``, demonstrating convergence.

## Simulation Expectations

The simulation must show the bucket refilling linearly until it reaches
capacity ``C``. Once full, further iterations should leave the level
unchanged, proving convergence under the configured rate ``R``.

[alg]: ../algorithms/api_rate_limiting.md
