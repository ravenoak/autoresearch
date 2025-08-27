# Error Recovery

Utilities for retrying operations with exponential backoff. The backoff
doubles the delay after each failure using `base_delay * 2^(attempt - 1)` and
stops after a successful call or when retries are exhausted, at which point a
`RuntimeError` is raised.

The expected number of attempts for success with probability `p` is `1/p`, as
shown in the [error recovery algorithm note][alg].

## Traceability

- Modules
  - [src/autoresearch/error_recovery.py][m1]
- Tests
  - [tests/unit/test_error_recovery.py][t1]

[m1]: ../../src/autoresearch/error_recovery.py
[t1]: ../../tests/unit/test_error_recovery.py
[alg]: ../algorithms/error_recovery.md
