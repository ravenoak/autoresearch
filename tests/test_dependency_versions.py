"""Ensure dependency versions match documentation."""

from __future__ import annotations

from pathlib import Path
import tomllib
from packaging.requirements import Requirement


ROOT = Path(__file__).resolve().parents[1]


def _parse_pyproject() -> dict[str, str]:
    with open(ROOT / "pyproject.toml", "rb") as fh:
        data = tomllib.load(fh)
    deps: dict[str, str] = {}
    for dep in data["project"]["dependencies"]:
        req = Requirement(dep)
        key = req.name
        if req.extras:
            key += f"[{','.join(sorted(req.extras))}]"
        spec = next(iter(req.specifier))
        deps[key] = spec.version
    return deps


def _parse_docs() -> dict[str, str]:
    lines = (ROOT / "docs/installation.md").read_text().splitlines()
    start = lines.index("| Package | Minimum version |") + 2
    deps: dict[str, str] = {}
    for line in lines[start:]:
        line = line.strip()
        if not line or not line.startswith("|"):
            break
        name, version = (part.strip() for part in line.strip("|").split("|"))
        deps[name] = version
    return deps


def test_dependency_versions_match() -> None:
    """CI guardrail verifying docs align with pyproject dependencies."""
    assert _parse_pyproject() == _parse_docs()

