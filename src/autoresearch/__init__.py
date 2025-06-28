"""Autoresearch package initialization.

This package provides a local-first research assistant with multiple
interfaces and a modular architecture.
"""

from .distributed import RayExecutor

__all__ = ["RayExecutor"]
