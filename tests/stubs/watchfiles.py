"""Typed stub for the :mod:`watchfiles` package."""

from __future__ import annotations

from collections.abc import Generator
from enum import Enum, auto
from pathlib import Path
from threading import Event
from types import ModuleType
from typing import Iterable, Protocol, cast

from ._registry import install_stub_module

PathLike = str | Path


class Change(Enum):
    """Subset of the :mod:`watchfiles` change types."""

    added = auto()
    modified = auto()
    deleted = auto()


class WatchFilter(Protocol):
    def __call__(self, change: Change, path: str) -> bool: ...


WatchEvent = tuple[Change, str]


def watch(
    *paths: PathLike,
    watch_filter: WatchFilter | None = None,
    debug: bool = False,
    stop_event: Event | None = None,
    yield_on_timeout: bool = False,
    raise_interrupt: bool = False,
    debounce: float | None = None,
    min_sleep: float = 0.0,
    step: float = 1.0,
    timeout: float | None = None,
) -> Generator[WatchEvent, None, None]:
    del paths, watch_filter, debug, stop_event, yield_on_timeout
    del raise_interrupt, debounce, min_sleep, step, timeout
    if False:
        yield (Change.modified, "")


class WatchfilesModule(Protocol):
    Change: type[Change]

    def watch(
        self,
        *paths: PathLike,
        watch_filter: WatchFilter | None = None,
        debug: bool = False,
        stop_event: Event | None = None,
        yield_on_timeout: bool = False,
        raise_interrupt: bool = False,
        debounce: float | None = None,
        min_sleep: float = 0.0,
        step: float = 1.0,
        timeout: float | None = None,
    ) -> Iterable[WatchEvent]:
        ...


class _WatchfilesModule(ModuleType):
    Change = Change

    def __init__(self) -> None:
        super().__init__("watchfiles")

    def watch(
        self,
        *paths: PathLike,
        watch_filter: WatchFilter | None = None,
        debug: bool = False,
        stop_event: Event | None = None,
        yield_on_timeout: bool = False,
        raise_interrupt: bool = False,
        debounce: float | None = None,
        min_sleep: float = 0.0,
        step: float = 1.0,
        timeout: float | None = None,
    ) -> Iterable[WatchEvent]:
        return watch(
            *paths,
            watch_filter=watch_filter,
            debug=debug,
            stop_event=stop_event,
            yield_on_timeout=yield_on_timeout,
            raise_interrupt=raise_interrupt,
            debounce=debounce,
            min_sleep=min_sleep,
            step=step,
            timeout=timeout,
        )


watchfiles = cast(WatchfilesModule, install_stub_module("watchfiles", _WatchfilesModule))

__all__ = ["Change", "WatchFilter", "WatchfilesModule", "watch", "watchfiles"]
