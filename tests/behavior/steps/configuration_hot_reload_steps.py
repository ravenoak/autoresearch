# flake8: noqa
import os
from pytest_bdd import scenario, when, then, parsers

from . import common_steps  # noqa: F401


from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader


@when(
    parsers.parse('I modify "{file}" to enable a new agent'),
    target_fixture="modify_config_enable_agent",
)
def modify_config_enable_agent(file, tmp_path):
    ConfigLoader.reset_instance()
    loader = ConfigLoader()
    reloaded: list[ConfigModel] = []

    def _observer(cfg: ConfigModel) -> None:
        reloaded.append(cfg)

    cfg = {
        "core": {"backend": "lmstudio", "loops": 1, "ram_budget_mb": 512},
        "agent": {"NewAgent": {"enabled": True}},
    }
    import tomli_w

    with loader.watching(_observer):
        with open(file, "w") as f:
            f.write(tomli_w.dumps(cfg))

        new_cfg = loader.load_config()

    return new_cfg


@then(
    "the orchestrator should reload the configuration automatically",
    target_fixture="check_hot_reload",
)
def check_hot_reload(modify_config_enable_agent: ConfigModel):
    new_cfg = modify_config_enable_agent
    assert "NewAgent" in new_cfg.agents
    return new_cfg


@then("the new agent should be visible in the next iteration cycle")
def check_agent_visible(check_hot_reload: ConfigModel):
    assert "NewAgent" in check_hot_reload.agents


@when(
    parsers.parse('I modify "{file}" with invalid content'),
    target_fixture="modify_config_invalid",
)
def modify_config_invalid(file, tmp_path):
    ConfigLoader.reset_instance()
    loader = ConfigLoader()
    cfg_before = loader.load_config()
    with open(file, "w") as f:
        f.write("invalid = [this is not valid toml]")
    try:
        loader.load_config()
    except Exception:
        pass
    return cfg_before


@then("the orchestrator should keep the previous configuration")
def config_unchanged(modify_config_invalid: ConfigModel):
    cfg_after = ConfigLoader().load_config()
    assert cfg_after == modify_config_invalid


@when(
    parsers.parse('I modify "{file}" to set loops to {count:d}'),
    target_fixture="modify_config_loops",
)
def modify_config_loops(file, count, tmp_path):
    """Change loop count in the configuration file and trigger reload."""
    ConfigLoader.reset_instance()
    loader = ConfigLoader()
    cfg = {"core": {"backend": "lmstudio", "loops": count}}
    import tomli_w

    with loader.watching(lambda cfg: None):
        with open(file, "w") as f:
            f.write(tomli_w.dumps(cfg))
        new_cfg = loader.load_config()
    return new_cfg


@then(parsers.parse("the loop count should be {count:d}"))
def check_loop_count(modify_config_loops: ConfigModel, count: int):
    """Verify that hot reload applied the new loop count."""
    assert modify_config_loops.loops == count


@when("I start the application", target_fixture="start_application")
def start_application():
    ConfigLoader.reset_instance()
    loader = ConfigLoader()
    cfg = loader.load_config()
    return cfg


@then(parsers.parse('it should load settings from "{file}"'))
def check_config_loaded(start_application: ConfigModel, file: str):
    assert os.path.exists(file)
    assert isinstance(start_application, ConfigModel)


@then("the active agents should match the config file")
def check_agents_match(start_application: ConfigModel):
    file_cfg = ConfigLoader().load_config()
    assert start_application.agents == file_cfg.agents


@scenario(
    "../features/configuration_hot_reload.feature", "Load configuration on startup"
)
def test_load_config_startup():
    pass


@scenario("../features/configuration_hot_reload.feature", "Hot-reload on config change")
def test_hot_reload_config():
    pass


@scenario(
    "../features/configuration_hot_reload.feature",
    "Ignore invalid configuration changes",
)
def test_ignore_invalid_config():
    pass


@scenario(
    "../features/configuration_hot_reload.feature",
    "Hot-reload updates loop count",
)
def test_hot_reload_loops():
    """Scenario: changing loop count triggers a reload."""
    pass
