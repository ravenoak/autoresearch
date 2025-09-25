from __future__ import annotations

from typing import Any


class _MemoryInfo:
    rss: int


class _VirtualMemory:
    percent: float
    available: int


class Process:
    def __init__(self, pid: int | None = None) -> None: ...

    def memory_info(self) -> _MemoryInfo: ...


class Popen:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def communicate(self, timeout: float | None = None) -> tuple[str, str]: ...

    def wait(self, timeout: float | None = None) -> int: ...


def cpu_percent(interval: float | None = ...) -> float: ...


def virtual_memory() -> _VirtualMemory: ...


__all__ = ["Popen", "Process", "cpu_percent", "virtual_memory"]
