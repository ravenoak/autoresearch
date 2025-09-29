from __future__ import annotations

from collections.abc import Callable, Sequence, Iterator
from contextlib import AbstractContextManager
from typing import Any, Protocol, TypeVar, NoReturn

T = TypeVar("T")


class SessionState(Protocol):
    def __getitem__(self, key: str) -> Any: ...

    def __setitem__(self, key: str, value: Any) -> None: ...

    def __delitem__(self, key: str) -> None: ...

    def __iter__(self) -> Iterator[str]: ...

    def __len__(self) -> int: ...

    def get(self, key: str, default: Any = ...) -> Any: ...

    def setdefault(self, key: str, default: Any) -> Any: ...

    def __getattr__(self, name: str) -> Any: ...

    def __setattr__(self, name: str, value: Any) -> None: ...


class ProgressBar(Protocol):
    def progress(
        self, value: float | int | Sequence[float] | None = ..., *, text: str | None = ...
    ) -> None: ...

    def empty(self) -> None: ...


class DeltaGenerator(Protocol):
    def __enter__(self) -> DeltaGenerator: ...

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any | None
    ) -> bool | None: ...

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
        **kwargs: Any,
    ) -> Any: ...

    def checkbox(
        self,
        label: str,
        value: bool | None = ...,
        *,
        key: str | None = ...,
        help: str | None = ...,
        disabled: bool | None = ...,
        **kwargs: Any,
    ) -> bool: ...

    def radio(
        self,
        label: str,
        options: Sequence[Any],
        *,
        index: int | None = ...,
        key: str | None = ...,
        help: str | None = ...,
        format_func: Callable[[Any], Any] | None = ...,
        horizontal: bool | None = ...,
        **kwargs: Any,
    ) -> Any: ...

    def button(
        self,
        label: str,
        *,
        key: str | None = ...,
        help: str | None = ...,
        use_container_width: bool | None = ...,
        **kwargs: Any,
    ) -> bool: ...

    def download_button(
        self,
        label: str,
        data: Any,
        file_name: str | None = ...,
        *,
        mime: str | None = ...,
        key: str | None = ...,
        **kwargs: Any,
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
        help: str | None = ...,
        **kwargs: Any,
    ) -> bool: ...

    def container(self) -> DeltaGenerator: ...

    def columns(
        self, spec: Sequence[int] | int, *, gap: str | None = ...
    ) -> Sequence[DeltaGenerator]: ...

    def expander(self, label: str, *, expanded: bool = ...) -> DeltaGenerator: ...

    def tabs(self, names: Sequence[str]) -> Sequence[DeltaGenerator]: ...

    def graphviz_chart(self, chart: Any, *, use_container_width: bool | None = ...) -> None: ...

    def altair_chart(self, chart: Any, *, use_container_width: bool | None = ...) -> None: ...

    def progress(
        self, value: float | int | Sequence[float] | None = ..., *, text: str | None = ...
    ) -> ProgressBar: ...

    def empty(self) -> DeltaGenerator: ...

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
        help: str | None = ...,
        **kwargs: Any,
    ) -> bool: ...


session_state: SessionState
sidebar: DeltaGenerator


def set_page_config(
    *,
    page_title: str | None = ...,
    page_icon: Any | None = ...,
    layout: str | None = ...,
    initial_sidebar_state: str | None = ...,
) -> None: ...


def markdown(body: str, *, unsafe_allow_html: bool = ...) -> None: ...


def write(*args: Any, **kwargs: Any) -> None: ...


def json(obj: Any, *, expanded: bool = ...) -> None: ...


def table(data: Any) -> None: ...


def dataframe(data: Any, *, use_container_width: bool | None = ...) -> None: ...


def metric(label: str, value: Any, delta: Any | None = ..., *, delta_color: str | None = ...) -> None: ...


def image(
    image: Any,
    *,
    caption: str | None = ...,
    use_column_width: bool | str | None = ...,
) -> None: ...


def header(text: str) -> None: ...


def subheader(text: str) -> None: ...


def caption(text: str) -> None: ...


def success(text: str) -> None: ...


def warning(text: str) -> None: ...


def error(text: str) -> None: ...


def info(text: str) -> None: ...


def text_input(
    label: str,
    value: str | None = ...,
    *,
    key: str | None = ...,
    help: str | None = ...,
    placeholder: str | None = ...,
) -> str: ...


