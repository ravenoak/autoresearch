# flake8: noqa
from pytest_bdd import given

from autoresearch.main import app as cli_app
from autoresearch.api import app as api_app


@given("the Autoresearch application is running")
def application_running(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {
        "core": {"backend": "lmstudio", "loops": 1, "ram_budget_mb": 512},
        "search": {"backends": [], "context_aware": {"enabled": False}},
    }
    with open("autoresearch.toml", "w") as f:
        import tomli_w

        f.write(tomli_w.dumps(cfg))

    from autoresearch.llm import DummyAdapter

    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter())
    return


@given("the application is running with default configuration")
def app_running_with_default(tmp_path, monkeypatch):
    return application_running(tmp_path, monkeypatch)


@given("the application is running")
def app_running(tmp_path, monkeypatch):
    return application_running(tmp_path, monkeypatch)
