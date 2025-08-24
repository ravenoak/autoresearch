# Add redis dependency for integration tests

## Context
Integration tests error during collection because the `redis` package is missing.
The current development extras exclude redis, so
`tests/integration/test_distributed_redis_broker.py` cannot run. After installing
`redis`, `tests/unit/test_distributed_redis.py::test_get_message_broker_redis_missing`
fails because it no longer raises `ModuleNotFoundError`.

## Acceptance Criteria
- `redis` dependency installed or provided via optional extra.
- `tests/integration/test_distributed_redis_broker.py` runs or is skipped when
  redis is unavailable.
- `tests/unit/test_distributed_redis.py` adapts to redis being installed and
  still validates missing-dependency behavior when appropriate.
- Documentation notes redis requirement for distributed broker tests.

## Status
Archived
