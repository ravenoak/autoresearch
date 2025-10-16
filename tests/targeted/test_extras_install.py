from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

import_or_skip: Callable[[str], ModuleType]
try:
    from tests.optional_imports import import_or_skip as _import_or_skip
except Exception:  # pragma: no cover - path fallback for --noconftest runs
    _mod_path = Path(__file__).resolve().parents[1] / "optional_imports.py"
    spec = importlib.util.spec_from_file_location("tests.optional_imports", str(_mod_path))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        attr = getattr(module, "import_or_skip")
        if not callable(attr):  # pragma: no cover - defensive guard
            raise TypeError("import_or_skip attribute is not callable")
        import_or_skip = cast(Callable[[str], ModuleType], attr)
    else:
        raise ModuleNotFoundError(
            "Could not import tests.optional_imports via direct path fallback"
        )
else:
    import_or_skip = cast(Callable[[str], ModuleType], _import_or_skip)


@pytest.mark.requires_nlp
def test_nlp_extra_imports() -> None:
    """Smoke test imports from the nlp extra."""
    spacy = import_or_skip("spacy")
    try:
        bertopic = importlib.import_module("bertopic")
    except Exception as exc:  # pragma: no cover - optional dependency issues
        pytest.skip(str(exc))
    nlp = spacy.blank("en")
    assert getattr(nlp, "pipe_names", []) == []
    assert hasattr(bertopic, "__version__")


@pytest.mark.requires_ui
def test_ui_extra_imports() -> None:
    """Smoke test imports from the ui extra."""
    st = import_or_skip("streamlit")
    pil_image = import_or_skip("PIL.Image")

    assert hasattr(st, "__version__")
    assert callable(getattr(pil_image, "open", None))


@pytest.mark.requires_vss
def test_vss_extra_imports() -> None:
    """Smoke test imports from the vss extra."""
    vss = import_or_skip("duckdb_extension_vss")
    assert hasattr(vss, "__file__")


@pytest.mark.requires_git
def test_git_extra_imports(tmp_path: Path) -> None:
    """Smoke test imports from the git extra."""
    git = import_or_skip("git")

    repo = git.Repo.init(tmp_path)
    assert repo.git_dir


@pytest.mark.requires_distributed
def test_distributed_extra_imports() -> None:
    """Smoke test imports from the distributed extra."""
    ray = import_or_skip("ray")
    redis = import_or_skip("redis")

    assert hasattr(ray, "__version__")
    assert hasattr(redis, "__version__")


@pytest.mark.requires_analysis
def test_analysis_extra_imports() -> None:
    """Smoke test imports from the analysis extra."""
    pl = import_or_skip("polars")

    df = pl.DataFrame({"a": [1, 2]})
    assert df.shape == (2, 1)


@pytest.mark.requires_llm
def test_llm_extra_imports() -> None:
    """Smoke test imports from the llm extra."""
    try:
        fastembed = importlib.import_module("fastembed")
        dspy = importlib.import_module("dspy")
    except Exception as exc:  # pragma: no cover - environment-specific
        pytest.skip(str(exc))

    assert any(hasattr(fastembed, attr) for attr in ("OnnxTextEmbedding", "TextEmbedding"))
    assert hasattr(dspy, "__version__")


@pytest.mark.requires_parsers
def test_parsers_extra_imports(tmp_path: Path) -> None:
    """Smoke test imports from the parsers extra."""
    docx = import_or_skip("docx")

    path = tmp_path / "test.docx"
    docx.Document().save(path)
    doc = docx.Document(path)
    assert len(doc.paragraphs) == 0


@pytest.mark.requires_gpu
def test_gpu_extra_imports() -> None:
    """Smoke test imports from the gpu extra."""
    bertopic = import_or_skip("bertopic")
    assert hasattr(bertopic, "__version__")


@pytest.mark.slow
def test_task_check_runs_after_setup() -> None:
    """Ensure task check runs from a fresh setup."""
    project_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PATH"] = f"{project_root / '.venv' / 'bin'}:{env['PATH']}"
    result: subprocess.CompletedProcess[bytes] = subprocess.run(
        ["task", "check", "EXTRAS=dev"],
        cwd=project_root,
        env=env,
        check=True,
    )
    assert result.returncode == 0
