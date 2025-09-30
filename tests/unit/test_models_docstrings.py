"""Tests for models docstrings; see docs/algorithms/models.md."""

from pathlib import Path

from autoresearch.models import QueryResponse

SPEC_PATH = Path(__file__).resolve().parents[2] / "docs/algorithms/models.md"


def test_models_spec_exists() -> None:
    """Models specification document must exist."""
    assert SPEC_PATH.is_file()


def test_module_docstrings() -> None:
    """Test that the models module has a comprehensive docstring."""
    import autoresearch.models as models_module

    # Check that the module has a docstring
    assert models_module.__doc__ is not None, "models module should have a docstring"

    # Check that the docstring is comprehensive
    docstring = models_module.__doc__
    assert (
        len(docstring.strip().split("\n")) >= 2
    ), "models module docstring should have at least 2 lines"
    assert (
        "This module" in docstring or "Module for" in docstring or "Provides" in docstring
    ), "models module docstring should explain what the module provides"


def test_module_docstring_mentions_spec() -> None:
    """Module docstring should reference the specification."""
    import autoresearch.models as models_module

    assert "docs/algorithms/models.md" in (models_module.__doc__ or "")


def test_class_docstrings() -> None:
    """Test that classes have comprehensive docstrings."""
    classes = [QueryResponse]

    for cls in classes:
        # Check that the class has a docstring
        assert cls.__doc__ is not None, f"{cls.__name__} should have a docstring"

        # Check that the docstring is comprehensive
        docstring = cls.__doc__
        assert (
            len(docstring.strip().split("\n")) >= 2
        ), f"{cls.__name__} docstring should have at least 2 lines"
        assert (
            "This class" in docstring or "Represents" in docstring or "Model for" in docstring
        ), f"{cls.__name__} docstring should explain what the class represents"

        # Check that the docstring explains the fields
        assert (
            "answer:" in docstring.lower() or "answer (" in docstring.lower()
        ), f"{cls.__name__} docstring should explain the answer field"
        assert (
            "citations:" in docstring.lower() or "citations (" in docstring.lower()
        ), f"{cls.__name__} docstring should explain the citations field"
        assert (
            "reasoning:" in docstring.lower() or "reasoning (" in docstring.lower()
        ), f"{cls.__name__} docstring should explain the reasoning field"
        assert (
            "metrics:" in docstring.lower() or "metrics (" in docstring.lower()
        ), f"{cls.__name__} docstring should explain the metrics field"
