from pytest_bdd import scenario, given, when, then
from autoresearch.config import ConfigModel, ConfigLoader


@given("the API server is running")
def api_server_running(test_context, api_client):
    test_context["client"] = api_client


@when("I send invalid JSON to the API")
def send_invalid_json(test_context):
    client = test_context["client"]
    resp = client.post(
        "/query",
        data="{invalid",
        headers={"Content-Type": "application/json"},
    )
    test_context["response"] = resp


@when("I request the metrics endpoint")
def request_metrics(test_context, monkeypatch):
    cfg = ConfigModel()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    client = test_context["client"]
    resp = client.get("/metrics")
    test_context["response"] = resp


@then("the response status should be 422")
def assert_status_422(test_context):
    assert test_context["response"].status_code == 422


@then("the response status should be 403")
def assert_status_403(test_context):
    assert test_context["response"].status_code == 403


@scenario("../features/api_edge_cases.feature", "Invalid JSON returns 422")
def test_invalid_json():
    pass


@scenario(
    "../features/api_edge_cases.feature",
    "Permission denied for metrics endpoint",
)
def test_permission_denied_metrics():
    pass
