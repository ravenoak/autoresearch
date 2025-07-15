from types import ModuleType
import sys
from pathlib import Path
import tomllib

# Provide dummy modules for optional dependencies before importing
fake_streamlit = ModuleType("streamlit")
fake_streamlit.set_page_config = lambda *a, **k: None
fake_streamlit.markdown = lambda *a, **k: None
fake_streamlit.error = lambda *a, **k: None
fake_streamlit.sidebar = ModuleType("sidebar")
sys.modules.setdefault("streamlit", fake_streamlit)
sys.modules.setdefault("networkx", ModuleType("networkx"))
fake_matplotlib = ModuleType("matplotlib")
fake_matplotlib.use = lambda *a, **k: None
sys.modules.setdefault("matplotlib", fake_matplotlib)
sys.modules.setdefault("matplotlib.pyplot", ModuleType("pyplot"))
sys.modules.setdefault("psutil", ModuleType("psutil"))

from autoresearch.config_utils import (  # noqa: E402
    save_config_to_toml,
    apply_preset,
)


def test_save_config_to_toml(tmp_path, monkeypatch):
    cfg = {"core_setting": "val", "storage": {"duckdb_path": "x.duckdb"}}
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    assert save_config_to_toml(cfg) is True
    data = tomllib.loads(Path(tmp_path / "autoresearch.toml").read_text())
    assert data["core"]["core_setting"] == "val"
    assert data["storage"]["duckdb"]["duckdb_path"] == "x.duckdb"


def test_apply_preset_names():
    names = ["Default", "Fast Mode", "Thorough Mode", "Chain of Thought", "OpenAI Mode"]
    for name in names:
        preset = apply_preset(name)
        assert isinstance(preset, dict)
    assert apply_preset("nonexistent") is None
