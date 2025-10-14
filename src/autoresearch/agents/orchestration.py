"""
Orchestration module for agents.

This module provides imports from the main orchestration module
to maintain compatibility with agent imports.
"""

# Re-export orchestration components needed by agents
from autoresearch.orchestration.metrics import get_orchestration_metrics
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.phases import DialoguePhase
from autoresearch.orchestration.reasoning import ReasoningMode

__all__ = [
    "get_orchestration_metrics",
    "QueryState",
    "DialoguePhase",
    "ReasoningMode",
]
