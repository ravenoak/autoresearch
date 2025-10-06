# mypy: ignore-errors
from pytest_bdd import scenario, given, when, then

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, APIConfig
from tests.behavior.context import BehaviorContext


@given("the API server is running")
def api_server_running(
    test_context: BehaviorContext, api_client, monkeypatch
) -> None:
    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"].append("health")
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    test_context["client"] = api_client


@when("I request the health endpoint")
def request_health(test_context: BehaviorContext) -> None:
    client = test_context["client"]
    resp = client.get("/health")
    test_context["response"] = resp


@then('the response body should contain "status" "ok"')
def check_health_body(test_context: BehaviorContext) -> None:
    resp = test_context["response"]
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert "error" not in resp.json()


@then("the response status should be 200")
def assert_status_200(test_context: BehaviorContext) -> None:
    resp = test_context["response"]
    assert resp.status_code == 200
    assert "error" not in resp.json()


@when("I request the capabilities endpoint")
def request_capabilities(test_context: BehaviorContext, monkeypatch) -> None:
    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"].append("capabilities")
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    resp = test_context["client"].get("/capabilities")
    test_context["response"] = resp


@then("the response should include supported reasoning modes")
def check_capabilities(test_context: BehaviorContext) -> None:
    resp = test_context["response"]
    assert resp.status_code == 200
    data = resp.json()
    assert "reasoning_modes" in data
    for mode in ["direct", "dialectical", "chain-of-thought"]:
        assert mode in data["reasoning_modes"]
    assert "error" not in data


@scenario("../features/api_misc.feature", "Health endpoint returns status")
def test_health_endpoint() -> None:
    pass


@scenario("../features/api_misc.feature", "Capabilities endpoint lists reasoning modes")
def test_capabilities_endpoint() -> None:
    pass
