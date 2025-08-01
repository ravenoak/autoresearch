"""Stub for the :mod:`git` module provided by GitPython."""

import sys
import types

if "git" not in sys.modules:
    git_stub = types.SimpleNamespace(Repo=object)
    sys.modules["git"] = git_stub
