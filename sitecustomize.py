"""Project-wide customizations for Python startup."""

from typing import TYPE_CHECKING
import warnings

_WEASEL_CONFIG_PATCH_INSTALLED = False

if not TYPE_CHECKING:  # pragma: no cover - runtime import
    import contextlib
    import importlib
    import importlib.abc
    import importlib.machinery
    import importlib.util
    import sys
    import types

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

    def _install_weasel_config_patch() -> None:
        """Ensure ``weasel.util.config`` imports Click helpers without warnings."""

        global _WEASEL_CONFIG_PATCH_INSTALLED

        if _WEASEL_CONFIG_PATCH_INSTALLED:
            return

        target_module = "weasel.util.config"

        class _WeaselConfigLoader(importlib.abc.Loader):
            """Delegate loader that patches deprecated Click imports."""

            def __init__(self, delegate: importlib.abc.Loader, origin: str | None) -> None:
                self._delegate = delegate
                self._origin = origin

            def create_module(self, spec):  # type: ignore[override]
                create = getattr(self._delegate, "create_module", None)
                if create is None:
                    return None
                return create(spec)

            def exec_module(self, module) -> None:  # type: ignore[override]
                get_source = getattr(self._delegate, "get_source", None)
                if get_source is None:
                    self._delegate.exec_module(module)
                    return

                source = get_source(module.__name__)
                if not source:
                    self._delegate.exec_module(module)
                    return

                sentinel = "from click.parser import split_arg_string"
                if sentinel not in source:
                    self._delegate.exec_module(module)
                    return

                replacement = (
                    "try:\n"
                    "    from click.shell_completion import split_arg_string\n"
                    "except ImportError:  # pragma: no cover - fallback for older Click\n"
                    "    from click.parser import split_arg_string\n"
                )
                patched_source = source.replace(sentinel, replacement)

                get_filename = getattr(self._delegate, "get_filename", None)
                filename = None
                if get_filename is not None:
                    with contextlib.suppress(Exception):
                        filename = get_filename(module.__name__)
                if not filename:
                    filename = getattr(module.__spec__, "origin", None)

                module.__loader__ = self
                module.__file__ = filename
                exec(compile(patched_source, filename or module.__name__, "exec"), module.__dict__)

        class _WeaselConfigFinder(importlib.abc.MetaPathFinder):
            """Finder that injects the patched loader."""

            def find_spec(self, fullname, path=None, target=None):  # type: ignore[override]
                if fullname != target_module:
                    return None

                spec = importlib.machinery.PathFinder.find_spec(fullname, path)
                if spec is None or spec.loader is None:
                    return None

                spec.loader = _WeaselConfigLoader(spec.loader, spec.origin)
                return spec

        sys.meta_path.insert(0, _WeaselConfigFinder())
        _WEASEL_CONFIG_PATCH_INSTALLED = True

        existing = sys.modules.pop(target_module, None)
        if existing is not None:
            with contextlib.suppress(Exception):
                importlib.import_module(target_module)

    try:
        _ensure_click_split_arg_string()
    except Exception:  # pragma: no cover - best effort
        pass

    try:
        _install_weasel_config_patch()
    except Exception:  # pragma: no cover - best effort
        pass

    try:
        import pydantic.root_model  # noqa: F401
    except Exception:  # pragma: no cover - best effort
        pass
