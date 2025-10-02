from typing import TypedDict

from pytest_bdd import given, scenario, then, when

pytest_plugins = ["tests.behavior.steps.common_steps"]


class RecoveryInfo(TypedDict, total=False):
    """Details captured about recovery attempts."""

    recovery_strategy: str


class RunResult(TypedDict):
    """Mutable mapping used to share recovery results between steps."""

    recovery_info: RecoveryInfo


@scenario("../features/error_recovery_basic.feature", "record a recovery strategy")
def test_basic_error_recovery() -> None:
    """Scenario: record a recovery strategy."""


@given("a failing operation", target_fixture="run_result")
def failing_operation() -> RunResult:
    return {"recovery_info": {}}


@when("recovery is attempted")
def attempt_recovery(run_result: RunResult) -> None:
    run_result["recovery_info"]["recovery_strategy"] = "retry_with_backoff"


@then('a recovery strategy "retry_with_backoff" should be recorded')
def check_recovery(run_result: RunResult) -> None:
    assert run_result["recovery_info"].get("recovery_strategy") == "retry_with_backoff"
