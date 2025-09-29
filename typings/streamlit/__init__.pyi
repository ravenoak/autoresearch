from __future__ import annotations

from collections.abc import Callable, MutableMapping, Sequence
from contextlib import AbstractContextManager
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class DeltaGenerator(Protocol):
    def markdown(self, body: str, *, unsafe_allow_html: bool = ...) -> None: ...

    def text_input(
        self,
        label: str,
        value: str | None = ...,
        *,
        key: str | None = ...,
        help: str | None = ...,
        placeholder: str | None = ...,
    ) -> str: ...

    def text_area(
        self,
        label: str,
        value: str | None = ...,
        *,
        key: str | None = ...,
        help: str | None = ...,
        placeholder: str | None = ...,
        height: int | None = ...,
    ) -> str: ...

    def selectbox(
        self,
        label: str,
        options: Sequence[Any],
        *,
        index: int | None = ...,
        key: str | None = ...,
        help: str | None = ...,
    ) -> Any: ...

    def multiselect(
        self,
        label: str,
        options: Sequence[Any],
        *,
        default: Sequence[Any] | None = ...,
        key: str | None = ...,
        help: str | None = ...,
    ) -> list[Any]: ...

    def slider(
        self,
        label: str,
        min_value: Any = ...,
        max_value: Any = ...,
        value: Any | None = ...,
        *,
        step: Any | None = ...,
        key: str | None = ...,
        help: str | None = ...,
    ) -> Any: ...

    def checkbox(
        self,
        label: str,
        value: bool | None = ...,
        *,
        key: str | None = ...,
        help: str | None = ...,
    ) -> bool: ...

    def radio(
        self,
        label: str,
        options: Sequence[Any],
        *,
        index: int | None = ...,
        key: str | None = ...,
        help: str | None = ...,
    ) -> Any: ...

    def button(
        self,
        label: str,
        *,
        key: str | None = ...,
        help: str | None = ...,
        use_container_width: bool | None = ...,
    ) -> bool: ...

    def download_button(
        self,
        label: str,
        data: Any,
        file_name: str | None = ...,
        *,
        mime: str | None = ...,
        key: str | None = ...,
    ) -> bool: ...

    def write(self, *args: Any, **kwargs: Any) -> None: ...

    def json(self, obj: Any, *, expanded: bool = ...) -> None: ...

    def table(self, data: Any) -> None: ...

    def dataframe(self, data: Any) -> None: ...

    def metric(self, label: str, value: Any, delta: Any | None = ..., *, delta_color: str | None = ...) -> None: ...

    def image(self, image: Any, *, caption: str | None = ..., use_column_width: bool | str | None = ...) -> None: ...

    def header(self, text: str) -> None: ...

    def subheader(self, text: str) -> None: ...

    def caption(self, text: str) -> None: ...

    def success(self, text: str) -> None: ...

    def warning(self, text: str) -> None: ...

    def error(self, text: str) -> None: ...

    def info(self, text: str) -> None: ...

    def form(self, key: str, *, clear_on_submit: bool = ...) -> Form: ...

    def form_submit_button(
        self,
        label: str = ...,
        *,
        use_container_width: bool | None = ...,
        type: str | None = ...,
    ) -> bool: ...

    def container(self) -> DeltaGenerator: ...

    def columns(
        self, spec: Sequence[int] | int, *, gap: str | None = ...
    ) -> Sequence[DeltaGenerator]: ...

    def expander(self, label: str, *, expanded: bool = ...) -> DeltaGenerator: ...

    def tabs(self, names: Sequence[str]) -> Sequence[DeltaGenerator]: ...

    def __getattr__(self, name: str) -> Callable[..., Any]: ...


class Form(Protocol):
    def __enter__(self) -> DeltaGenerator: ...

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any | None) -> bool | None: ...

    def form_submit_button(
        self,
        label: str = ...,
        *,
        use_container_width: bool | None = ...,
        type: str | None = ...,
    ) -> bool: ...


class StreamlitModule(Protocol):
    session_state: MutableMapping[str, Any]
    sidebar: DeltaGenerator

    def set_page_config(
        self,
        *,
        page_title: str | None = ...,
        page_icon: Any | None = ...,
        layout: str | None = ...,
        initial_sidebar_state: str | None = ...,
    ) -> None: ...

    def markdown(self, body: str, *, unsafe_allow_html: bool = ...) -> None: ...

    def rerun(self) -> None: ...

    def experimental_rerun(self) -> None: ...

    def spinner(self, text: str | None = None) -> AbstractContextManager[None]: ...

    def cache_data(
        self,
        func: Callable[..., T] | None = ...,
        *,
        ttl: float | None = ...,
        show_spinner: bool | None = ...,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

    def stop(self) -> None: ...

    def __getattr__(self, name: str) -> Callable[..., Any]: ...


st: StreamlitModule

__all__ = ["DeltaGenerator", "Form", "StreamlitModule", "st"]
