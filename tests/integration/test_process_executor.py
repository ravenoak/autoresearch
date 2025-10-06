# mypy: ignore-errors
import pytest

from autoresearch.config.models import ConfigModel, DistributedConfig
from autoresearch.distributed import ProcessExecutor
from autoresearch.models import QueryResponse

from tests.integration._executor_stubs import patch_tracking_agent_factory

pytestmark = pytest.mark.slow


def test_process_executor_multi_process(monkeypatch: pytest.MonkeyPatch) -> None:
    pids: list[int] = []
    patch_tracking_agent_factory(monkeypatch, pids)
    cfg: ConfigModel = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
    )
    executor = ProcessExecutor(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    assert len(set(pids)) > 1
    executor.shutdown()


def test_process_result_aggregation(monkeypatch: pytest.MonkeyPatch) -> None:
    pids: list[int] = []
    patch_tracking_agent_factory(monkeypatch, pids)
    cfg: ConfigModel = ConfigModel(
        agents=["A", "B"],
        loops=1,
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2),
    )
    executor = ProcessExecutor(cfg)
    resp = executor.run_query("q")
    assert isinstance(resp, QueryResponse)
    assert len(set(pids)) > 1
    assert executor.result_aggregator is not None
    assert len(executor.result_aggregator.results) == len(cfg.agents)
    executor.shutdown()
