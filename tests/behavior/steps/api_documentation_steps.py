"""Step definitions for API documentation endpoint behavior tests."""

from __future__ import annotations

from typing import Any

from pytest_bdd import given, when, then, scenario, parsers

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel


@given("the API server is running")
def api_server_running(
    bdd_context: dict[str, Any],
    api_client,
    monkeypatch,
    temp_config,
    isolate_network,
    restore_environment,
) -> None:
    """Provide a configured API client."""

    cfg = ConfigModel(api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    bdd_context["client"] = api_client


@when("I request the docs endpoint")
def request_docs(bdd_context: dict[str, Any]) -> None:
    """Send a GET request to the Swagger UI endpoint."""

    client = bdd_context["client"]
    bdd_context["response"] = client.get("/docs")


@when("I request the openapi endpoint")
def request_openapi(bdd_context: dict[str, Any]) -> None:
    """Send a GET request to the OpenAPI schema endpoint."""

    client = bdd_context["client"]
    bdd_context["response"] = client.get("/openapi.json")


@then("the response status should be 200")
def check_status_ok(bdd_context: dict[str, Any]) -> None:
    """Assert that the HTTP status code is 200."""

    assert bdd_context["response"].status_code == 200


@then(parsers.parse('the response body should contain "{text}"'))
def check_body_contains(text: str, bdd_context: dict[str, Any]) -> None:
    """Verify that the response body contains the expected substring."""

    assert text in bdd_context["response"].text


@scenario(
    "../features/api_documentation.feature",
    "Access Swagger UI",
)
def test_access_swagger_ui() -> None:
    """Swagger UI is served successfully."""
    return


@scenario(
    "../features/api_documentation.feature",
    "Retrieve OpenAPI schema",
)
def test_retrieve_openapi_schema() -> None:
    """OpenAPI schema is accessible."""
    return
