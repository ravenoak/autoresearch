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

## Traceability


- Modules
  - [src/autoresearch/api/middleware.py][m1]
- Tests
  - [tests/analysis/test_api_stream_order_sim.py][t15]
  - [tests/analysis/test_api_streaming_sim.py][t16]
  - [tests/integration/test_api.py][t17]
  - [tests/integration/test_api_additional.py][t18]
  - [tests/integration/test_api_auth.py][t19]
  - [tests/integration/test_api_auth_middleware.py][t20]
  - [tests/integration/test_api_auth_permissions.py][t21]
  - [tests/integration/test_api_docs.py][t22]
  - [tests/integration/test_api_hot_reload.py][t23]
  - [tests/integration/test_api_streaming.py][t24]
  - [tests/integration/test_api_streaming_webhook.py][t25]
  - [tests/integration/test_api_versioning.py][t26]
  - [tests/unit/legacy/test_api.py][t27]
  - [tests/unit/legacy/test_api_auth_deps.py][t28]
  - [tests/unit/legacy/test_api_auth_middleware.py][t29]
  - [tests/unit/legacy/test_api_error_handling.py][t30]
  - [tests/unit/legacy/test_api_imports.py][t31]
  - [tests/unit/legacy/test_property_api_rate_limit_bounds.py][t33]
  - [tests/unit/legacy/test_webhooks_logging.py][t32]

[m1]: ../../src/autoresearch/api/middleware.py

[alg]: ../algorithms/api_rate_limiting.md

[t15]: ../../tests/analysis/test_api_stream_order_sim.py
[t16]: ../../tests/analysis/test_api_streaming_sim.py
[t17]: ../../tests/integration/test_api.py
[t18]: ../../tests/integration/test_api_additional.py
[t19]: ../../tests/integration/test_api_auth.py
[t20]: ../../tests/integration/test_api_auth_middleware.py
[t21]: ../../tests/integration/test_api_auth_permissions.py
[t22]: ../../tests/integration/test_api_docs.py
[t23]: ../../tests/integration/test_api_hot_reload.py
[t24]: ../../tests/integration/test_api_streaming.py
[t25]: ../../tests/integration/test_api_streaming_webhook.py
[t26]: ../../tests/integration/test_api_versioning.py
[t27]: ../../tests/unit/legacy/test_api.py
[t28]: ../../tests/unit/legacy/test_api_auth_deps.py
[t29]: ../../tests/unit/legacy/test_api_auth_middleware.py
[t30]: ../../tests/unit/legacy/test_api_error_handling.py
[t31]: ../../tests/unit/legacy/test_api_imports.py
[t33]: ../../tests/unit/legacy/test_property_api_rate_limit_bounds.py
[t32]: ../../tests/unit/legacy/test_webhooks_logging.py
