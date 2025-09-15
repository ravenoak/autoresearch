"""Project-wide customizations for Python startup."""

from typing import TYPE_CHECKING
import warnings

if not TYPE_CHECKING:  # pragma: no cover - runtime import
    import importlib
    import shlex
    import sys
    import types

    warnings.filterwarnings(
        "ignore",
        message=".*pkg_resources.*",
        category=DeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*split_arg_string.*",
        category=DeprecationWarning,
    )

    def _ensure_click_split_arg_string() -> None:
        """Provide a ``click.parser.split_arg_string`` compat shim."""

        try:
            importlib.import_module("click")
        except Exception:  # pragma: no cover - optional dependency
            return

        module_name = "click.parser"
        try:
            click_parser = importlib.import_module(module_name)
        except ModuleNotFoundError:
            click_parser = types.ModuleType(module_name)
            sys.modules[module_name] = click_parser

        if not hasattr(click_parser, "split_arg_string"):
            click_parser.split_arg_string = shlex.split

    try:
        _ensure_click_split_arg_string()
    except Exception:  # pragma: no cover - best effort
        pass

    try:
        import pydantic.root_model  # noqa: F401
    except Exception:  # pragma: no cover - best effort
        pass
