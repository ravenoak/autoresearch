# mypy: ignore-errors
import pytest


@pytest.mark.requires_nlp
def test_nlp_marker():
    assert True


@pytest.mark.requires_ui
def test_ui_marker():
    assert True


@pytest.mark.requires_vss
def test_vss_marker():
    assert True


@pytest.mark.requires_git
def test_git_marker():
    assert True


@pytest.mark.requires_distributed
def test_distributed_marker():
    assert True


@pytest.mark.requires_analysis
def test_analysis_marker():
    assert True


@pytest.mark.requires_llm
def test_llm_marker():
    assert True


@pytest.mark.requires_parsers
def test_parsers_marker():
    assert True


@pytest.mark.requires_gpu
def test_gpu_marker():
    assert True
