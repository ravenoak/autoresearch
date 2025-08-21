"""Tests for the `examples` package."""

from importlib import resources
import tomllib


def test_sample_configuration() -> None:
    """Spec: docs/specs/examples.md#sample-configuration"""
    config_path = resources.files("autoresearch.examples") / "autoresearch.toml"
    data = tomllib.loads(config_path.read_text())
    core = data["core"]
    assert core["llm_backend"] == "lmstudio"
    assert core["loops"] == 3
