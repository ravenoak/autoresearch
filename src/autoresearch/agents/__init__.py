"""Dialectical agent infrastructure."""

from .base import Agent, AgentRole
from .registry import AgentRegistry, AgentFactory
from .dialectical import SynthesizerAgent, ContrarianAgent, FactChecker
from .specialized import ResearcherAgent, CriticAgent, SummarizerAgent, PlannerAgent

# Register default dialectical agents on import
AgentFactory.register("Synthesizer", SynthesizerAgent)
AgentFactory.register("Contrarian", ContrarianAgent)
AgentFactory.register("FactChecker", FactChecker)

# Register specialized agents on import
AgentFactory.register("Researcher", ResearcherAgent)
AgentFactory.register("Critic", CriticAgent)
AgentFactory.register("Summarizer", SummarizerAgent)
AgentFactory.register("Planner", PlannerAgent)

__all__ = [
    "Agent",
    "AgentRole",
    "AgentRegistry",
    "AgentFactory",
    "SynthesizerAgent",
    "ContrarianAgent",
    "FactChecker",
    "ResearcherAgent",
    "CriticAgent",
    "SummarizerAgent",
    "PlannerAgent",
]
