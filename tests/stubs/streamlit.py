"""Typed stub for :mod:`streamlit`."""

from __future__ import annotations

import importlib.util
from types import ModuleType, SimpleNamespace, TracebackType
from typing import Any, ContextManager, Protocol, Sequence, cast

from ._registry import install_stub_module


class SessionState(dict[str, Any]):
    def __getattr__(self, name: str) -> Any:
        return self.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class StreamlitModule(Protocol):
    __version__: str
    session_state: SessionState

    def markdown(self, *args: Any, **kwargs: Any) -> None: ...

    def set_page_config(self, *args: Any, **kwargs: Any) -> None: ...

    def text_area(self, *args: Any, **kwargs: Any) -> str: ...

    def selectbox(self, *args: Any, **kwargs: Any) -> Any: ...

    def slider(self, *args: Any, **kwargs: Any) -> Any: ...

    def button(self, *args: Any, **kwargs: Any) -> bool: ...

    def columns(self, *args: Any, **kwargs: Any) -> Sequence[SimpleNamespace]: ...

    def container(self) -> ContextManager[SimpleNamespace]: ...

    def modal(self, *args: Any, **kwargs: Any) -> ContextManager[SimpleNamespace]: ...


class _ContextManager(SimpleNamespace):
    def __enter__(self) -> SimpleNamespace:  # pragma: no cover - trivial
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:  # pragma: no cover - trivial
        return None


class _StreamlitModule(ModuleType):
    __version__ = "0.0"

    def __init__(self) -> None:
        super().__init__("streamlit")
        self.session_state = SessionState()
        self.__spec__ = importlib.util.spec_from_loader("streamlit", loader=None)

    def markdown(self, *args: Any, **kwargs: Any) -> None:
        return None

    def set_page_config(self, *args: Any, **kwargs: Any) -> None:
        return None

    def text_area(self, *args: Any, **kwargs: Any) -> str:
        return ""

    def selectbox(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def slider(self, *args: Any, **kwargs: Any) -> Any:
        return 0

    def button(self, *args: Any, **kwargs: Any) -> bool:
        return False

    def columns(self, *args: Any, **kwargs: Any) -> Sequence[SimpleNamespace]:
        return (SimpleNamespace(), SimpleNamespace())

    def container(self) -> ContextManager[SimpleNamespace]:
        return _ContextManager()

    def modal(self, *args: Any, **kwargs: Any) -> ContextManager[SimpleNamespace]:
        return _ContextManager()


if importlib.util.find_spec("streamlit") is None:
    streamlit: StreamlitModule = install_stub_module("streamlit", _StreamlitModule)
else:  # pragma: no cover
    import streamlit as _streamlit  # noqa: F401

    streamlit = cast(StreamlitModule, _streamlit)


__all__ = ["SessionState", "StreamlitModule", "streamlit"]
