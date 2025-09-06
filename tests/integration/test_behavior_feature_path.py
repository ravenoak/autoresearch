"""Regression test for invoking a single feature file by path."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.mark.skip(reason="feature file not available in this environment")
def test_direct_feature_invocation() -> None:
    """Run a behavior feature file via its direct path.

    This ensures ``bdd_features_base_dir`` configuration resolves step
    definitions when a feature file is targeted explicitly.
    """

    repo_root = Path(__file__).resolve().parents[2]
    feature_rel = "tests/behavior/features/api_orchestrator_integration.feature"
    result = subprocess.run(
        ["uv", "run", "pytest", feature_rel, "-q"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert result.returncode == 0, result.stdout + result.stderr
