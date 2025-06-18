# flake8: noqa
import os
import json
from typer.testing import CliRunner
from fastapi.testclient import TestClient
from pytest_bdd import given

from autoresearch.main import app as cli_app
from autoresearch.api import app as api_app

runner = CliRunner()
client = TestClient(api_app)


@given("the Autoresearch application is running")
def application_running(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = {"core": {"backend": "lmstudio", "loops": 1, "ram_budget_mb": 512}}
    with open("autoresearch.toml", "w") as f:
        import tomli_w

        f.write(tomli_w.dumps(cfg))

    monkeypatch.setattr(
        "autoresearch.search.Search.external_lookup",
        lambda q, max_results=5: [{"title": "t", "url": "u"}],
    )
    from autoresearch.llm import DummyAdapter

    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter())
    return


@given("the application is running with default configuration")
def app_running_with_default(tmp_path, monkeypatch):
    return application_running(tmp_path, monkeypatch)


@given("the application is running")
def app_running(tmp_path, monkeypatch):
    return application_running(tmp_path, monkeypatch)