def text_area(
    label: str,
    value: str | None = ...,
    *,
    key: str | None = ...,
    help: str | None = ...,
    placeholder: str | None = ...,
    height: int | None = ...,
) -> str: ...


def selectbox(
    label: str,
    options: Sequence[Any],
    *,
    index: int | None = ...,
    key: str | None = ...,
    help: str | None = ...,
) -> Any: ...


def multiselect(
    label: str,
    options: Sequence[Any],
    *,
    default: Sequence[Any] | None = ...,
    key: str | None = ...,
    help: str | None = ...,
) -> list[Any]: ...


def slider(
    label: str,
    min_value: Any = ...,
    max_value: Any = ...,
    value: Any | None = ...,
    *,
    step: Any | None = ...,
    key: str | None = ...,
    help: str | None = ...,
    **kwargs: Any,
) -> Any: ...


def checkbox(
    label: str,
    value: bool | None = ...,
    *,
    key: str | None = ...,
    help: str | None = ...,
    disabled: bool | None = ...,
    **kwargs: Any,
) -> bool: ...


def radio(
    label: str,
    options: Sequence[Any],
    *,
    index: int | None = ...,
    key: str | None = ...,
    help: str | None = ...,
    format_func: Callable[[Any], Any] | None = ...,
    horizontal: bool | None = ...,
    **kwargs: Any,
) -> Any: ...


def number_input(
    label: str,
    value: float | int = ...,
    *,
    min_value: float | int | None = ...,
    max_value: float | int | None = ...,
    step: float | int | None = ...,
    key: str | None = ...,
    help: str | None = ...,
    format: str | None = ...,
    **kwargs: Any,
) -> float | int: ...


def button(
    label: str,
    *,
    key: str | None = ...,
    help: str | None = ...,
    use_container_width: bool | None = ...,
    **kwargs: Any,
) -> bool: ...


def download_button(
    label: str,
    data: Any,
    file_name: str | None = ...,
    *,
    mime: str | None = ...,
    key: str | None = ...,
    **kwargs: Any,
) -> bool: ...


def form(
    key: str,
    *,
    clear_on_submit: bool = ...,
) -> Form: ...


def form_submit_button(
    label: str = ...,
    *,
    use_container_width: bool | None = ...,
    type: str | None = ...,
    help: str | None = ...,
    **kwargs: Any,
) -> bool: ...


def container() -> DeltaGenerator: ...


def columns(spec: Sequence[int] | int, *, gap: str | None = ...) -> Sequence[DeltaGenerator]: ...


def expander(label: str, *, expanded: bool = ...) -> DeltaGenerator: ...


def tabs(names: Sequence[str]) -> Sequence[DeltaGenerator]: ...


def graphviz_chart(chart: Any, *, use_container_width: bool | None = ...) -> None: ...


def altair_chart(chart: Any, *, use_container_width: bool | None = ...) -> None: ...


def line_chart(data: Any, *, use_container_width: bool | None = ...) -> None: ...


def progress(
    value: float | int | Sequence[float] | None = ..., *, text: str | None = ...
) -> ProgressBar: ...


def spinner(text: str | None = None) -> AbstractContextManager[None]: ...


def cache_data(
    func: Callable[..., T] | None = ..., *, ttl: float | None = ..., show_spinner: bool | None = ...
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...


def stop() -> NoReturn: ...


def rerun() -> NoReturn: ...


def experimental_rerun() -> NoReturn: ...


def modal(title: str, *args: Any, **kwargs: Any) -> AbstractContextManager[None]: ...


__all__ = [
    "DeltaGenerator",
    "Form",
    "SessionState",
    "ProgressBar",
    "session_state",
    "sidebar",
    "set_page_config",
    "markdown",
    "write",
    "json",
    "table",
    "dataframe",
    "metric",
    "image",
    "header",
    "subheader",
    "caption",
    "success",
    "warning",
    "error",
    "info",
    "text_input",
    "text_area",
    "selectbox",
    "multiselect",
    "slider",
    "checkbox",
    "radio",
    "number_input",
    "button",
    "download_button",
    "form",
    "form_submit_button",
    "container",
    "columns",
    "expander",
    "tabs",
    "graphviz_chart",
    "altair_chart",
    "line_chart",
    "progress",
    "spinner",
    "cache_data",
    "stop",
    "rerun",
    "experimental_rerun",
    "modal",
]
