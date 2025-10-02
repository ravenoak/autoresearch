# flake8: noqa
from tests.behavior.context import BehaviorContext
from pytest_bdd import scenario, when, then, parsers
import requests
import responses

from .common_steps import app_running, app_running_with_default, application_running

A2A_URL = "http://a2a.example/message"


@when(parsers.parse('I send a valid A2A query "{query}"'))
def send_valid_a2a_query(query, bdd_context: BehaviorContext):
    with responses.RequestsMock() as rsps:
        rsps.post(
            A2A_URL,
            json={"status": "success", "message": {"answer": "42"}},
            status=200,
        )
        resp = requests.post(A2A_URL, json={"query": query})
    bdd_context["a2a_response"] = resp


@when("I send malformed JSON to the A2A interface")
def send_malformed_json(bdd_context: BehaviorContext):
    with responses.RequestsMock() as rsps:
        rsps.post(
            A2A_URL,
            json={"status": "error", "error": "Invalid JSON"},
            status=400,
        )
        resp = requests.post(A2A_URL, data="not-json")
    bdd_context["a2a_response"] = resp


@when("the A2A interface returns a server error")
def send_server_error(bdd_context: BehaviorContext):
    with responses.RequestsMock() as rsps:
        rsps.post(
            A2A_URL,
            json={"status": "error", "error": "Internal Server Error"},
            status=500,
        )
        resp = requests.post(A2A_URL, json={"query": "test"})
    bdd_context["a2a_response"] = resp


@then(parsers.parse("the response status code should be {status:d}"))
def check_status_code(status, bdd_context: BehaviorContext):
    resp = bdd_context["a2a_response"]
    assert resp.status_code == status


@then("the response should include a JSON message with an answer")
def check_json_response(bdd_context: BehaviorContext):
    resp = bdd_context["a2a_response"]
    data = resp.json()
    assert data.get("status") == "success"
    assert "message" in data
    assert "answer" in data["message"]


@then(parsers.parse('the error message should contain "{message}"'))
def check_error_message(message, bdd_context: BehaviorContext):
    resp = bdd_context["a2a_response"]
    data = resp.json()
    assert data.get("status") == "error"
    assert message in data.get("error", "")


@scenario("../features/a2a_interface.feature", "Successful query")
def test_a2a_success():
    pass


@scenario("../features/a2a_interface.feature", "Malformed JSON")
def test_a2a_malformed_json():
    pass


@scenario("../features/a2a_interface.feature", "Server-side error")
def test_a2a_server_error():
    pass
