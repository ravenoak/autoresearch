import pytest

try:
    from tests.optional_imports import import_or_skip
except Exception:  # pragma: no cover - path fallback for --noconftest runs
    import importlib.util
    from pathlib import Path as _Path

    _mod_path = _Path(__file__).resolve().parents[1] / "optional_imports.py"
    spec = importlib.util.spec_from_file_location("tests.optional_imports", str(_mod_path))
    if spec and spec.loader:
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)
        import_or_skip = getattr(_mod, "import_or_skip")
    else:
        raise ModuleNotFoundError("Could not import tests.optional_imports via direct path fallback")


@pytest.mark.parametrize(
    "module, attr",
    [
        pytest.param("spacy", "__version__", marks=pytest.mark.requires_nlp),
        pytest.param("streamlit", "__version__", marks=pytest.mark.requires_ui),
        pytest.param("duckdb_extension_vss", None, marks=pytest.mark.requires_vss),
        pytest.param("git", "Repo", marks=pytest.mark.requires_git),
        pytest.param("redis", "__version__", marks=pytest.mark.requires_distributed),
        pytest.param("polars", "__version__", marks=pytest.mark.requires_analysis),
        pytest.param("fastembed", "__version__", marks=pytest.mark.requires_llm),
        pytest.param("docx", "Document", marks=pytest.mark.requires_parsers),
        pytest.param("bertopic", "__version__", marks=pytest.mark.requires_gpu),
    ],
)
def test_optional_extra_versions(module: str, attr: str) -> None:
    """Each optional extra exposes a recognizable attribute."""
    mod = import_or_skip(module)
    if attr is not None:
        assert hasattr(mod, attr)
