from pytest_bdd import given, when, then
from autoresearch.distributed import get_message_broker, InMemoryBroker


@given('the message broker name "{name}"')
def given_broker_name(bdd_context, name: str) -> None:
    bdd_context["broker_name"] = name


@when("I obtain a message broker instance")
def obtain_broker_instance(bdd_context) -> None:
    name = bdd_context["broker_name"]
    try:
        broker = get_message_broker(name)
        bdd_context["broker"] = broker
        bdd_context["broker_error"] = None
    except Exception as e:  # pragma: no cover - error path
        bdd_context["broker"] = None
        bdd_context["broker_error"] = e


@then("an in-memory broker should be returned")
def assert_in_memory_broker(bdd_context) -> None:
    assert isinstance(bdd_context["broker"], InMemoryBroker)


@then("a message broker error should be raised")
def assert_broker_error(bdd_context) -> None:
    assert bdd_context["broker"] is None
    err = bdd_context.get("broker_error")
    assert err is not None
    assert "Unsupported message broker" in str(err)
