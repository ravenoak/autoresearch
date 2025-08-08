"""Scenario registrations for extended error recovery behavior tests."""

from __future__ import annotations

from pytest_bdd import scenario

# Reuse all step definitions from the base error recovery steps module
from .error_recovery_steps import *  # noqa: F401,F403


@scenario(
    "../features/error_recovery_extended.feature",
    "Recovery after agent timeout",
)
def test_error_recovery_timeout() -> None:
    """System recovers after an agent times out."""
    return


@scenario(
    "../features/error_recovery_extended.feature",
    "Recovery after agent failure",
)
def test_error_recovery_agent_failure() -> None:
    """System handles agent execution failures gracefully."""
    return


@scenario(
    "../features/error_recovery_extended.feature",
    "Recovery after agent timeout in direct mode",
)
def test_error_recovery_timeout_direct() -> None:
    """Timeout recovery works in direct reasoning mode."""
    return


@scenario(
    "../features/error_recovery_extended.feature",
    "Unsupported reasoning mode during extended recovery fails gracefully",
)
def test_error_recovery_extended_unsupported() -> None:
    """Unsupported reasoning modes surface an error without executing agents."""
    return


@scenario(
    "../features/error_recovery_extended.feature",
    "Recovery after network outage with fallback agent",
)
def test_error_recovery_network_fallback() -> None:
    """Fallback agent handles network outages."""
    return
