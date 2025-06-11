"""Dialectical agent infrastructure."""

from .base import Agent, AgentRole
from .registry import AgentRegistry, AgentFactory
from .dialectical import SynthesizerAgent, ContrarianAgent, FactChecker

# Register default dialectical agents on import
AgentFactory.register("Synthesizer", SynthesizerAgent)
AgentFactory.register("Contrarian", ContrarianAgent)
AgentFactory.register("FactChecker", FactChecker)
__all__ = [
    "Agent",
    "AgentRole",
    "AgentRegistry",
    "AgentFactory",
    "SynthesizerAgent",
    "ContrarianAgent",
    "FactChecker",
]
