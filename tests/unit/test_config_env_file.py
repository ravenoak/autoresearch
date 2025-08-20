from autoresearch.config.loader import ConfigLoader


def test_env_file_parsing(example_env_file):
    """ConfigLoader should populate ConfigModel from .env file."""
    env_path = example_env_file
    env_path.write_text("loops=5\nstorage__rdf_path=env.db\n")
    loader = ConfigLoader.new_for_tests(env_path=env_path)
    cfg = loader.load_config()
    assert cfg.loops == 5
    assert cfg.storage.rdf_path == "env.db"
