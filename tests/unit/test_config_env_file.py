from autoresearch.config.loader import ConfigLoader


def test_env_file_parsing(tmp_path):
    """ConfigLoader should populate ConfigModel from .env file."""
    env_path = tmp_path / ".env"
    env_path.write_text("\n".join(["loops=5", "storage__rdf_path=env.db"]))
    loader = ConfigLoader.new_for_tests(env_path=env_path)
    cfg = loader.load_config()
    assert cfg.loops == 5
    assert cfg.storage.rdf_path == "env.db"
