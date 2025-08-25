from __future__ import annotations

from typing import Dict, Any, Type

from autoresearch.agents.base import Agent
from autoresearch.agents.registry import AgentFactory
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState
from autoresearch.distributed.executors import (
    _execute_agent_process,
    _execute_agent_remote,
)


class DummyAgent(Agent):
    name: str = "Dummy"

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        return {"results": {"final_answer": "done"}}


class LocalFactory(AgentFactory):
    _registry: Dict[str, Type[Agent]] = {}
    _instances: Dict[str, Agent] = {}


def _register_dummy() -> None:
    AgentFactory.set_delegate(LocalFactory)
    AgentFactory.register("Dummy", DummyAgent)


def _unregister_dummy() -> None:
    AgentFactory.set_delegate(None)


def test_execute_agent_process():
    _register_dummy()
    try:
        config = ConfigModel(agents=["Dummy"], loops=1)
        state = QueryState(query="q")
        msg = _execute_agent_process("Dummy", state, config)
        assert msg["agent"] == "Dummy"
        assert msg["result"]["results"]["final_answer"] == "done"
    finally:
        _unregister_dummy()


def test_execute_agent_remote():
    _register_dummy()
    try:
        config = ConfigModel(agents=["Dummy"], loops=1)
        state = QueryState(query="q")
        msg = _execute_agent_remote.remote("Dummy", state, config)
        assert msg["agent"] == "Dummy"
        assert msg["result"]["results"]["final_answer"] == "done"
    finally:
        _unregister_dummy()
