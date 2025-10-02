"""Factories and helpers for distributed broker tests."""

from __future__ import annotations

from typing import Any

from autoresearch.distributed.broker import AgentResultMessage


def build_agent_result_message(
    *,
    agent: str = "agent",
    result: dict[str, Any] | None = None,
    pid: int = 1234,
) -> AgentResultMessage:
    """Construct a typed :class:`AgentResultMessage` payload for broker tests."""

    return {
        "action": "agent_result",
        "agent": agent,
        "result": result or {"status": "ok"},
        "pid": pid,
    }


__all__ = ["build_agent_result_message"]
