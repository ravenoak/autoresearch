"""Step definitions for API authentication and rate limiting."""

from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.api import config_loader, get_request_logger
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator

from . import api_orchestrator_integration_steps  # noqa: F401


@given("the API server is running")
def api_server_running():
    """Placeholder step to signify the API is available."""
    pass


@given(parsers.parse('the API requires an API key "{key}"'))
def require_api_key(monkeypatch, key):
    cfg = ConfigModel(api=APIConfig(api_key=key))
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setenv("AUTORESEARCH_API_KEY", key)
    config_loader._config = None
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )


@given(parsers.parse('the API requires a bearer token "{token}"'))
def require_bearer_token(monkeypatch, token):
    cfg = ConfigModel(api=APIConfig(bearer_token=token))
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setenv("AUTORESEARCH_BEARER_TOKEN", token)
    config_loader._config = None
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )


@given(parsers.parse("the API rate limit is {limit:d} request per minute"))
def set_rate_limit(monkeypatch, limit):
    cfg = ConfigModel(api=APIConfig(rate_limit=limit))
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    config_loader._config = None
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )
    get_request_logger().reset()


@given(parsers.parse('the API requires an API key "{key}" with role "{role}" and no permissions'))
def require_api_key_no_permissions(monkeypatch, key, role):
    cfg = ConfigModel(api=APIConfig(api_keys={key: role}, role_permissions={role: []}))
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setenv("AUTORESEARCH_API_KEY", key)
    config_loader._config = None
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )


@when(parsers.parse('I send a query "{query}" with header "{header}" set to "{value}"'))
def send_query_with_header(api_client_factory, test_context, query, header, value):
    client = api_client_factory({header: value})
    resp = client.post("/query", json={"query": query})
    test_context["response"] = resp


@when(parsers.parse('I send a query "{query}" without credentials'))
def send_query_without_credentials(api_client_factory, test_context, query):
    client = api_client_factory()
    resp = client.post("/query", json={"query": query})
    test_context["response"] = resp


@when("I send two queries to the API")
def send_two_queries(api_client_factory, test_context):
    client = api_client_factory()
    test_context["resp1"] = client.post("/query", json={"query": "q"})
    test_context["resp2"] = client.post("/query", json={"query": "q"})


@then(parsers.parse("the response status should be {status:d}"))
def check_status(test_context, status):
    resp = test_context["response"]
    assert resp.status_code == status
    data = resp.json()
    if status == 200:
        assert "error" not in data
    else:
        assert "detail" in data


@then(parsers.parse("the first response status should be {status:d}"))
def check_first_status(test_context, status):
    resp = test_context["resp1"]
    assert resp.status_code == status
    data = resp.json()
    assert "answer" in data
    assert "error" not in data


@then(parsers.parse("the second response status should be {status:d}"))
def check_second_status(test_context, status):
    resp = test_context["resp2"]
    assert resp.status_code == status
    if status == 429:
        assert resp.text == "rate limit exceeded"
    else:
        data = resp.json()
        assert "error" not in data


@scenario("../features/api_auth.feature", "Invalid API key")
def test_invalid_api_key():
    pass


@scenario("../features/api_auth.feature", "Invalid bearer token")
def test_invalid_bearer_token():
    pass


@scenario("../features/api_auth.feature", "Rate limit exceeded")
def test_rate_limit_exceeded():
    pass


@scenario("../features/api_auth.feature", "Missing credentials")
def test_missing_credentials():
    pass


@scenario("../features/api_auth.feature", "Insufficient permission")
def test_insufficient_permission():
    pass
