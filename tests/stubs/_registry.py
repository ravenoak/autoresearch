"""Utilities for installing typed stub modules used in the test suite."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Callable, Iterable, TypeVar, cast


T_Module = TypeVar("T_Module", bound=ModuleType)


def _ensure_parent_packages(name: str) -> Iterable[ModuleType]:
    """Ensure placeholder packages exist for dotted module names.

    ``import`` statements expect intermediate packages to be present in
    :data:`sys.modules`.  When generating stub modules dynamically we create
    ``ModuleType`` placeholders for each parent package so importing the final
    module succeeds without the real dependency installed.
    """

    parts = name.split(".")
    for index in range(1, len(parts)):
        parent_name = ".".join(parts[:index])
        parent = sys.modules.get(parent_name)
        if parent is None:
            parent = ModuleType(parent_name)
            sys.modules[parent_name] = parent
        if index < len(parts):
            child_attr = parts[index]
            if getattr(parent, child_attr, None) is None:
                setattr(parent, child_attr, None)
        yield parent


def install_stub_module(name: str, factory: Callable[[], T_Module]) -> T_Module:
    """Install a stub module under ``name`` if the real module is absent.

    Parameters
    ----------
    name:
        Fully qualified module name to register.
    factory:
        Zero-argument callable that creates a :class:`ModuleType` subclass with
        the desired stub behaviour.

    Returns
    -------
    ModuleType
        The module (either the existing real module or the newly created stub).
    """

    existing = sys.modules.get(name)
    if existing is not None:
        return cast(T_Module, existing)

    for _parent in _ensure_parent_packages(name):
        # Parent placeholders are created for side effects in ``sys.modules``.
        continue

    module = factory()
    sys.modules[name] = module

    if "." in name:
        parent_name, _, attribute = name.rpartition(".")
        parent = sys.modules.get(parent_name)
        if parent is not None:
            setattr(parent, attribute, module)

    return module
