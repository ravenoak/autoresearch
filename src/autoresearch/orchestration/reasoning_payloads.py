"""Normalization helpers for reasoning payloads used across orchestration."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping, Sequence
from typing import Any, Iterable as TypingIterable, Iterator, Protocol, SupportsIndex, Tuple, TypeAlias, overload

from pydantic_core import core_schema


class GetCoreSchemaHandler(Protocol):
    """Minimal protocol for ``pydantic`` schema handler callbacks."""

    def generate_schema(self, source: type[Any]) -> core_schema.CoreSchema: ...


class FrozenReasoningStep(Mapping[str, Any]):
    """Immutable, hashable view over a reasoning payload mapping."""

    __slots__ = ("_data", "_canonical", "_label", "_hash")

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._data: dict[str, Any] = {
            str(key): self._sanitize_value(value) for key, value in payload.items()
        }
        self._canonical: Tuple[tuple[str, Any], ...] = tuple(
            (key, self._canonicalize_value(value)) for key, value in sorted(self._data.items())
        )
        self._label = self._derive_label(self._data)
        self._hash = hash(self._label) if self._label else hash(self._canonical)

    @staticmethod
    def _sanitize_value(value: Any) -> Any:
        if isinstance(value, FrozenReasoningStep):
            return value
        if isinstance(value, Mapping):
            return FrozenReasoningStep(value)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return tuple(FrozenReasoningStep._sanitize_value(item) for item in value)
        return value

    @classmethod
    def _canonicalize_value(cls, value: Any) -> Any:
        if isinstance(value, FrozenReasoningStep):
            return value._canonical
        if isinstance(value, tuple):
            return tuple(cls._canonicalize_value(item) for item in value)
        if isinstance(value, Mapping):
            return tuple(
                (str(key), cls._canonicalize_value(val))
                for key, val in sorted(value.items(), key=lambda item: str(item[0]))
            )
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return tuple(cls._canonicalize_value(item) for item in value)
        return value

    @staticmethod
    def _derive_label(data: Mapping[str, Any]) -> str | None:
        priority_keys = (
            "text",
            "content",
            "claim",
            "summary",
            "label",
            "id",
        )
        for key in priority_keys:
            candidate = data.get(key)
            if isinstance(candidate, str):
                if key in {"text", "content"}:
                    if candidate:
                        return candidate
                elif candidate.strip():
                    return candidate.strip()
        return None

    def __getitem__(self, key: str) -> Any:
        value = self._data[key]
        return self._export_value(value)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FrozenReasoningStep):
            return self._canonical == other._canonical
        if isinstance(other, Mapping):
            try:
                return self._canonical == FrozenReasoningStep(other)._canonical
            except Exception:  # pragma: no cover - defensive guard
                return False
        if isinstance(other, str):
            return (self._label or "") == other
        return False

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        label = f" label={self._label!r}" if self._label else ""
        return f"FrozenReasoningStep({dict(self.items())!r}{label})"

    def __str__(self) -> str:
        return self._label or repr(dict(self.items()))

    @staticmethod
    def _export_value(value: Any) -> Any:
        if isinstance(value, FrozenReasoningStep):
            return value.to_dict()
        if isinstance(value, tuple):
            return [FrozenReasoningStep._export_value(item) for item in value]
        return value

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable copy of the payload."""

        return {key: self._export_value(value) for key, value in self._data.items()}

    @property
    def sort_key(self) -> str:
        return self._label or repr(self._canonical)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type["FrozenReasoningStep"], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        base_schema = handler.generate_schema(dict[str, Any])
        return core_schema.no_info_wrap_validator_function(cls._validate, base_schema)

    @classmethod
    def _validate(
        cls, value: Any, _handler: core_schema.ValidatorFunctionWrapHandler
    ) -> "FrozenReasoningStep":
        if isinstance(value, FrozenReasoningStep):
            return value
        if isinstance(value, Mapping):
            return cls(value)
        if isinstance(value, str):
            return cls({"text": value})
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            items = [cls._sanitize_value(v) for v in value]
            return cls({"items": [cls._export_value(item) for item in items]})
        return cls({"value": value})


NormalizedReasoning: TypeAlias = Mapping[str, Any]


class ReasoningCollection(list[FrozenReasoningStep]):
    """Mutable sequence that normalises reasoning payloads on mutation."""

    __slots__ = ()

    def __init__(self, values: Iterable[Any] | None = None) -> None:
        super().__init__()
        if values:
            self.extend(values)

    @staticmethod
    def _coerce(value: Any) -> FrozenReasoningStep:
        return normalize_reasoning_step(value)

    def append(self, value: Any) -> None:
        super().append(self._coerce(value))

    def extend(self, values: Iterable[Any]) -> None:
        if isinstance(values, (str, bytes, bytearray)):
            super().extend([self._coerce(values)])
            return
        super().extend(self._coerce(value) for value in values)

    def insert(self, index: SupportsIndex, value: Any) -> None:
        super().insert(index, self._coerce(value))

    @overload
    def __setitem__(self, index: SupportsIndex, value: Any) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: TypingIterable[Any]) -> None: ...

    def __setitem__(self, index: SupportsIndex | slice, value: Any) -> None:
        if isinstance(index, slice):
            if isinstance(value, (str, bytes, bytearray)):
                raise TypeError("slice assignment requires an iterable of reasoning payloads")
            normalized = [self._coerce(item) for item in value]
            super().__setitem__(index, normalized)
            return
        super().__setitem__(index, self._coerce(value))

    def copy(self) -> "ReasoningCollection":
        return ReasoningCollection(self)

    @classmethod
    def _validate(
        cls, value: Any, _handler: core_schema.ValidatorFunctionWrapHandler
    ) -> "ReasoningCollection":
        if isinstance(value, cls):
            return value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return cls(value)
        if isinstance(value, FrozenReasoningStep):
            return cls([value])
        raise TypeError("ReasoningCollection requires a sequence of reasoning payloads")

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type["ReasoningCollection"], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        base_schema = handler.generate_schema(list[FrozenReasoningStep])
        return core_schema.no_info_wrap_validator_function(cls._validate, base_schema)


def normalize_reasoning_step(step: Any) -> FrozenReasoningStep:
    """Return a hashable reasoning step representation."""

    if isinstance(step, FrozenReasoningStep):
        return step
    if isinstance(step, Mapping):
        return FrozenReasoningStep(step)
    if isinstance(step, str):
        return FrozenReasoningStep({"text": step})
    if isinstance(step, Sequence) and not isinstance(step, (str, bytes)):
        items = [normalize_reasoning_step(item).to_dict() for item in step]
        return FrozenReasoningStep({"items": items})
    if isinstance(step, Hashable):
        return FrozenReasoningStep({"value": step})
    return FrozenReasoningStep({"value": repr(step)})


def normalize_reasoning_sequence(steps: Sequence[Any]) -> list[FrozenReasoningStep]:
    """Normalise all reasoning steps within ``steps``."""

    return [normalize_reasoning_step(step) for step in steps]


def stabilize_reasoning_order(steps: Sequence[Any]) -> list[FrozenReasoningStep]:
    """Return reasoning steps sorted by their semantic label."""

    normalized = normalize_reasoning_sequence(steps)
    return sorted(normalized, key=_sort_key)


def _sort_key(step: NormalizedReasoning) -> str:
    if isinstance(step, FrozenReasoningStep):
        return step.sort_key
    return FrozenReasoningStep(step).sort_key
