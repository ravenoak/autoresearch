import importlib.util
import logging
import sys
from pathlib import Path

import duckdb

spec = importlib.util.spec_from_file_location(
    "download_duckdb_extensions",
    Path(__file__).resolve().parents[2] / "scripts" / "download_duckdb_extensions.py",
)
dde = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dde)


class FailingConn:
    def __init__(self, path):
        self.path = path

    def execute(self, *args, **kwargs):
        return None

    def install_extension(self, name):
        raise duckdb.IOException("network failure")

    def close(self):
        pass


def test_download_extension_network_failure(monkeypatch, tmp_path, caplog):
    """Extension downloads warn and continue on network failure."""
    monkeypatch.setattr(duckdb, "connect", lambda path: FailingConn(path))
    caplog.set_level(logging.WARNING)
    result = dde.download_extension("vss", tmp_path, "linux_amd64")
    assert result is None
    assert "Error downloading vss extension" in caplog.text

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "download_duckdb_extensions.py",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(dde, "download_extension", lambda *a, **k: None)
    dde.main()  # Should not raise SystemExit
