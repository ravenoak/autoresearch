"""Orchestration module for agent coordination."""

from importlib import import_module

from .reasoning import ChainOfThoughtStrategy, ReasoningMode, ReasoningStrategy

__all__ = [
    "ReasoningMode",
    "ReasoningStrategy",
    "ChainOfThoughtStrategy",
    "TaskCoordinator",
    "TaskStatus",
]


def __getattr__(name: str) -> object:
    """Lazily import coordinator symbols to avoid circular imports."""

    if name in {"TaskCoordinator", "TaskStatus"}:
        module = import_module(".coordinator", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
