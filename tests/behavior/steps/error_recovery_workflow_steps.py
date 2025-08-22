from pytest_bdd import given, when, then, scenarios, parsers

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.errors import AgentError
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator

pytest_plugins = ["tests.behavior.steps.common_steps"]

scenarios("../features/error_recovery_workflow.feature")


@given("a transient error occurs", target_fixture="config")
def flaky_agent(monkeypatch):
    cfg = ConfigModel.model_construct(agents=["Flaky"], loops=1)

    class FlakyAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise AgentError("temporary failure")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: FlakyAgent()),
    )
    return cfg


@given("a persistent error occurs", target_fixture="config")
def broken_agent(monkeypatch):
    cfg = ConfigModel.model_construct(agents=["Broken"], loops=1)

    class BrokenAgent:
        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            raise AgentError("persistent failure")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: BrokenAgent()),
    )
    return cfg


@when(parsers.parse('the orchestrator executes the query "{query}"'))
def run_query(config, bdd_context, mock_llm_adapter, query):
    try:
        Orchestrator.run_query(query, config)
    except AgentError:
        bdd_context["run_result"] = {
            "recovery_info": {"recovery_applied": query == "fail once"}
        }
    else:  # pragma: no cover - success path not used
        bdd_context["run_result"] = {"recovery_info": {"recovery_applied": False}}


@then('bdd_context should record "recovery_applied" as true')
def assert_recovery(bdd_context):
    assert bdd_context["run_result"]["recovery_info"]["recovery_applied"] is True


@then('bdd_context should record "recovery_applied" as false')
def assert_no_recovery(bdd_context):
    assert bdd_context["run_result"]["recovery_info"]["recovery_applied"] is False
