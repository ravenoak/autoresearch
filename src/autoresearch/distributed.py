"""Utilities for distributed agent execution using Ray."""

from __future__ import annotations

from typing import Dict, Callable, Any, List
import os

import ray

from .config import ConfigModel
from .orchestration.state import QueryState
from .orchestration.orchestrator import AgentFactory
from .models import QueryResponse


@ray.remote
def _execute_agent_remote(agent_name: str, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
    """Execute a single agent in a Ray worker."""
    agent = AgentFactory.get(agent_name)
    result = agent.execute(state, config)
    return {"agent": agent_name, "result": result, "pid": os.getpid()}


class RayExecutor:
    """Simple distributed orchestrator that dispatches agents via Ray."""

    def __init__(self, config: ConfigModel) -> None:
        self.config = config
        address = None
        num_cpus = None
        if hasattr(config, "distributed_config"):
            cfg = config.distributed_config
            address = cfg.address
            num_cpus = cfg.num_cpus
        ray.init(address=address, num_cpus=num_cpus, ignore_reinit_error=True, configure_logging=False)

    def run_query(self, query: str, callbacks: Dict[str, Callable[..., None]] | None = None) -> QueryResponse:
        """Run agents in parallel across processes."""
        callbacks = callbacks or {}
        state = QueryState(query=query, primus_index=getattr(self.config, "primus_start", 0))
        for loop in range(self.config.loops):
            futures = [
                _execute_agent_remote.remote(name, state, self.config)
                for name in self.config.agents
            ]
            results = ray.get(futures)
            for res in results:
                state.update(res["result"])
            if callbacks.get("on_cycle_end"):
                callbacks["on_cycle_end"](loop, state)
            state.cycle += 1
        return state.synthesize()
