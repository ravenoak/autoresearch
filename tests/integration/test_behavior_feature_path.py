"""Regression test for invoking a single feature file by path."""

from __future__ import annotations

import subprocess


def test_direct_feature_invocation() -> None:
    """Run a behavior feature file via its direct path.

    This ensures ``bdd_features_base_dir`` configuration resolves step
    definitions when a feature file is targeted explicitly.
    """

    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "tests/behavior/features/api_orchestrator_integration.feature",
            "-q",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

