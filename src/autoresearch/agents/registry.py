"""
Registry and Factory for agent management.
"""

from typing import Dict, Type, List
from threading import Lock
import logging

from .base import Agent

log = logging.getLogger(__name__)


class AgentRegistry:
    """Registry of available agent types."""

    _registry: Dict[str, Type[Agent]] = {}

    @classmethod
    def register(cls, name: str, agent_class: Type[Agent]) -> None:
        """Register an agent class."""
        cls._registry[name] = agent_class
        log.info(f"Registered agent: {name}")

    @classmethod
    def get_class(cls, name: str) -> Type[Agent]:
        """Get agent class by name."""
        if name not in cls._registry:
            raise ValueError(f"Unknown agent type: {name}")
        return cls._registry[name]

    @classmethod
    def list_available(cls) -> List[str]:
        """List available agent types."""
        return list(cls._registry.keys())


class AgentFactory:
    """Factory for creating and retrieving agents."""

    _registry: Dict[str, Type[Agent]] = {}
    _instances: Dict[str, Agent] = {}
    _lock = Lock()
    _delegate: type["AgentFactory"] | None = None

    @classmethod
    def set_delegate(cls, delegate: type["AgentFactory"] | None) -> None:
        """Replace the active AgentFactory implementation."""
        cls._delegate = delegate

    @classmethod
    def get_delegate(cls) -> type["AgentFactory"] | None:
        """Return the injected AgentFactory class if any."""
        return cls._delegate

    @classmethod
    def register(cls, name: str, agent_class: Type[Agent]) -> None:
        """Register an agent class."""
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.register(name, agent_class)
        with cls._lock:
            cls._registry[name] = agent_class
            AgentRegistry.register(name, agent_class)
            log.info(f"Registered agent: {name}")

    @classmethod
    def get(cls, name: str) -> Agent:
        """Get or create an agent instance."""
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.get(name)
        with cls._lock:
            if name not in cls._instances:
                if name not in cls._registry:
                    raise ValueError(f"Unknown agent: {name}")
                cls._instances[name] = cls._registry[name](name=name)
            return cls._instances[name]

    @classmethod
    def create(cls, name: str, **kwargs) -> Agent:
        """Create a new agent instance with custom parameters."""
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.create(name, **kwargs)
        with cls._lock:
            if name not in cls._registry:
                raise ValueError(f"Unknown agent: {name}")
            return cls._registry[name](name=name, **kwargs)

    @classmethod
    def list_available(cls) -> List[str]:
        """List available agent types."""
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.list_available()
        return list(cls._registry.keys())

    @classmethod
    def reset_instances(cls) -> None:
        """Clear all cached instances."""
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.reset_instances()
        with cls._lock:
            cls._instances.clear()
