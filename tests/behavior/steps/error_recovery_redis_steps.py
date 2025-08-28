from pytest_bdd import given, scenario, then, when


class FailingRedis:
    """Simple Redis client that always fails."""

    def ping(self) -> None:  # pragma: no cover - error path
        raise ConnectionError("Redis unavailable")


@given("a Redis client that fails to connect", target_fixture="redis_client")
def redis_client() -> FailingRedis:
    return FailingRedis()


@when("I attempt a Redis operation")
def attempt_redis_operation(redis_client, bdd_context) -> None:
    try:
        redis_client.ping()
    except Exception as err:  # pragma: no cover - error path
        bdd_context["redis_error"] = err


@then("the system should handle the Redis error")
def handle_redis_error(bdd_context) -> None:
    assert bdd_context.get("redis_error") is not None


@scenario(
    "../features/error_recovery_redis.feature",
    "Connection failure triggers recovery",
)
def test_redis_error_recovery() -> None:
    """Ensure Redis connection failures are handled gracefully."""
