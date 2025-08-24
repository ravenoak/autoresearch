"""Steps for critic agent behavior tests."""

from pytest_bdd import given, when, then, scenarios

from autoresearch.agents.specialized.critic import CriticAgent
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState


scenarios("../features/critic_agent.feature")


@given("a query with findings")
def given_query_with_findings(test_context):
    test_context["state"] = QueryState(
        query="q",
        claims=[{"id": "1", "type": "research_findings", "content": "data"}],
    )
    test_context["config"] = ConfigModel()


@when("the critic agent evaluates the query")
def when_critic_executes(test_context, monkeypatch):
    agent = CriticAgent()

    class DummyAdapter:
        def generate(self, prompt, model=None):
            return "critique text"

    monkeypatch.setattr(
        CriticAgent, "get_adapter", lambda self, cfg: DummyAdapter()
    )
    monkeypatch.setattr(
        CriticAgent, "generate_prompt", lambda self, name, **kw: "prompt"
    )
    test_context["result"] = agent.execute(
        test_context["state"], test_context["config"]
    )


@then("a critique is produced")
def then_critique_produced(test_context):
    assert test_context["result"]["results"]["critique"] == "critique text"
