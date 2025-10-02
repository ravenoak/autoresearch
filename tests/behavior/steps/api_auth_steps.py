"""Step definitions for API authentication and rate limiting."""

from __future__ import annotations
from tests.behavior.context import BehaviorContext
from tests.behavior.utils import empty_metrics

import importlib

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from pytest_bdd import parsers

from autoresearch.api import (
    config_loader,
    get_request_logger,
)
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import (
    APIConfig,
    ConfigModel,
)
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import (
    Orchestrator,
)

from tests.typing_helpers import given, scenario, then, when

if not TYPE_CHECKING:
    importlib.import_module(
        "tests.behavior.steps.api_orchestrator_integration_steps"
    )


class HttpResponse(Protocol):
    """Protocol describing HTTP responses used in behavior tests."""

    status_code: int
    text: str
    headers: Mapping[str, str]

    def json(self) -> dict[str, object]: ...


class ApiClient(Protocol):
    """Protocol for FastAPI test clients used in behavior scenarios."""

    def post(self, url: str, *, json: dict[str, object]) -> HttpResponse: ...


ApiClientFactory = Callable[[dict[str, str] | None], ApiClient]


def _stub_config_loader(
    monkeypatch: pytest.MonkeyPatch, cfg: ConfigModel
) -> None:
    """Replace ``ConfigLoader.load_config`` with a deterministic stub."""

    def _load_config_stub(_self: ConfigLoader) -> ConfigModel:
        return cfg

    monkeypatch.setattr(ConfigLoader, "load_config", _load_config_stub)
    config_loader._config = None


def _install_orchestrator_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure orchestrator queries return a predictable response."""

    def _run_query_stub(*_args: object, **_kwargs: object) -> QueryResponse:
        return QueryResponse(
            answer="ok",
            citations=[],
            reasoning=[],
            metrics=empty_metrics(),
        )

    monkeypatch.setattr(Orchestrator, "run_query", _run_query_stub)


def _get_response(test_context: BehaviorContext, key: str) -> HttpResponse:
    """Retrieve and type-cast a stored HTTP response from the context."""

    return cast(HttpResponse, test_context[key])


@given("the API server is running")
def api_server_running() -> None:
    """Placeholder step to signify the API is available."""


@given(parsers.parse('the API requires an API key "{key}"'))
def require_api_key(monkeypatch: pytest.MonkeyPatch, key: str) -> None:
    cfg = ConfigModel(api=APIConfig(api_key=key))
    _stub_config_loader(monkeypatch, cfg)
    monkeypatch.setenv("AUTORESEARCH_API_KEY", key)
    _install_orchestrator_stub(monkeypatch)


@given(parsers.parse('the API requires a bearer token "{token}"'))
def require_bearer_token(monkeypatch: pytest.MonkeyPatch, token: str) -> None:
    cfg = ConfigModel(api=APIConfig(bearer_token=token))
    _stub_config_loader(monkeypatch, cfg)
    monkeypatch.setenv("AUTORESEARCH_BEARER_TOKEN", token)
    _install_orchestrator_stub(monkeypatch)


@given(parsers.parse("the API rate limit is {limit:d} request per minute"))
def set_rate_limit(monkeypatch: pytest.MonkeyPatch, limit: int) -> None:
    cfg = ConfigModel(api=APIConfig(rate_limit=limit))
    ConfigLoader.reset_instance()
    _stub_config_loader(monkeypatch, cfg)
    _install_orchestrator_stub(monkeypatch)
    get_request_logger().reset()


@given(
    parsers.parse(
        'the API requires an API key "{key}" with role "{role}" '
        'and no permissions'
    )
)
def require_api_key_no_permissions(
    monkeypatch: pytest.MonkeyPatch, key: str, role: str
) -> None:
    cfg = ConfigModel(
        api=APIConfig(api_keys={key: role}, role_permissions={role: []})
    )
    _stub_config_loader(monkeypatch, cfg)
    monkeypatch.setenv("AUTORESEARCH_API_KEY", key)
    _install_orchestrator_stub(monkeypatch)


@when(
    parsers.parse(
        'I send a query "{query}" with header "{header}" set to '
        '"{value}"'
    )
)
def send_query_with_header(
    api_client_factory: ApiClientFactory,
    test_context: BehaviorContext,
    query: str,
    header: str,
    value: str,
) -> None:
    client = api_client_factory({header: value})
    response = client.post("/query", json={"query": query})
    test_context["response"] = response


@when(parsers.parse('I send a query "{query}" without credentials'))
def send_query_without_credentials(
    api_client_factory: ApiClientFactory,
    test_context: BehaviorContext,
    query: str,
) -> None:
    client = api_client_factory(None)
    response = client.post("/query", json={"query": query})
    test_context["response"] = response


@when("I send two queries to the API")
def send_two_queries(
    api_client_factory: ApiClientFactory, test_context: BehaviorContext
) -> None:
    client = api_client_factory(None)
    test_context["resp1"] = client.post("/query", json={"query": "q"})
    test_context["resp2"] = client.post("/query", json={"query": "q"})


@then(parsers.parse("the response status should be {status:d}"))
def check_status(test_context: BehaviorContext, status: int) -> None:
    response = _get_response(test_context, "response")
    assert response.status_code == status
    data = response.json()
    if status == 200:
        assert "error" not in data
    else:
        assert "detail" in data


@then(
    parsers.parse('the response should include header "{header}" with value "{value}"')
)
def check_response_header(
    test_context: BehaviorContext, header: str, value: str
) -> None:
    response = _get_response(test_context, "response")
    assert header in response.headers
    assert response.headers[header] == value


@then(parsers.parse("the first response status should be {status:d}"))
def check_first_status(test_context: BehaviorContext, status: int) -> None:
    response = _get_response(test_context, "resp1")
    assert response.status_code == status
    data = response.json()
    assert "answer" in data
    assert "error" not in data


@then(parsers.parse("the second response status should be {status:d}"))
def check_second_status(test_context: BehaviorContext, status: int) -> None:
    response = _get_response(test_context, "resp2")
    assert response.status_code == status
    if status == 429:
        assert response.text == "rate limit exceeded"
    else:
        data = response.json()
        assert "error" not in data


@then(parsers.parse("the request logger should record {count:d} hits"))
def check_request_logger_hits(count: int) -> None:
    snapshot = get_request_logger().snapshot()
    total_hits = sum(snapshot.values())
    assert total_hits == count


@scenario("../features/api_auth.feature", "Invalid API key")
def test_invalid_api_key() -> None:
    """Scenario validating API key authentication failures."""


@scenario("../features/api_auth.feature", "Invalid bearer token")
def test_invalid_bearer_token() -> None:
    """Scenario validating bearer token authentication failures."""


@scenario("../features/api_auth.feature", "Rate limit exceeded")
def test_rate_limit_exceeded() -> None:
    """Scenario validating rate limit enforcement."""


@scenario("../features/api_auth.feature", "Missing credentials")
def test_missing_credentials() -> None:
    """Scenario validating missing credential handling."""


@scenario("../features/api_auth.feature", "Insufficient permission")
def test_insufficient_permission() -> None:
    """Scenario validating permission checks for API keys."""
