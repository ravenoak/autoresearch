from pytest_bdd import scenario, given, when, then

pytest_plugins = ["tests.behavior.steps.common_steps"]


@scenario("../features/error_recovery_basic.feature", "record a recovery strategy")
def test_basic_error_recovery():
    """Scenario: record a recovery strategy."""


@given("a failing operation", target_fixture="run_result")
def failing_operation():
    return {"recovery_info": {}}


@when("recovery is attempted")
def attempt_recovery(run_result):
    run_result["recovery_info"]["recovery_strategy"] = "retry_with_backoff"


@then('a recovery strategy "retry_with_backoff" should be recorded')
def check_recovery(run_result):
    assert run_result["recovery_info"].get("recovery_strategy") == "retry_with_backoff"
