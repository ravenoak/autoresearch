"""Test DuckDB extension download fallback."""

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "download_duckdb_extensions.py"
spec = importlib.util.spec_from_file_location("download_duckdb_extensions", MODULE_PATH)
download_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download_mod)


def test_network_failure_creates_stub(tmp_path, monkeypatch):
    """Ensure a stub is created when downloads fail."""

    class FailingConn:
        def execute(self, *args, **kwargs):
            return self

        def fetchall(self):
            return []

        def install_extension(self, name):
            raise download_mod.duckdb.Error("network unreachable")

        def close(self):
            pass

    monkeypatch.setattr(download_mod, "load_offline_env", lambda *_: {})
    monkeypatch.setattr(download_mod.duckdb, "connect", lambda *_: FailingConn())

    dest = download_mod.download_extension("vss", str(tmp_path))
    stub = tmp_path / "vss" / "vss.duckdb_extension"
    assert Path(dest) == stub
    assert stub.exists()
    assert stub.stat().st_size == 0
