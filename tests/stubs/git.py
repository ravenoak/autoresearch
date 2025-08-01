"""Stub for the :mod:`git` module provided by GitPython."""

import sys
import types

if "git" not in sys.modules:
    sys.modules["git"] = types.SimpleNamespace(Repo=object)
