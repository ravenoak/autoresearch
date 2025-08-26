"""Behavior step package."""

from .common_steps import (
    app_running,
    app_running_with_default,
    application_running,
    cli_app,
)  # noqa: F401

# Import step modules so pytest-bdd discovers them when running the package.
for _mod in [
    "distributed_execution_steps",
    "config_cli_steps",
    "backup_cli_steps",
    "serve_cli_steps",
    "completion_cli_steps",
    "capabilities_cli_steps",
    "api_auth_steps",
    "api_orchestrator_integration_steps",
]:
    try:
        __import__(f"tests.behavior.steps.{_mod}")
    except Exception:  # pragma: no cover - optional imports
        pass

__all__ = [
    "app_running",
    "app_running_with_default",
    "application_running",
    "cli_app",
]
