from pytest_bdd import when, then, scenarios, parsers

from autoresearch.orchestration import ReasoningMode

pytest_plugins = ["tests.behavior.steps.common_steps"]

scenarios("../features/reasoning_modes_all.feature")


@when(parsers.parse('I request reasoning mode "{mode}"'))
def request_mode(mode, bdd_context):
    bdd_context["mode"] = ReasoningMode(mode)


@then(parsers.parse('bdd_context should record the reasoning mode "{mode}"'))
def assert_mode(mode, bdd_context):
    assert bdd_context.get("mode") == ReasoningMode(mode)
