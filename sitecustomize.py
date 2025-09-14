"""Project-wide customizations for Python startup."""

from typing import TYPE_CHECKING
import warnings

if not TYPE_CHECKING:  # pragma: no cover - runtime import
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
    try:
        import pydantic.root_model  # noqa: F401
    except Exception:  # pragma: no cover - best effort
        pass
    try:
        import shlex

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*split_arg_string.*",
                category=DeprecationWarning,
            )
            import weasel.util.config as weasel_config
            import spacy.cli._util as spacy_cli_util

        # Replace deprecated Click API with ``shlex.split`` to silence
        # deprecation warnings from transitive dependencies.
        weasel_config.split_arg_string = shlex.split
        spacy_cli_util.split_arg_string = shlex.split
    except Exception:  # pragma: no cover - best effort
        pass
