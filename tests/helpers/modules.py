"""Utilities for installing stub modules during tests."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
import sys
from types import ModuleType

__all__ = ["StubModule", "create_stub_module", "ensure_stub_module"]


class StubModule(ModuleType):
    """Module with dynamic attribute support for typing."""

    def __getattr__(self, name: str) -> object:  # pragma: no cover - dynamic fallback
        try:
            return self.__dict__[name]
        except KeyError as exc:  # pragma: no cover - match ModuleType semantics
            raise AttributeError(name) from exc


def create_stub_module(
    name: str,
    attributes: Mapping[str, object] | None = None,
) -> StubModule:
    """Create a :class:`ModuleType` populated with ``attributes``.

    Args:
        name: Fully qualified module name.
        attributes: Optional mapping of attribute names to values.

    Returns:
        A new module instance with the provided attributes.
    """

    module = StubModule(name)
    if attributes:
        for attr, value in attributes.items():
            setattr(module, attr, value)
    return module


def ensure_stub_module(
    name: str,
    attributes: Mapping[str, object] | None = None,
    modules: MutableMapping[str, ModuleType] | None = None,
) -> ModuleType:
    """Install a stub module into ``modules`` if it is missing.

    The helper mirrors :func:`dict.setdefault` semantics for ``sys.modules``
    while ensuring that a proper :class:`ModuleType` instance is registered.

    Args:
        name: Fully qualified module name.
        attributes: Optional attributes to set on the module. Attributes are only
            applied when missing to avoid clobbering real implementations.
        modules: Registry to update. Defaults to :data:`sys.modules`.

    Returns:
        The stub module registered under ``name``.
    """

    registry = modules if modules is not None else sys.modules
    module = registry.get(name)
    if not isinstance(module, ModuleType):
        module = create_stub_module(name)
        registry[name] = module
    if attributes:
        for attr, value in attributes.items():
            if not hasattr(module, attr):
                setattr(module, attr, value)
    parent_name, _, child_name = name.rpartition(".")
    if parent_name:
        parent = ensure_stub_module(parent_name, modules=registry)
        if getattr(parent, child_name, None) is not module:
            setattr(parent, child_name, module)
        if getattr(module, "__package__", None) != parent_name:
            module.__package__ = parent_name
    return module
