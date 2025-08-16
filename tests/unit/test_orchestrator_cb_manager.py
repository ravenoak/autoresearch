from unittest.mock import patch

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator


def test_cb_manager_is_instance_scoped():
    cfg = ConfigModel(loops=1, agents=["Synthesizer"])

    o1 = Orchestrator()
    o2 = Orchestrator()

    orig_run_query = Orchestrator.run_query
    with patch.object(Orchestrator, "run_query", orig_run_query):
        with patch(
            "autoresearch.orchestration.orchestrator.OrchestrationUtils.execute_cycle",
            return_value=0,
        ):
            o1.run_query("q", cfg)
            o2.run_query("q", cfg)

    assert o1._cb_manager is not None
    assert o2._cb_manager is not None
    assert o1._cb_manager is not o2._cb_manager
