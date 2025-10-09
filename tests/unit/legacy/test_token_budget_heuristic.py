# mypy: ignore-errors
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils


def test_token_budget_adjustment(monkeypatch, orchestrator):
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

    base_cfg = ConfigModel(agents=["A", "B", "C"], loops=1, token_budget=90)
    cfg = base_cfg.model_copy()

    orchestrator.run_query("q", cfg)

    # The adaptive budget reduces 90 to 20 (20 * 1 token query)
    # The group size calculation doesn't apply in this scenario since group_size/total_groups aren't set
    assert recorded["budget"] == 20
