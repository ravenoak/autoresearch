#!/usr/bin/env python
"""Run a token and memory benchmark for a typical query."""

from __future__ import annotations

import sys
from types import ModuleType

# Avoid heavy optional dependencies during benchmarks
sys.modules.setdefault("bertopic", ModuleType("bertopic"))
sys.modules.setdefault("sentence_transformers", ModuleType("sentence_transformers"))

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from autoresearch.agents.base import Agent
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.storage import StorageManager


class DummyAdapter:
    def generate(self, _prompt: str) -> None:
        return None


class DummyAgent(Agent):
    """Minimal agent used for benchmarks."""

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        return True

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, Any]:
        adapter = self.llm_adapter or DummyAdapter()
        adapter.generate("hello world")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def run_benchmark() -> dict[str, float | dict[str, dict[str, int]]]:
    """Execute a benchmark query and return metrics."""
    def _get_dummy_agent(name: str, llm_adapter=None) -> DummyAgent:
        adapter = llm_adapter or DummyAdapter()
        return DummyAgent(name=name, llm_adapter=adapter)

    AgentFactory.get = cast(
        Callable[[str, Any], Agent],
        _get_dummy_agent,
    )
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy")

    memory_before = StorageManager._current_ram_mb()
    start = time.perf_counter()
    response = Orchestrator().run_query("benchmark query", cfg)
    duration = time.perf_counter() - start
    memory_after = StorageManager._current_ram_mb()

    tokens = response.metrics["execution_metrics"]["agent_tokens"]
    return {
        "duration_seconds": duration,
        "memory_delta_mb": memory_after - memory_before,
        "tokens": tokens,
    }


def main() -> None:
    metrics = run_benchmark()
    path = Path("tests/integration/baselines/token_memory.json")
    path.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"Baseline written to {path}")


if __name__ == "__main__":
    main()
