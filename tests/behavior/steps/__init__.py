from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

"""Behavior step package."""

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.behavior.context import (
        APICapture,
        BehaviorContext,
        CLIInvocation,
        get_optional,
        get_required,
        set_value,
    )

    app_running: Callable[..., None]
    app_running_with_default: Callable[..., None]
    application_running: Callable[..., None]
    cli_app: Callable[..., None]
else:
    _common_steps = importlib.import_module(
        "tests.behavior.steps.common_steps"
    )
    app_running = _common_steps.app_running
    app_running_with_default = _common_steps.app_running_with_default
    application_running = _common_steps.application_running
    cli_app = _common_steps.cli_app

    _context = importlib.import_module("tests.behavior.context")
    BehaviorContext = _context.BehaviorContext
    CLIInvocation = _context.CLIInvocation
    APICapture = _context.APICapture
    get_required = _context.get_required
    get_optional = _context.get_optional
    set_value = _context.set_value

if not TYPE_CHECKING:
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
        "evaluation_steps",
    ]:
        try:
            importlib.import_module(f"tests.behavior.steps.{_mod}")
        except Exception:  # pragma: no cover - optional imports
            pass

__all__ = [
    "app_running",
    "app_running_with_default",
    "application_running",
    "cli_app",
    "BehaviorContext",
    "CLIInvocation",
    "APICapture",
    "get_required",
    "get_optional",
    "set_value",
]
