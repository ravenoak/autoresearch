"""Specialized agents for specific research tasks."""

# Import and register specialized agents
from .researcher import ResearcherAgent
from .critic import CriticAgent
from .summarizer import SummarizerAgent
from .planner import PlannerAgent

__all__ = [
    "ResearcherAgent",
    "CriticAgent",
    "SummarizerAgent",
    "PlannerAgent",
]