#!/usr/bin/env python
"""Run a token and memory benchmark for a typical query."""

from __future__ import annotations

import sys

# Avoid heavy optional dependencies during benchmarks
sys.modules.setdefault("bertopic", None)
sys.modules.setdefault("sentence_transformers", None)

import json
import time
from pathlib import Path

from autoresearch.config import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator, AgentFactory
from autoresearch.storage import StorageManager


class DummyAgent:
    """Minimal agent used for benchmarks."""

    def __init__(self, name: str, llm_adapter=None) -> None:
        self.name = name

    def can_execute(self, state, config) -> bool:  # type: ignore[override]
        return True

    def execute(self, state, config, adapter=None):  # type: ignore[override]
        adapter.generate("hello world")
        state.results[self.name] = "ok"
        state.results["final_answer"] = "answer"
        return {"results": {self.name: "ok"}}


def run_benchmark() -> dict[str, float | dict[str, dict[str, int]]]:
    """Execute a benchmark query and return metrics."""
    AgentFactory.get = lambda name, llm_adapter=None: DummyAgent(name)  # type: ignore
    cfg = ConfigModel(agents=["Dummy"], loops=1, llm_backend="dummy")

    memory_before = StorageManager._current_ram_mb()
    start = time.perf_counter()
    response = Orchestrator.run_query("benchmark query", cfg)
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
