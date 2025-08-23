# Add redis dependency for integration tests

## Context
Integration tests error during collection because the `redis` package is missing.
The current development extras exclude redis, so `tests/integration/test_distributed_redis_broker.py`
cannot run.

## Acceptance Criteria
- `redis` dependency installed or provided via optional extra.
- `tests/integration/test_distributed_redis_broker.py` runs or is skipped when redis is unavailable.
- Documentation notes redis requirement for distributed broker tests.

## Status
Open
