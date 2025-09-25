from __future__ import annotations

from typing import Any, Callable, ClassVar, Mapping, TypeVar

T_BaseModel = TypeVar("T_BaseModel", bound="BaseModel")
F = TypeVar("F", bound=Callable[..., Any])


class BaseModel:
    model_config: ClassVar[dict[str, Any]]
    model_fields: ClassVar[Mapping[str, Any]]
    model_fields_set: set[str]

    def __init__(self, /, **data: Any) -> None: ...

    @classmethod
    def model_validate(cls: type[T_BaseModel], obj: Any, /) -> T_BaseModel: ...

    @classmethod
    def model_validate_json(cls: type[T_BaseModel], json_data: str, /) -> T_BaseModel: ...

    def model_dump(
        self,
        *,
        mode: str | None = ...,
        by_alias: bool | None = ...,
        include: Any | None = ...,
        exclude: Any | None = ...,
        exclude_none: bool | None = ...,
        round_trip: bool | None = ...,
    ) -> dict[str, Any]: ...

    def model_dump_json(
        self,
        *,
        indent: int | None = ...,
        by_alias: bool | None = ...,
        include: Any | None = ...,
        exclude: Any | None = ...,
    ) -> str: ...

    def model_copy(
        self: T_BaseModel,
        *,
        update: Mapping[str, Any] | None = ...,
        deep: bool | None = ...,
    ) -> T_BaseModel: ...


class ValidationError(Exception):
    def errors(self) -> list[dict[str, Any]]: ...


def Field(*args: Any, **kwargs: Any) -> Any: ...


def PrivateAttr(*, default: Any = ..., default_factory: Callable[[], Any] | None = ...) -> Any: ...


def field_validator(*_fields: str, **_kwargs: Any) -> Callable[[F], F]: ...


def model_validator(*_fields: str, **_kwargs: Any) -> Callable[[F], F]: ...


ConfigDict = dict[str, Any]

__all__ = [
    "BaseModel",
    "ConfigDict",
    "Field",
    "PrivateAttr",
    "ValidationError",
    "field_validator",
    "model_validator",
]
