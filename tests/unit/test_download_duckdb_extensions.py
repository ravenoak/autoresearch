import importlib.util
import logging
import os
import subprocess
import sys
from pathlib import Path

import duckdb

spec = importlib.util.spec_from_file_location(
    "download_duckdb_extensions",
    Path(__file__).resolve().parents[2] / "scripts" / "download_duckdb_extensions.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load download_duckdb_extensions module")
dde = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dde)


class FailingConn:
    def __init__(self, path):
        self.path = path
        self.calls = 0

    def execute(self, *args, **kwargs):
        return None

    def install_extension(self, name):
        self.calls += 1
        raise duckdb.Error("network failure")

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


def test_download_extension_network_fallback(monkeypatch, tmp_path, caplog):
    """Network failures load offline env and continue."""
    env_file = tmp_path / ".env.offline"
    stub_src = tmp_path / "extensions" / "vss_stub.duckdb_extension"
    stub_src.parent.mkdir(parents=True, exist_ok=True)
    stub_src.write_text("stub")
    env_file.write_text(f"VECTOR_EXTENSION_PATH={stub_src}\n")

    monkeypatch.chdir(tmp_path)
    conn = FailingConn("path")
    monkeypatch.setattr(duckdb, "connect", lambda path: conn)
    caplog.set_level(logging.WARNING)
    result = dde.download_extension("vss", tmp_path, "linux_amd64")
    dst = tmp_path / "extensions" / "vss" / stub_src.name
    assert result == str(dst)
    assert conn.calls == 3
    assert os.environ["VECTOR_EXTENSION_PATH"] == str(dst)
    assert "after 3 attempts" in caplog.text
    assert "Falling back to offline configuration" in caplog.text

    monkeypatch.setattr(
        sys,
        "argv",
        ["download_duckdb_extensions.py", "--output-dir", str(tmp_path)],
    )
    caplog.clear()
    caplog.set_level(logging.INFO)
    dde.main()
    assert "Extensions downloaded successfully" in caplog.text


def test_download_extension_creates_stub_when_offline(monkeypatch, tmp_path, caplog):
    """Network failure without offline path creates stub."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VECTOR_EXTENSION_PATH", raising=False)
    conn = FailingConn("path")
    monkeypatch.setattr(duckdb, "connect", lambda path: conn)
    caplog.set_level(logging.WARNING)
    stub = tmp_path / "extensions" / "vss" / "vss.duckdb_extension"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text("pre-existing data")
    result = dde.download_extension("vss", tmp_path, "linux_amd64")
    assert result == str(stub)
    assert stub.exists()
    assert stub.stat().st_size == 0
    assert stub.read_bytes() == b""
    assert "created stub" in caplog.text


def test_download_extension_offline_without_duckdb(monkeypatch, tmp_path, caplog):
    """Missing duckdb module uses offline copy."""
    env_file = tmp_path / ".env.offline"
    stub_src = tmp_path / "extensions" / "vss_stub.duckdb_extension"
    stub_src.parent.mkdir(parents=True, exist_ok=True)
    stub_src.write_text("stub")
    env_file.write_text(f"VECTOR_EXTENSION_PATH={stub_src}\n")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(dde, "duckdb", None)
    caplog.set_level(logging.WARNING)
    result = dde.download_extension("vss", tmp_path, "linux_amd64")
    dst = tmp_path / "extensions" / "vss" / stub_src.name
    assert result == str(dst)
    assert os.environ["VECTOR_EXTENSION_PATH"] == str(dst)
    assert "duckdb package not available" in caplog.text


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


def test_offline_fallback_skips_samefile_copy(monkeypatch, tmp_path, caplog):
    """Offline fallback ignores copies when the cached file is already in place."""

    env_file = tmp_path / ".env.offline"
    cached = tmp_path / "extensions" / "vss" / "vss.duckdb_extension"
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text("cached extension")
    env_file.write_text(f"VECTOR_EXTENSION_PATH={cached}\n")

    monkeypatch.chdir(tmp_path)
    conn = FailingConn("path")
    monkeypatch.setattr(duckdb, "connect", lambda path: conn)
    caplog.set_level(logging.INFO)

    result = dde.download_extension("vss", tmp_path, "linux_amd64")

    assert result == str(cached)
    assert conn.calls == 3
    assert cached.read_text() == "cached extension"
    assert "SameFileError" not in caplog.text
    assert "already present" in caplog.text


def test_setup_sh_ignores_smoke_failure_with_stub(monkeypatch, tmp_path):
    """Smoke test failures are ignored when only a stub extension exists."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VECTOR_EXTENSION_PATH", raising=False)
    conn = FailingConn("path")
    monkeypatch.setattr(duckdb, "connect", lambda path: conn)
    result = dde.download_extension("vss", tmp_path, "linux_amd64")
    stub = Path(result)
    assert stub.exists() and stub.stat().st_size == 0

    script = (
        'VSS_EXTENSION=$(find ./extensions -name "vss*.duckdb_extension" '
        "-size +0c | head -n 1)\n"
        'if [ -n "$VSS_EXTENSION" ]; then false || echo fail; '
        "else false >/dev/null || true; fi\n"
    )
    completed = subprocess.run(
        ["bash", "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "fail" not in completed.stdout


def test_load_offline_env_sets_vector_extension_path(monkeypatch, tmp_path, caplog):
    """Documentation example for VECTOR_EXTENSION_PATH is honored."""
    env_file = tmp_path / ".env.offline"
    stub_path = tmp_path / "extensions" / "vss_stub.duckdb_extension"
    stub_path.parent.mkdir(parents=True, exist_ok=True)
    stub_path.write_text("stub")
    env_file.write_text(f"VECTOR_EXTENSION_PATH={stub_path}\n")

    monkeypatch.chdir(tmp_path)
    caplog.set_level(logging.INFO)
    vars_loaded = dde.load_offline_env()
    assert vars_loaded["VECTOR_EXTENSION_PATH"] == str(stub_path)
    assert os.environ["VECTOR_EXTENSION_PATH"] == str(stub_path)
    assert "Loaded offline configuration" in caplog.text
