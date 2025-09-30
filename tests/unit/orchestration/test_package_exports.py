"""Tests for the public exports of :mod:`autoresearch.orchestration`."""

from autoresearch.agents.registry import AgentFactory as RegistryAgentFactory
from autoresearch.agents.registry import AgentRegistry as RegistryAgentRegistry
from autoresearch.orchestration import (
    AgentFactory,
    AgentRegistry,
    Orchestrator,
    StorageManager,
)
from autoresearch.orchestration.orchestrator import Orchestrator as ModuleOrchestrator
from autoresearch.storage import StorageManager as ModuleStorageManager


def test_agent_factory_export() -> None:
    """AgentFactory exported from package is the canonical implementation."""

    assert AgentFactory is RegistryAgentFactory


def test_agent_registry_export() -> None:
    """AgentRegistry exported from package is the canonical implementation."""

    assert AgentRegistry is RegistryAgentRegistry


def test_orchestrator_export() -> None:
    """Orchestrator exported from package resolves to orchestrator module class."""

    assert Orchestrator is ModuleOrchestrator


def test_storage_manager_export() -> None:
    """StorageManager exported from package resolves to storage module class."""

    assert StorageManager is ModuleStorageManager
