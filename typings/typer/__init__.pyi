from __future__ import annotations

from typing import Any, Callable, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


class Exit(SystemExit):
    def __init__(self, code: int | None = ...) -> None: ...


class BadParameter(Exception): ...


class Context:
    obj: Any

    def __init__(self, app: Typer | None = ..., **kwargs: Any) -> None: ...


class Typer:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[P, T]], Callable[P, T]]: ...

    def callback(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[P, T]], Callable[P, T]]: ...

    def add_typer(self, app: Typer, *args: Any, **kwargs: Any) -> None: ...


def Option(*args: Any, **kwargs: Any) -> Any: ...

def Argument(*args: Any, **kwargs: Any) -> Any: ...

def echo(message: object = ..., *, err: bool = ...) -> None: ...

def secho(
    message: object = ..., *, fg: Optional[str] = ..., err: bool = ..., bold: bool = ...
) -> None: ...

def confirm(text: str, *args: Any, **kwargs: Any) -> bool: ...

def prompt(text: str, *args: Any, **kwargs: Any) -> str: ...

def launch(app: Typer, *args: Any, **kwargs: Any) -> None: ...
