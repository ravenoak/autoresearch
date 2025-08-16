from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils


def test_token_budget_adjustment(monkeypatch, orchestrator_runner):
    recorded = {}

    def fake_execute_cycle(
        loop,
        loops,
        agents,
        primus_index,
        max_errors,
        state,
        config,
        metrics,
        callbacks,
        agent_factory,
        storage_manager,
        tracer,
        cb_manager,
    ):
        recorded["budget"] = config.token_budget
        return primus_index

    monkeypatch.setattr(OrchestrationUtils, "execute_cycle", fake_execute_cycle)

    base_cfg = ConfigModel(agents=["A"], loops=1, token_budget=90)
    cfg = base_cfg.model_copy(
        update={"group_size": 2, "total_groups": 2, "total_agents": 3}
    )

    orchestrator_runner().run_query("q", cfg)

    assert recorded["budget"] == 13
