import asyncio
import time
from dataclasses import asdict, dataclass, field
import pytest
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import orchestrator as orch_mod
from autoresearch.orchestration.reasoning import ReasoningMode
from autoresearch.orchestration.state import QueryState
from autoresearch.storage_typing import JSONDict

from tests.integration._orchestrator_stubs import AgentDouble, patch_agent_factory_get

Orchestrator = orch_mod.Orchestrator


@dataclass(slots=True)
class ParsedConfigParams:
    agents: list[str]
    agent_groups: list[list[str]]
    primus_index: int
    loops: int
    mode: ReasoningMode
    max_errors: int
    circuit_breaker_threshold: int
    circuit_breaker_cooldown: int
    retry_attempts: int
    retry_backoff: float
    enable_agent_messages: bool
    enable_feedback: bool
    coalitions: dict[str, list[str]]


@dataclass(slots=True)
class SleepAgentDouble(AgentDouble):
    starts: list[float] = field(default_factory=list)
    delay: float = 0.3

    def execute(
        self,
        state: QueryState,
        config: ConfigModel,
        **_: object,
    ) -> JSONDict:
        self.starts.append(time.perf_counter())
        time.sleep(self.delay)
        payload: JSONDict = {"results": {self.name: "ok"}}
        state.update(payload)
        state.results["final_answer"] = "ok"
        return payload


def _install_sleep_agents(
    monkeypatch: pytest.MonkeyPatch,
    starts: list[float],
    delay: float = 0.3,
) -> None:
    agents = (
        SleepAgentDouble(name="A", starts=starts, delay=delay),
        SleepAgentDouble(name="B", starts=starts, delay=delay),
    )
    patch_agent_factory_get(monkeypatch, agents)


def _patch_config(monkeypatch: pytest.MonkeyPatch, orchestrator: Orchestrator) -> None:
    params = ParsedConfigParams(
        agents=["A", "B"],
        agent_groups=[["A", "B"]],
        primus_index=0,
        loops=1,
        mode=ReasoningMode.DIALECTICAL,
        max_errors=3,
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown=30,
        retry_attempts=1,
        retry_backoff=0.0,
        enable_agent_messages=False,
        enable_feedback=False,
        coalitions={},
    )

    def _stub_parse_config(_: ConfigModel) -> dict[str, object]:
        return asdict(params)

    monkeypatch.setattr(orchestrator, "_parse_config", _stub_parse_config)


async def _run(concurrent: bool, monkeypatch: pytest.MonkeyPatch) -> list[float]:
    starts: list[float] = []
    _install_sleep_agents(monkeypatch, starts)
    cfg = ConfigModel(agents=["A", "B"], loops=1)
    orch = Orchestrator()
    _patch_config(monkeypatch, orch)
    await orch.run_query_async("q", cfg, concurrent=concurrent)
    return starts


@pytest.mark.integration
def test_agent_execution_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    seq = asyncio.run(_run(False, monkeypatch))
    conc = asyncio.run(_run(True, monkeypatch))
    assert seq[1] - seq[0] >= 0.3
    assert conc[1] - conc[0] < 0.3
