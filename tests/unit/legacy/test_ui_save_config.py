import importlib
import sys
import types

import pytest


@pytest.mark.requires_ui
def test_save_config_to_toml(tmp_path, monkeypatch):
    """save_config_to_toml should persist configuration without Streamlit."""
    stub = types.SimpleNamespace(error=lambda msg: None)
    monkeypatch.setitem(sys.modules, "streamlit", stub)
    config_utils = importlib.import_module("autoresearch.config_utils")
    monkeypatch.chdir(tmp_path)
    assert config_utils.save_config_to_toml({"foo": "bar"}) is True
    assert (tmp_path / "autoresearch.toml").exists()
