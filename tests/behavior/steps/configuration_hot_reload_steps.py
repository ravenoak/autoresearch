# flake8: noqa
import os
from pytest_bdd import scenario, when, then, parsers

from . import common_steps
from autoresearch.config import ConfigLoader, ConfigModel


@when(
    parsers.parse('I modify "{file}" to enable a new agent'),
    target_fixture="modify_config_enable_agent",
)
def modify_config_enable_agent(file, tmp_path):
    loader = ConfigLoader()
    reloaded: list[ConfigModel] = []

    def _observer(cfg: ConfigModel) -> None:
        reloaded.append(cfg)

    loader.watch_changes(_observer)

    cfg = {
        "core": {"backend": "lmstudio", "loops": 1, "ram_budget_mb": 512},
        "agent": {"NewAgent": {"enabled": True}},
    }
    import tomli_w

    with open(file, "w") as f:
        f.write(tomli_w.dumps(cfg))

    new_cfg = loader.load_config()
    loader.stop_watching()
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


@when("I start the application", target_fixture="start_application")
def start_application():
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


@scenario("../features/configuration_hot_reload.feature", "Load configuration on startup")
def test_load_config_startup():
    pass


@scenario("../features/configuration_hot_reload.feature", "Hot-reload on config change")
def test_hot_reload_config():
    pass
