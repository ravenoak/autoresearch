"""Project-wide customizations for Python startup."""

from typing import TYPE_CHECKING
import warnings

if not TYPE_CHECKING:  # pragma: no cover - runtime import
    warnings.filterwarnings(
        "ignore",
        message=".*pkg_resources.*",
        category=DeprecationWarning,
    )
    try:
        import pydantic.root_model  # noqa: F401
    except Exception:  # pragma: no cover - best effort
        pass
