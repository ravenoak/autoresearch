"""
Module initialization for the agents package.

This module provides the agent infrastructure for the dialectical reasoning system.
"""

from .base import Agent, AgentRole
from .registry import AgentRegistry, AgentFactory

__all__ = ["Agent", "AgentRole", "AgentRegistry", "AgentFactory"]
