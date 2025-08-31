import pytest
from pytest_bdd import given, scenarios, then, parsers

pytest_plugins = ["tests.behavior.steps.common_steps"]

scenarios("../features/optional_extras.feature")


@given(parsers.parse('the optional module "{module}" can be imported'))
def optional_module(module):
    return pytest.importorskip(module)


@then(parsers.parse('the module exposes attribute "{attr}"'))
def module_has_attribute(optional_module, attr):
    assert hasattr(optional_module, attr)
