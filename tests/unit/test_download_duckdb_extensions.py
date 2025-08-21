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


class DefaultPathConn:
    def __init__(self, path, platform_name):
        self.path = Path(path)
        self.platform_name = platform_name

    def execute(self, *args, **kwargs):
        class _Cursor:
            def fetchall(self_inner):
                return [("vss",)]

        return _Cursor()

    def install_extension(self, name):
        default_dir = self.path.parent / ".duckdb" / "extensions" / self.platform_name
        default_dir.mkdir(parents=True, exist_ok=True)
        (default_dir / f"{name}.duckdb_extension").write_text("dummy")

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
    assert "Proceeding without them" in caplog.text


def test_download_extension_fallback_path(monkeypatch, tmp_path):
    """Extension copies from default DuckDB dir when output dir is empty."""

    def _connect(path):
        return DefaultPathConn(path, "linux_amd64")

    monkeypatch.setattr(duckdb, "connect", _connect)
    result = dde.download_extension("vss", tmp_path, "linux_amd64")
    assert result is not None
    ext_dir = Path(tmp_path) / "extensions" / "vss"
    files = list(ext_dir.glob("*.duckdb_extension"))
    assert files, "extension file was not copied"
