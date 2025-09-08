import os
import subprocess
import uuid
from pathlib import Path
import shutil

import duckdb
import pytest


@pytest.mark.requires_nlp
def test_nlp_extra_imports() -> None:
    """Smoke test imports from the nlp extra."""
    spacy = pytest.importorskip("spacy")
    try:
        bertopic = __import__("bertopic")
    except Exception as exc:  # pragma: no cover - optional dependency issues
        pytest.skip(str(exc))
    nlp = spacy.blank("en")
    assert getattr(nlp, "pipe_names", []) == []
    assert hasattr(bertopic, "__version__")


@pytest.mark.requires_ui
def test_ui_extra_imports() -> None:
    """Smoke test imports from the ui extra."""
    st = pytest.importorskip("streamlit")

    assert hasattr(st, "__version__")


@pytest.mark.requires_vss
def test_vss_extra_imports() -> None:
    """Smoke test imports from the vss extra."""
    vss = pytest.importorskip("duckdb_extension_vss")
    con = duckdb.connect()
    try:
        assert con.execute("SELECT 1").fetchone()[0] == 1
    finally:
        con.close()
    assert hasattr(vss, "__version__") or vss is not None


@pytest.mark.requires_git
def test_git_extra_imports(tmp_path) -> None:
    """Smoke test imports from the git extra."""
    git = pytest.importorskip("git")

    repo = git.Repo.init(tmp_path)
    assert repo.git_dir


@pytest.mark.requires_distributed
def test_distributed_extra_imports(tmp_path, monkeypatch) -> None:
    """Smoke test imports from the distributed extra."""
    ray = pytest.importorskip("ray")
    redis = pytest.importorskip("redis")
    temp_dir = Path("/tmp") / f"raytmp_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("RAY_TMPDIR", str(temp_dir))
    try:
        ray.init(
            num_cpus=1,
            local_mode=True,
            ignore_reinit_error=True,
            _temp_dir=str(temp_dir),
        )
    except ValueError as exc:
        pytest.skip(str(exc))
    else:
        try:
            is_initialized = getattr(ray, "is_initialized", lambda: True)
            assert is_initialized()
        finally:
            ray.shutdown()
    assert hasattr(redis, "__version__")
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.requires_analysis
def test_analysis_extra_imports() -> None:
    """Smoke test imports from the analysis extra."""
    pl = pytest.importorskip("polars")

    df = pl.DataFrame({"a": [1, 2]})
    assert df.shape == (2, 1)


@pytest.mark.requires_llm
def test_llm_extra_imports() -> None:
    """Smoke test imports from the llm extra."""
    try:
        fastembed = __import__("fastembed")
        dspy = __import__("dspy")
    except Exception as exc:  # pragma: no cover - environment-specific
        pytest.skip(str(exc))

    assert hasattr(fastembed, "TextEmbedding")
    assert hasattr(dspy, "__version__")


@pytest.mark.requires_parsers
def test_parsers_extra_imports(tmp_path) -> None:
    """Smoke test imports from the parsers extra."""
    docx = pytest.importorskip("docx")

    path = tmp_path / "test.docx"
    docx.Document().save(path)
    doc = docx.Document(path)
    assert len(doc.paragraphs) == 0


@pytest.mark.slow
def test_task_check_runs_after_setup() -> None:
    """Ensure task check runs from a fresh setup."""
    project_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PATH"] = f"{project_root / '.venv' / 'bin'}:{env['PATH']}"
    subprocess.run(["task", "check", "EXTRAS=dev"], cwd=project_root, env=env, check=True)
