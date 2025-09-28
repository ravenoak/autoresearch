from __future__ import annotations

from typing import Any


class _Utilization:
    gpu: float


class _MemoryInfo:
    total: int
    used: int
    free: int


def nvmlInit() -> None: ...


def nvmlShutdown() -> None: ...


def nvmlDeviceGetCount() -> int: ...


def nvmlDeviceGetHandleByIndex(index: int) -> Any: ...


def nvmlDeviceGetUtilizationRates(handle: Any) -> _Utilization: ...


def nvmlDeviceGetMemoryInfo(handle: Any) -> _MemoryInfo: ...


__all__ = [
    "nvmlDeviceGetCount",
    "nvmlDeviceGetHandleByIndex",
    "nvmlDeviceGetMemoryInfo",
    "nvmlDeviceGetUtilizationRates",
    "nvmlInit",
    "nvmlShutdown",
]
