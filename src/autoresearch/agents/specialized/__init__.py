"""Specialized agents for specific research tasks."""

# Import and register specialized agents
from .researcher import ResearcherAgent
from .critic import CriticAgent
from .summarizer import SummarizerAgent
from .planner import PlannerAgent
from .moderator import ModeratorAgent
from .domain_specialist import DomainSpecialistAgent
from .user_agent import UserAgent

__all__ = [
    "ResearcherAgent",
    "CriticAgent",
    "SummarizerAgent",
    "PlannerAgent",
    "ModeratorAgent",
    "DomainSpecialistAgent",
    "UserAgent",
]
