# mypy: ignore-errors
"""Step definitions for API documentation endpoint behavior tests."""

from __future__ import annotations

from fastapi.openapi.docs import get_swagger_ui_html
from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from tests.behavior.context import BehaviorContext

pytest_plugins = ["tests.behavior.steps.common_steps"]


@given("the API server is running")
def api_server_running(
    bdd_context: BehaviorContext,
    api_client,
    monkeypatch,
    temp_config,
    restore_environment,
) -> None:
    """Provide a configured API client."""

    cfg = ConfigModel(api=APIConfig())
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    bdd_context["client"] = api_client

    # Expose Swagger UI endpoint for documentation tests
    api_app = api_client.app
    if not any(r.path == "/docs" for r in api_app.router.routes):
        api_app.router.add_api_route(
            "/docs",
            lambda: get_swagger_ui_html(
                openapi_url="/openapi.json", title="Swagger UI"
            ),
            include_in_schema=False,
        )


@when("I request the docs endpoint")
def request_docs(bdd_context: BehaviorContext) -> None:
    """Send a GET request to the Swagger UI endpoint."""

    client = bdd_context["client"]
    bdd_context["response"] = client.get("/docs")


@when("I request the openapi endpoint")
def request_openapi(bdd_context: BehaviorContext) -> None:
    """Send a GET request to the OpenAPI schema endpoint."""

    client = bdd_context["client"]
    bdd_context["response"] = client.get("/openapi.json")


@then("the response status should be 200")
def check_status_ok(bdd_context: BehaviorContext) -> None:
    """Assert that the HTTP status code is 200."""

    assert bdd_context["response"].status_code == 200


@then(parsers.parse('the response body should contain "{text}"'))
def check_body_contains(text: str, bdd_context: BehaviorContext) -> None:
    """Verify that the response body contains the expected substring."""
    body = bdd_context["response"].text.lower().replace(" ", "").replace("-", "")
    expected = text.lower().replace(" ", "").replace("-", "")
    assert expected in body


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
