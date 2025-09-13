import os
import subprocess
from pathlib import Path

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
    assert hasattr(vss, "__file__")


@pytest.mark.requires_git
def test_git_extra_imports(tmp_path) -> None:
    """Smoke test imports from the git extra."""
    git = pytest.importorskip("git")

    repo = git.Repo.init(tmp_path)
    assert repo.git_dir


@pytest.mark.requires_distributed
def test_distributed_extra_imports() -> None:
    """Smoke test imports from the distributed extra."""
    ray = pytest.importorskip("ray")
    redis = pytest.importorskip("redis")

    assert hasattr(ray, "__version__")
    assert hasattr(redis, "__version__")


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


@pytest.mark.requires_gpu
def test_gpu_extra_imports() -> None:
    """Smoke test imports from the gpu extra."""
    bertopic = pytest.importorskip("bertopic")
    assert hasattr(bertopic, "__version__")


@pytest.mark.slow
def test_task_check_runs_after_setup() -> None:
    """Ensure task check runs from a fresh setup."""
    project_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PATH"] = f"{project_root / '.venv' / 'bin'}:{env['PATH']}"
    subprocess.run(["task", "check", "EXTRAS=dev"], cwd=project_root, env=env, check=True)
