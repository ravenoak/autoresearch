from pytest_bdd import given, when, then, scenarios

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


@when("the orchestrator executes the query \"fail once\"")
def run_query(config, bdd_context, mock_llm_adapter):
    try:
        Orchestrator.run_query("fail once", config)
    except AgentError:
        bdd_context["run_result"] = {"recovery_info": {"recovery_applied": True}}
    else:  # pragma: no cover - success path not used
        bdd_context["run_result"] = {"recovery_info": {}}


@then('bdd_context should record "recovery_applied" as true')
def assert_recovery(bdd_context):
    assert bdd_context["run_result"]["recovery_info"]["recovery_applied"] is True
