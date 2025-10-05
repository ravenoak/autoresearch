"""Normalization helpers for reasoning payloads used across orchestration."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from typing import Any, Iterator, Tuple, TypeAlias

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


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

    def items(self) -> Iterator[tuple[str, Any]]:  # pragma: no cover - simple proxy
        for key in self._data:
            yield key, self._export_value(self._data[key])

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


NormalizedReasoning: TypeAlias = FrozenReasoningStep | tuple[Any, ...] | str


def normalize_reasoning_step(step: Any) -> NormalizedReasoning:
    """Return a hashable reasoning step representation."""

    if isinstance(step, FrozenReasoningStep):
        return step
    if isinstance(step, Mapping):
        return FrozenReasoningStep(step)
    if isinstance(step, str):
        return FrozenReasoningStep({"text": step})
    if isinstance(step, Sequence) and not isinstance(step, (str, bytes)):
        return tuple(normalize_reasoning_step(item) for item in step)
    if isinstance(step, Hashable):
        return FrozenReasoningStep({"value": step})
    return FrozenReasoningStep({"value": repr(step)})


def normalize_reasoning_sequence(steps: Sequence[Any]) -> list[NormalizedReasoning]:
    """Normalise all reasoning steps within ``steps``."""

    return [normalize_reasoning_step(step) for step in steps]


def stabilize_reasoning_order(steps: Sequence[Any]) -> list[NormalizedReasoning]:
    """Return reasoning steps sorted by their semantic label."""

    normalized = normalize_reasoning_sequence(steps)
    return sorted(normalized, key=_sort_key)


def _sort_key(step: NormalizedReasoning) -> str:
    if isinstance(step, FrozenReasoningStep):
        return step.sort_key
    if isinstance(step, tuple):
        return "|".join(_sort_key(item) for item in step)
    return str(step)
