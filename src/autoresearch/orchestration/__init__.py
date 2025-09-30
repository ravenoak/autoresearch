"""Orchestration module for agent coordination."""

from importlib import import_module

from .reasoning import ChainOfThoughtStrategy, ReasoningMode, ReasoningStrategy

__all__ = [
    "AgentFactory",
    "AgentRegistry",
    "ChainOfThoughtStrategy",
    "Orchestrator",
    "ReasoningMode",
    "ReasoningStrategy",
    "StorageManager",
    "TaskCoordinator",
    "TaskEdge",
    "TaskGraph",
    "TaskNode",
    "TaskStatus",
]


def __getattr__(name: str) -> object:
    """Lazily import coordinator symbols to avoid circular imports."""

    module_map = {
        "AgentFactory": "..agents.registry",
        "AgentRegistry": "..agents.registry",
        "Orchestrator": ".orchestrator",
        "StorageManager": "..storage",
        "TaskCoordinator": ".coordinator",
        "TaskEdge": ".task_graph",
        "TaskGraph": ".task_graph",
        "TaskNode": ".task_graph",
        "TaskStatus": ".coordinator",
    }

    if name in module_map:
        module = import_module(module_map[name], __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
