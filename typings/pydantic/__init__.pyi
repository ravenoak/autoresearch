from __future__ import annotations

from typing import Any, Callable, ClassVar, Generic, TypeVar, overload

_ModelT = TypeVar("_ModelT", bound="BaseModel")
_T = TypeVar("_T")


class ValidationError(Exception):
    def errors(self) -> list[dict[str, Any]]: ...


class BaseModel:
    model_config: ClassVar[Any]
    model_fields: ClassVar[dict[str, Any]]
    model_fields_set: set[str]

    def __init__(self, **data: Any) -> None: ...

    @classmethod
    def model_validate(
        cls: type[_ModelT], data: Any, *, strict: bool = ...
    ) -> _ModelT: ...

    def model_dump(
        self,
        *,
        mode: str = ...,
        by_alias: bool = ...,
        exclude_none: bool = ...,
        exclude_unset: bool = ...,
        exclude_defaults: bool = ...,
        include: Any = ...,
        exclude: Any = ...,
    ) -> dict[str, Any]: ...

    def model_dump_json(
        self,
        *,
        mode: str = ...,
        by_alias: bool = ...,
        exclude_none: bool = ...,
        exclude_unset: bool = ...,
        exclude_defaults: bool = ...,
        include: Any = ...,
        exclude: Any = ...,
    ) -> str: ...

    def model_post_init(self, __context: Any) -> None: ...


class PrivateAttr(Generic[_T]):
    def __init__(
        self,
        default: _T | None = ...,
        *,
        default_factory: Callable[[], _T] | None = ...,
    ) -> None: ...

    def __get__(self, instance: Any, owner: type[Any] | None = ...) -> _T: ...

    def __set__(self, instance: Any, value: _T) -> None: ...


ConfigDict = dict[str, Any]


def Field(
    default: Any = ...,
    *,
    default_factory: Callable[[], Any] | None = ...,
    alias: str | None = ...,
    description: str | None = ...,
    ge: float | None = ...,
    gt: float | None = ...,
    le: float | None = ...,
    lt: float | None = ...,
    min_length: int | None = ...,
    max_length: int | None = ...,
    pattern: str | None = ...,
    alias_priority: int | None = ...,
    frozen: bool | None = ...,
) -> Any: ...


def field_validator(
    *fields: str,
    mode: str | tuple[str, ...] | None = ...,
    check_fields: bool = ...,
) -> Callable[[Callable[..., _T]], Callable[..., _T]]: ...


__all__ = [
    "BaseModel",
    "ConfigDict",
    "Field",
    "PrivateAttr",
    "ValidationError",
    "field_validator",
]
