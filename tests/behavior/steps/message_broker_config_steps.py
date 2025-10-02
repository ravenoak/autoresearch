"""Step definitions for message broker configuration scenarios."""
from tests.behavior.context import BehaviorContext

import pytest
from pytest_bdd import given, scenario, then, when
from autoresearch.distributed import (
    InMemoryBroker,
    RedisBroker,
    get_message_broker,
)


@given('the message broker name "{name}"')
def given_broker_name(bdd_context: BehaviorContext, name: str) -> None:
    """Store the broker name for later retrieval."""
    bdd_context["broker_name"] = name


@when("I obtain a message broker instance")
def obtain_broker_instance(bdd_context: BehaviorContext) -> None:
    """Instantiate the configured message broker."""
    name = bdd_context["broker_name"]
    try:
        broker = get_message_broker(name)
        bdd_context["broker"] = broker
        bdd_context["broker_error"] = None
    except Exception as err:  # pragma: no cover - error path
        bdd_context["broker"] = None
        bdd_context["broker_error"] = err


@then("an in-memory broker should be returned")
def assert_in_memory_broker(bdd_context: BehaviorContext) -> None:
    """Verify the resolved broker is the in-memory implementation."""
    assert isinstance(bdd_context["broker"], InMemoryBroker)


@then("a message broker error should be raised")
def assert_broker_error(bdd_context: BehaviorContext) -> None:
    """Ensure an error was captured during broker resolution."""
    assert bdd_context["broker"] is None
    err = bdd_context.get("broker_error")
    assert err is not None
    assert "Unsupported message broker" in str(err)


@then("a redis broker should be returned")
def assert_redis_broker(bdd_context: BehaviorContext) -> None:
    """Verify the resolved broker is the Redis implementation."""
    assert isinstance(bdd_context["broker"], RedisBroker)


@scenario("../features/message_broker_config.feature", "Use default in-memory message broker")
def test_use_default_inmemory_message_broker() -> None:
    """Scenario: selecting the in-memory broker."""
    pass


@scenario("../features/message_broker_config.feature", "Unsupported message broker raises error")
def test_unsupported_message_broker_raises_error() -> None:
    """Scenario: unknown broker names raise an error."""
    pass


@pytest.mark.requires_distributed
@pytest.mark.redis
@scenario("../features/message_broker_config.feature", "Redis broker detection")
def test_redis_broker_detection() -> None:
    """Scenario: detect Redis broker configuration."""
    pass
