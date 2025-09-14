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
    try:
        import importlib.util, sys, types
        from pathlib import Path

        spec = importlib.util.find_spec("weasel.util.config")
        if spec and spec.origin:
            src = Path(spec.origin).read_text()
            # Replace deprecated Click API with ``shlex.split`` to silence
            # deprecation warnings from the ``weasel`` dependency.
            src = src.replace(
                "from click.parser import split_arg_string",
                "import shlex\n\nsplit_arg_string = shlex.split",
            )
            src = src.replace("click.parser.split_arg_string", "shlex.split")
            module = types.ModuleType("weasel.util.config")
            exec(compile(src, spec.origin, "exec"), module.__dict__)
            sys.modules["weasel.util.config"] = module
    except Exception:  # pragma: no cover - best effort
        pass
