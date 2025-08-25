import asyncio
import time
from typing import List

import pytest
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import orchestrator as orch_mod
from autoresearch.orchestration.reasoning import ReasoningMode

Orchestrator = orch_mod.Orchestrator
AgentFactory = orch_mod.AgentFactory


class _SleepAgent:
    def __init__(self, name: str, starts: List[float], delay: float = 0.3) -> None:
        self.name = name
        self.delay = delay
        self.starts = starts

    def can_execute(self, state, config):  # pragma: no cover - simple
        return True

    def execute(self, state, config, **kwargs):
        self.starts.append(time.perf_counter())
        time.sleep(self.delay)
        state.results["final_answer"] = "ok"
        return {"results": {self.name: "ok"}}


async def _run(concurrent: bool, monkeypatch: pytest.MonkeyPatch) -> List[float]:
    starts: List[float] = []
    monkeypatch.setattr(AgentFactory, "get", lambda name: _SleepAgent(name, starts))
    cfg = ConfigModel(agents=["A", "B"], loops=1)
    orch = Orchestrator()
    monkeypatch.setattr(
        orch,
        "_parse_config",
        lambda config: {
            "agents": ["A", "B"],
            "agent_groups": [["A", "B"]],
            "primus_index": 0,
            "loops": 1,
            "mode": ReasoningMode.DIALECTICAL,
            "max_errors": 3,
            "circuit_breaker_threshold": 3,
            "circuit_breaker_cooldown": 30,
            "retry_attempts": 1,
            "retry_backoff": 0.0,
            "enable_agent_messages": False,
            "enable_feedback": False,
            "coalitions": {},
        },
    )
    await orch.run_query_async("q", cfg, concurrent=concurrent)
    return starts


@pytest.mark.integration
def test_agent_execution_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    seq = asyncio.run(_run(False, monkeypatch))
    conc = asyncio.run(_run(True, monkeypatch))
    assert seq[1] - seq[0] >= 0.3
    assert conc[1] - conc[0] < 0.3
