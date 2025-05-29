"""
Base Agent class and role definitions for the dialectical system.
"""
from typing import Dict, Any
from enum import Enum
from pydantic import BaseModel

from ..config import ConfigModel
from ..orchestration.state import QueryState

class AgentRole(str, Enum):
    """Enumeration of standard agent roles in the dialectical system."""
    SYNTHESIZER = "Synthesizer"
    CONTRARIAN = "Contrarian"
    FACT_CHECKER = "FactChecker"
    SPECIALIST = "Specialist"
    MODERATOR = "Moderator"
    USER = "User"


class Agent(BaseModel):
    """Base agent interface for dialectical cycle."""
    name: str
    role: AgentRole = AgentRole.SPECIALIST
    enabled: bool = True

    class Config:
        arbitrary_types_allowed = True

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Execute agent's task on the given state."""
        raise NotImplementedError("Agent subclasses must implement execute()")

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Determine if this agent should execute in the current state."""
        return self.enabled
