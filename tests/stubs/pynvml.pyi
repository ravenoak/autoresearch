from __future__ import annotations


class _Utilization:
    gpu: float


class _MemoryInfo:
    used: float


def nvmlInit() -> None: ...


def nvmlShutdown() -> None: ...


def nvmlDeviceGetCount() -> int: ...


def nvmlDeviceGetHandleByIndex(index: int) -> object: ...


def nvmlDeviceGetUtilizationRates(handle: object) -> _Utilization: ...


def nvmlDeviceGetMemoryInfo(handle: object) -> _MemoryInfo: ...


__all__ = [
    "nvmlDeviceGetCount",
    "nvmlDeviceGetHandleByIndex",
    "nvmlDeviceGetMemoryInfo",
    "nvmlDeviceGetUtilizationRates",
    "nvmlInit",
    "nvmlShutdown",
]
