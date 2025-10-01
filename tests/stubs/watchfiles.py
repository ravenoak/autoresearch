"""Typed stub for the :mod:`watchfiles` package."""

from __future__ import annotations

from collections.abc import Generator, Iterable
from enum import Enum, auto
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module

PathLike = str | Path


class SupportsIsSet(Protocol):
    def is_set(self) -> bool: ...


class Change(Enum):
    """Subset of the :mod:`watchfiles` change types."""

    added = auto()
    modified = auto()
    deleted = auto()


class WatchFilter(Protocol):
    def __call__(self, change: Change, path: str) -> bool: ...


WatchEvent = tuple[Change, str]
WatchEventBatch = set[WatchEvent]


def watch(
    *paths: PathLike,
    watch_filter: WatchFilter | None = None,
    debounce: int = 1_600,
    step: int = 50,
    stop_event: SupportsIsSet | None = None,
    rust_timeout: int = 5_000,
    yield_on_timeout: bool = False,
    debug: bool | None = None,
    raise_interrupt: bool = True,
    force_polling: bool | None = None,
    poll_delay_ms: int = 300,
    recursive: bool = True,
    ignore_permission_denied: bool | None = None,
) -> Generator[WatchEventBatch, None, None]:
    del (
        paths,
        watch_filter,
        debounce,
        step,
        stop_event,
        rust_timeout,
        yield_on_timeout,
        debug,
        raise_interrupt,
        force_polling,
        poll_delay_ms,
        recursive,
        ignore_permission_denied,
    )
    if False:
        yield {(Change.modified, "")}


class WatchfilesModule(Protocol):
    Change: type[Change]

    def watch(
        self,
        *paths: PathLike,
        watch_filter: WatchFilter | None = None,
        debounce: int = 1_600,
        step: int = 50,
        stop_event: SupportsIsSet | None = None,
        rust_timeout: int = 5_000,
        yield_on_timeout: bool = False,
        debug: bool | None = None,
        raise_interrupt: bool = True,
        force_polling: bool | None = None,
        poll_delay_ms: int = 300,
        recursive: bool = True,
        ignore_permission_denied: bool | None = None,
    ) -> Iterable[WatchEventBatch]:
        ...


class _WatchfilesModule(ModuleType):
    Change = Change

    def __init__(self) -> None:
        super().__init__("watchfiles")

    def watch(
        self,
        *paths: PathLike,
        watch_filter: WatchFilter | None = None,
        debounce: int = 1_600,
        step: int = 50,
        stop_event: SupportsIsSet | None = None,
        rust_timeout: int = 5_000,
        yield_on_timeout: bool = False,
        debug: bool | None = None,
        raise_interrupt: bool = True,
        force_polling: bool | None = None,
        poll_delay_ms: int = 300,
        recursive: bool = True,
        ignore_permission_denied: bool | None = None,
    ) -> Iterable[WatchEventBatch]:
        return watch(
            *paths,
            watch_filter=watch_filter,
            debounce=debounce,
            step=step,
            stop_event=stop_event,
            yield_on_timeout=yield_on_timeout,
            raise_interrupt=raise_interrupt,
            debug=debug,
            rust_timeout=rust_timeout,
            force_polling=force_polling,
            poll_delay_ms=poll_delay_ms,
            recursive=recursive,
            ignore_permission_denied=ignore_permission_denied,
        )


watchfiles = cast(WatchfilesModule, install_stub_module("watchfiles", _WatchfilesModule))

__all__ = ["Change", "WatchFilter", "WatchfilesModule", "watch", "watchfiles"]
