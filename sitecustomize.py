"""Project-wide customizations for Python startup."""

from typing import TYPE_CHECKING

if not TYPE_CHECKING:  # pragma: no cover - runtime import
    try:
        import pydantic.root_model  # noqa: F401
    except Exception:  # pragma: no cover - best effort
        pass
