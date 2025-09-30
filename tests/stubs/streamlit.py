"""Typed stub for :mod:`streamlit`."""

from __future__ import annotations

import importlib.util
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from types import ModuleType, TracebackType
from typing import Literal, Protocol, TypeVar, cast

from ._registry import install_stub_module


class SessionState(dict[str, object]):
    """Mapping-like session store used by the stub."""

    def __getattr__(self, name: str) -> object:
        return self.get(name)

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


class ContainerContext(Protocol):
    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None: ...

    def write(self, value: object) -> None: ...


class ColumnContext(ContainerContext, Protocol):
    pass


class ModalContext(ContainerContext, Protocol):
    pass


TContext = TypeVar("TContext", bound=ContainerContext)


class _ContextManager(AbstractContextManager[TContext]):
    def __init__(self, value: TContext) -> None:
        self._value = value

    def __enter__(self) -> TContext:  # pragma: no cover - trivial
        return self._value

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:  # pragma: no cover - trivial
        return None


class _BaseContext:
    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        del body, unsafe_allow_html

    def write(self, value: object) -> None:
        del value


class _ColumnContext(_BaseContext):
    pass


class _ContainerContext(_BaseContext):
    pass


class _ModalContext(_BaseContext):
    pass


OptionT = TypeVar("OptionT")
NumberT = TypeVar("NumberT", int, float)


class StreamlitModule(Protocol):
    __version__: str
    session_state: SessionState

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None: ...

    def set_page_config(
        self,
        page_title: str | None = None,
        *,
        page_icon: str | None = None,
        layout: Literal["centered", "wide"] = "centered",
        initial_sidebar_state: Literal["auto", "expanded", "collapsed"] | None = None,
    ) -> None: ...

    def text_area(
        self,
        label: str,
        value: str = "",
        *,
        height: int | None = None,
        placeholder: str | None = None,
    ) -> str: ...

    def selectbox(
        self,
        label: str,
        options: Sequence[OptionT],
        *,
        index: int = 0,
        format_func: Callable[[OptionT], str] | None = None,
    ) -> OptionT: ...

    def slider(
        self,
        label: str,
        min_value: NumberT,
        max_value: NumberT,
        value: NumberT | tuple[NumberT, NumberT] | None = None,
        *,
        step: NumberT | None = None,
    ) -> NumberT | tuple[NumberT, NumberT]: ...

    def button(
        self,
        label: str,
        *,
        help: str | None = None,
        disabled: bool = False,
    ) -> bool: ...

    def write(self, value: object) -> None: ...

    def columns(
        self,
        spec: int | Sequence[float],
        *,
        gap: Literal["small", "medium", "large"] = "small",
    ) -> Sequence[ColumnContext]: ...

    def container(self) -> AbstractContextManager[ContainerContext]: ...

    def modal(self, title: str, *, closable: bool = True) -> AbstractContextManager[ModalContext]: ...


class _StreamlitModule(ModuleType):
    __version__ = "0.0"

    def __init__(self) -> None:
        super().__init__("streamlit")
        self.session_state = SessionState()
        self.__spec__ = importlib.util.spec_from_loader("streamlit", loader=None)

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        del body, unsafe_allow_html

    def set_page_config(
        self,
        page_title: str | None = None,
        *,
        page_icon: str | None = None,
        layout: Literal["centered", "wide"] = "centered",
        initial_sidebar_state: Literal["auto", "expanded", "collapsed"] | None = None,
    ) -> None:
        del page_title, page_icon, layout, initial_sidebar_state

    def text_area(
        self,
        label: str,
        value: str = "",
        *,
        height: int | None = None,
        placeholder: str | None = None,
    ) -> str:
        del label, height, placeholder
        return value

    def selectbox(
        self,
        label: str,
        options: Sequence[OptionT],
        *,
        index: int = 0,
        format_func: Callable[[OptionT], str] | None = None,
    ) -> OptionT:
        del label, format_func
        if not options:
            raise ValueError("options must not be empty")
        if index < 0 or index >= len(options):
            return options[0]
        return options[index]

    def slider(
        self,
        label: str,
        min_value: NumberT,
        max_value: NumberT,
        value: NumberT | tuple[NumberT, NumberT] | None = None,
        *,
        step: NumberT | None = None,
    ) -> NumberT | tuple[NumberT, NumberT]:
        del label, step, max_value
        if value is not None:
            return value
        return min_value

    def button(
        self,
        label: str,
        *,
        help: str | None = None,
        disabled: bool = False,
    ) -> bool:
        del label, help, disabled
        return False

    def write(self, value: object) -> None:
        del value

    def columns(
        self,
        spec: int | Sequence[float],
        *,
        gap: Literal["small", "medium", "large"] = "small",
    ) -> Sequence[ColumnContext]:
        del spec, gap
        return (_ColumnContext(), _ColumnContext())

    def container(self) -> AbstractContextManager[ContainerContext]:
        return _ContextManager(_ContainerContext())

    def modal(self, title: str, *, closable: bool = True) -> AbstractContextManager[ModalContext]:
        del title, closable
        return _ContextManager(_ModalContext())


if importlib.util.find_spec("streamlit") is None:
    streamlit: StreamlitModule = install_stub_module("streamlit", _StreamlitModule)
else:  # pragma: no cover
    import streamlit as _streamlit  # noqa: F401

    streamlit = cast(StreamlitModule, _streamlit)


__all__ = [
    "ColumnContext",
    "ContainerContext",
    "ModalContext",
    "SessionState",
    "StreamlitModule",
    "streamlit",
]
