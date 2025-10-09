"""Regression test ensuring `from __future__ import annotations` stays first."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _iter_python_modules(root: Path) -> list[Path]:
    return [
        path for path in root.rglob("*.py")
        if ".git" not in path.parts and ".venv" not in path.parts
    ]


def _first_non_docstring_node(body: list[ast.stmt]) -> int:
    if not body:
        return 0
    node = body[0]
    if (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ):
        return 1
    return 0


@pytest.mark.quick
def test_future_annotations_import_is_first() -> None:
    """Ensure the annotations future import appears before other statements."""

    for module_path in _iter_python_modules(REPO_ROOT):
        source = module_path.read_text(encoding="utf-8")
        if "from __future__ import annotations" not in source:
            continue

        try:
            module = ast.parse(source)
        except SyntaxError as exc:  # pragma: no cover - surfaces invalid layout
            pytest.fail(
                f"{module_path.relative_to(REPO_ROOT)} failed to parse: {exc}"
            )

        idx = _first_non_docstring_node(module.body)
        if idx >= len(module.body):
            continue

        node = module.body[idx]
        if not (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
        ):
            pytest.fail(
                "`from __future__ import annotations` must be the first "
                "executable statement in "
                f"{module_path.relative_to(REPO_ROOT)}"
            )
