# mypy: ignore-errors
from pytest_bdd import given, when, then, scenario

from autoresearch.config.models import ConfigModel, APIConfig
from autoresearch.config.loader import ConfigLoader
from tests.behavior.context import BehaviorContext


@given("the API server is running with config permissions")
def api_server_with_permissions(
    test_context: BehaviorContext, api_client, monkeypatch
) -> None:
    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"].append("config")
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    test_context["client"] = api_client


@when("I request the config endpoint")
def request_config(test_context: BehaviorContext) -> None:
    client = test_context["client"]
    test_context["response"] = client.get("/config")


@when("I update loops to 2 via the config endpoint")
def update_config(test_context: BehaviorContext) -> None:
    client = test_context["client"]
    test_context["response"] = client.put("/config", json={"loops": 2})


@when("I replace the configuration via the config endpoint")
def replace_config(test_context: BehaviorContext) -> None:
    client = test_context["client"]
    current = client.get("/config").json()
    test_context["response"] = client.post("/config", json=current)


@when("I reload the configuration")
def reload_config(test_context: BehaviorContext) -> None:
    client = test_context["client"]
    test_context["response"] = client.delete("/config")


@then("the response status should be 200")
def response_ok(test_context: BehaviorContext) -> None:
    resp = test_context["response"]
    assert resp.status_code == 200
    assert "error" not in resp.json()


@then('the response body should contain "reasoning_mode"')
def body_has_reasoning_mode(test_context: BehaviorContext) -> None:
    data = test_context["response"].json()
    assert "reasoning_mode" in data


@then("the response body should show loops 2")
def body_shows_loops(test_context: BehaviorContext) -> None:
    data = test_context["response"].json()
    assert data.get("loops") == 2


@scenario("../features/api_config.feature", "Retrieve current configuration")
def test_get_config() -> None:
    pass


@scenario("../features/api_config.feature", "Update loops via the config endpoint")
def test_update_config() -> None:
    pass


@scenario(
    "../features/api_config.feature", "Replace configuration via the config endpoint"
)
def test_replace_config() -> None:
    pass


@scenario("../features/api_config.feature", "Reload configuration")
def test_reload_config() -> None:
    pass
