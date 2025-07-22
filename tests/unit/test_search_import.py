import builtins
import importlib
import sys

import pytest


def test_search_import_without_gitpython(monkeypatch):
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "git" or name.startswith("git."):
            raise ModuleNotFoundError("No module named 'git'")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "autoresearch.search", raising=False)
    with pytest.warns(UserWarning):
        module = importlib.import_module("autoresearch.search")
    assert not module.GITPYTHON_AVAILABLE


def test_search_import_with_gitpython():
    module = importlib.import_module("autoresearch.search")
    assert module.GITPYTHON_AVAILABLE
