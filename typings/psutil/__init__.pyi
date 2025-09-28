from __future__ import annotations

from typing import Any, Iterable, Mapping


class _ProcessMemoryInfo:
    rss: int


class _VirtualMemory:
    percent: float
    available: int


class Process:
    pid: int

    def __init__(self, pid: int | None = ...) -> None: ...

    def memory_info(self) -> _ProcessMemoryInfo: ...

    def cpu_percent(self, interval: float | None = ...) -> float: ...


class Popen:
    pid: int

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def communicate(self, timeout: float | None = ...) -> tuple[str, str]: ...

    def wait(self, timeout: float | None = ...) -> int: ...


def cpu_percent(interval: float | None = ..., *, percpu: bool = ...) -> float | list[float]: ...


def virtual_memory() -> _VirtualMemory: ...


__all__ = ["Popen", "Process", "cpu_percent", "virtual_memory"]
