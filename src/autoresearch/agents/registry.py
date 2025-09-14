"""
Registry and Factory for agent management.

This module provides classes for registering, retrieving, and creating agent instances.
It includes a registry for agent types and a factory for creating agent instances.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Type

from ..llm.adapters import LLMAdapter
from .base import Agent

log = logging.getLogger(__name__)


@dataclass
class Coalition:
    """Grouping of multiple agents treated as a single unit."""

    name: str
    members: List[str]


class AgentRegistry:
    """Registry of available agent types.

    This class provides a central registry for all available agent types.
    It allows registering agent classes, retrieving them by name, and listing
    all available agent types.
    """

    _registry: Dict[str, Type[Agent]] = {}
    _coalitions: Dict[str, Coalition] = {}

    @classmethod
    def register(cls, name: str, agent_class: Type[Agent]) -> None:
        """Register an agent class.

        Args:
            name: The name to register the agent class under
            agent_class: The agent class to register
        """
        cls._registry[name] = agent_class
        log.info(f"Registered agent: {name}")

    @classmethod
    def get_class(cls, name: str) -> Type[Agent]:
        """Get agent class by name.

        Args:
            name: The name of the agent class to retrieve

        Returns:
            The agent class registered under the given name

        Raises:
            ValueError: If no agent class is registered under the given name
        """
        if name not in cls._registry:
            raise ValueError(f"Unknown agent type: {name}")
        return cls._registry[name]

    @classmethod
    def list_available(cls) -> List[str]:
        """List available agent types.

        Returns:
            A list of names of all registered agent types
        """
        return list(cls._registry.keys())

    @classmethod
    def reset(cls) -> None:
        """Clear all registered agents and coalitions."""
        cls._registry.clear()
        cls._coalitions.clear()

    @classmethod
    @contextmanager
    def temporary_state(cls):
        """Isolate registry state within a context."""
        registry = dict(cls._registry)
        coalitions = dict(cls._coalitions)
        try:
            yield cls
        finally:
            cls._registry = registry
            cls._coalitions = coalitions

    # ------------------------------------------------------------------
    # Coalition management
    # ------------------------------------------------------------------

    @classmethod
    def create_coalition(cls, name: str, members: List[str]) -> None:
        """Register a named coalition of agents."""
        for member in members:
            if member not in cls._registry:
                raise ValueError(f"Unknown agent type: {member}")
        cls._coalitions[name] = Coalition(name=name, members=members)

    @classmethod
    def get_coalition(cls, name: str) -> List[str]:
        """Return members of a registered coalition."""
        coalition = cls._coalitions.get(name)
        return coalition.members if coalition else []

    @classmethod
    def get_coalition_obj(cls, name: str) -> Coalition | None:
        """Return the Coalition object if registered."""
        return cls._coalitions.get(name)

    @classmethod
    def list_coalitions(cls) -> List[str]:
        """List all registered coalitions."""
        return list(cls._coalitions.keys())


class AgentFactory:
    """Factory for creating and retrieving agents.

    This class provides a factory for creating and retrieving agent instances.
    It maintains a registry of agent classes and a cache of agent instances.
    It also supports delegation to another factory implementation for testing.
    """

    _registry: Dict[str, Type[Agent]] = {}
    _instances: Dict[str, Agent] = {}
    _lock = Lock()
    _delegate: type["AgentFactory"] | None = None

    @classmethod
    def set_delegate(cls, delegate: type["AgentFactory"] | None) -> None:
        """Replace the active AgentFactory implementation.

        This method is primarily used for testing to inject a mock factory.

        Args:
            delegate: The factory class to delegate to, or None to remove delegation
        """
        cls._delegate = delegate

    @classmethod
    def get_delegate(cls) -> type["AgentFactory"] | None:
        """Return the injected AgentFactory class if any.

        Returns:
            The delegate factory class, or None if no delegate is set
        """
        return cls._delegate

    @classmethod
    def register(cls, name: str, agent_class: Type[Agent]) -> None:
        """Register an agent class.

        Args:
            name: The name to register the agent class under
            agent_class: The agent class to register

        Note:
            If a delegate is set, the registration is forwarded to the delegate.
            The agent class is also registered with the AgentRegistry.
        """
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.register(name, agent_class)
        with cls._lock:
            cls._registry[name] = agent_class
            AgentRegistry.register(name, agent_class)
            log.info(f"Registered agent: {name}")

    @classmethod
    def get(cls, name: str, llm_adapter: LLMAdapter | None = None) -> Agent:
        """Get or create an agent instance.

        This method returns a cached instance if available, or creates a new one.
        The instance is cached for future use.

        Args:
            name: The name of the agent to get or create
            llm_adapter: Optional LLM adapter to inject into the agent

        Returns:
            An agent instance of the requested type

        Raises:
            ValueError: If no agent class is registered under the given name
        """
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.get(name, llm_adapter)
        with cls._lock:
            if name not in cls._instances:
                if name not in cls._registry:
                    raise ValueError(f"Unknown agent: {name}")
                cls._instances[name] = cls._registry[name](name=name, llm_adapter=llm_adapter)
            return cls._instances[name]

    @classmethod
    def create(cls, name: str, llm_adapter: LLMAdapter | None = None, **kwargs: Any) -> Agent:
        """Create a new agent instance with custom parameters.

        This method always creates a new instance and does not cache it.
        Use this method when you need an agent with custom parameters.

        Args:
            name: The name of the agent to create
            llm_adapter: Optional LLM adapter to inject into the agent
            **kwargs: Additional parameters to pass to the agent constructor

        Returns:
            A new agent instance of the requested type

        Raises:
            ValueError: If no agent class is registered under the given name
        """
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.create(name, llm_adapter, **kwargs)
        with cls._lock:
            if name not in cls._registry:
                raise ValueError(f"Unknown agent: {name}")
            return cls._registry[name](name=name, llm_adapter=llm_adapter, **kwargs)

    @classmethod
    def list_available(cls) -> List[str]:
        """List available agent types.

        Returns:
            A list of names of all registered agent types
        """
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.list_available()
        return list(cls._registry.keys())

    @classmethod
    def reset(cls) -> None:
        """Clear registered classes, instances, and delegates."""
        cls._registry.clear()
        cls._instances.clear()
        cls._delegate = None

    @classmethod
    @contextmanager
    def temporary_state(cls):
        """Provide a context with isolated factory state."""
        registry = dict(cls._registry)
        instances = dict(cls._instances)
        delegate = cls._delegate
        try:
            yield cls
        finally:
            cls._registry = registry
            cls._instances = instances
            cls._delegate = delegate

    @classmethod
    def reset_instances(cls) -> None:
        """Clear all cached instances.

        This method removes all cached agent instances, forcing new instances
        to be created on the next call to get(). This is useful for testing
        and for resetting the state of the application.
        """
        if cls._delegate and cls._delegate is not cls:
            return cls._delegate.reset_instances()
        with cls._lock:
            cls._instances.clear()
