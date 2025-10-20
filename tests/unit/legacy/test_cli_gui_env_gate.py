from typer.testing import CliRunner

from autoresearch.main.app import app


def test_gui_requires_opt_in(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_ENABLE_STREAMLIT", raising=False)
    runner = CliRunner()
    result = runner.invoke(app, ["gui"])

    assert result.exit_code == 1
    assert "Streamlit GUI is deprecated" in result.stdout
    assert "AUTORESEARCH_ENABLE_STREAMLIT=1 autoresearch gui" in result.stdout


def test_gui_runs_with_opt_in(monkeypatch):
    import subprocess

    monkeypatch.setenv("AUTORESEARCH_ENABLE_STREAMLIT", "1")
    recorded = {}

    def fake_run(cmd, *args, **kwargs):
        recorded["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()
    result = runner.invoke(app, ["gui", "--port", "8600", "--no-browser"])

    assert result.exit_code == 0
    assert "Launching Streamlit GUI on port 8600" in result.stdout
    assert recorded["cmd"][0:4] == ["streamlit", "run", recorded["cmd"][2], "--server.port"]
    assert recorded["cmd"][2].endswith("streamlit_app.py")
    assert recorded["cmd"][4] == "8600"
    assert recorded["cmd"][5:] == ["--server.headless", "true"]
