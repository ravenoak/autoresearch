"""Project-wide customizations for Python startup."""

from typing import TYPE_CHECKING
import warnings

if not TYPE_CHECKING:  # pragma: no cover - runtime import
    import importlib
    import sys
    import types

    warnings.filterwarnings(
        "ignore",
        message=".*pkg_resources.*",
        category=DeprecationWarning,
    )

    def _ensure_click_split_arg_string() -> None:
        """Provide a ``click.parser.split_arg_string`` compat shim."""

        try:
            shell_completion = importlib.import_module("click.shell_completion")
        except Exception:  # pragma: no cover - optional dependency
            return

        split_arg_string = getattr(shell_completion, "split_arg_string", None)
        if split_arg_string is None:
            return

        module_name = "click.parser"
        try:
            click_parser = importlib.import_module(module_name)
        except ModuleNotFoundError:
            click_parser = types.ModuleType(module_name)
            sys.modules[module_name] = click_parser

        if "split_arg_string" not in click_parser.__dict__:
            click_parser.split_arg_string = split_arg_string

    try:
        _ensure_click_split_arg_string()
    except Exception:  # pragma: no cover - best effort
        pass

    try:
        import pydantic.root_model  # noqa: F401
    except Exception:  # pragma: no cover - best effort
        pass
