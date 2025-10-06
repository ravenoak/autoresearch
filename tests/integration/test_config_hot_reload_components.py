# mypy: ignore-errors
from pathlib import Path

from autoresearch.config.loader import ConfigLoader, get_config


def test_config_hot_reload_components(tmp_path: Path) -> None:
    cfg = tmp_path / "autoresearch.toml"
    cfg.write_text("""[core]\nloops = 1\n[api]\nrate_limit = 1\n""")
    with ConfigLoader.temporary_instance(search_paths=[cfg]) as loader:
        first = get_config()
        assert first.loops == 1
        assert first.api.rate_limit == 1

        cfg.write_text("""[core]\nloops = 2\n[api]\nrate_limit = 5\n""")
        loader._config = loader.load_config()
        updated = get_config()
        assert updated.loops == 2
        assert updated.api.rate_limit == 5
        assert ConfigLoader() is loader
