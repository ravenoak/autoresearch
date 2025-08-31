# API Rate Limiting

Token bucket limits API requests per client. See [algorithm][alg] for proof and
convergence details.

[alg]: ../algorithms/api_rate_limiting.md

## Acceptance Criteria

- Each client makes no more than its configured number of requests per second.
- Buckets refill at the sustained rate and never exceed capacity.
- Excess requests receive **429 Too Many Requests**.

## Traceability

- Modules
  - [src/autoresearch/api/middleware.py][m1]
- Tests
  - [tests/unit/test_property_api_rate_limit_bounds.py][t1]

[m1]: ../../src/autoresearch/api/middleware.py
[t1]: ../../tests/unit/test_property_api_rate_limit_bounds.py
