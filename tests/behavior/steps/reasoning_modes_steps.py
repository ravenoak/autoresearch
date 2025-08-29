from pytest_bdd import scenarios, when, then, parsers

from autoresearch.orchestration import ReasoningMode

pytest_plugins = ["tests.behavior.steps.common_steps"]

scenarios("../features/reasoning_modes.feature")


@when(parsers.parse('a reasoning mode "{mode}" is chosen'))
def choose_mode(bdd_context, mode):
    bdd_context["mode"] = ReasoningMode(mode)


@then(parsers.parse('bdd_context records mode "{mode}"'))
def record_mode(bdd_context, mode):
    assert bdd_context.get("mode") == ReasoningMode(mode)
