"""Typed stub for :mod:`streamlit`."""

from __future__ import annotations

import importlib.util
from types import ModuleType, SimpleNamespace
from typing import Any, Protocol, Sequence

from ._registry import install_stub_module


class SessionState(dict[str, Any]):
    __getattr__ = dict.get  # type: ignore[assignment]
    __setattr__ = dict.__setitem__  # type: ignore[assignment]


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

    def container(self) -> SimpleNamespace: ...

    def modal(self, *args: Any, **kwargs: Any) -> SimpleNamespace: ...


class _ContextManager(SimpleNamespace):
    def __enter__(self) -> None:  # pragma: no cover - trivial
        return None

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
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

    def container(self) -> SimpleNamespace:
        return _ContextManager()

    def modal(self, *args: Any, **kwargs: Any) -> SimpleNamespace:
        return _ContextManager()


if importlib.util.find_spec("streamlit") is None:
    streamlit: StreamlitModule = install_stub_module("streamlit", _StreamlitModule)
else:  # pragma: no cover
    import streamlit as streamlit  # type: ignore  # noqa: F401


__all__ = ["SessionState", "StreamlitModule", "streamlit"]
