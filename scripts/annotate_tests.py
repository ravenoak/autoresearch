"""Annotate tests under ``tests/`` with explicit type hints.

Usage:
    uv run python scripts/annotate_tests.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor
from libcst.helpers import get_full_name_for_node


@dataclass(frozen=True)
class ParamType:
    annotation: str
    imports: tuple[tuple[str, str | None], ...] = ()


PARAM_TYPES: dict[str, ParamType] = {
    "monkeypatch": ParamType(
        annotation="pytest.MonkeyPatch",
        imports=(("pytest", None),),
    ),
    "tmp_path": ParamType(
        annotation="Path",
        imports=(("pathlib", "Path"),),
    ),
    "tmp_path_factory": ParamType(
        annotation="pytest.TempPathFactory",
        imports=(("pytest", None),),
    ),
    "capsys": ParamType(
        annotation="pytest.CaptureFixture[str]",
        imports=(("pytest", None),),
    ),
    "capfd": ParamType(
        annotation="pytest.CaptureFixture[str]",
        imports=(("pytest", None),),
    ),
    "capfdbinary": ParamType(
        annotation="pytest.CaptureFixture[bytes]",
        imports=(("pytest", None),),
    ),
    "caplog": ParamType(
        annotation="pytest.LogCaptureFixture",
        imports=(("pytest", None),),
    ),
    "mocker": ParamType(
        annotation="pytest_mock.MockerFixture",
        imports=(("pytest_mock", None),),
    ),
    "requests_mock": ParamType(
        annotation="requests_mock.Mocker",
        imports=(("requests_mock", None),),
    ),
    "respx_mock": ParamType(
        annotation="respx.MockRouter",
        imports=(("respx", None),),
    ),
    "event_loop": ParamType(
        annotation="asyncio.AbstractEventLoop",
        imports=(("asyncio", None),),
    ),
    "tmpdir": ParamType(
        annotation="Any",
    ),
    "tmpdir_factory": ParamType(
        annotation="Any",
    ),
}


class AnnotateTestsTransformer(cst.CSTTransformer):
    def __init__(self, context: CodemodContext) -> None:
        super().__init__()
        self.context = context
        self.modified = False
        self.has_any_import = False
        self.needs_any = False
        self.imported_modules: set[str] = set()
        self.imported_from: dict[str, set[str]] = {}

    def visit_Import(self, node: cst.Import) -> None:  # pragma: no cover - traversal
        for alias in node.names:
            name = alias.evaluated_name
            self.imported_modules.add(name)
            if name == "typing" and alias.asname is None:
                # plain ``import typing`` does not import ``Any`` directly.
                continue

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:  # pragma: no cover - traversal
        if node.module is None:
            return
        module_name = get_full_name_for_node(node.module)
        if module_name is None:
            return
        imported = self.imported_from.setdefault(module_name, set())
        for alias in node.names:
            if isinstance(alias, cst.ImportStar):
                imported.add("*")
            else:
                imported.add(alias.name.value)
            if module_name == "typing" and isinstance(alias, cst.ImportAlias):
                if alias.name.value == "Any":
                    self.has_any_import = True

    def _ensure_imports(self, imports: Iterable[tuple[str, str | None]]) -> None:
        for module, obj in imports:
            AddImportsVisitor.add_needed_import(self.context, module=module, obj=obj)
            self.modified = True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        is_test = original_node.name.value.startswith("test_")
        is_fixture = any(
            isinstance(decorator.decorator, cst.Attribute)
            and decorator.decorator.attr.value == "fixture"
            or isinstance(decorator.decorator, cst.Name)
            and decorator.decorator.value == "fixture"
            for decorator in original_node.decorators or []
        )
        if not is_test and not is_fixture:
            return updated_node

        params = updated_node.params
        param_lists = [
            list(params.posonly_params),
            list(params.params),
            list(params.kwonly_params),
        ]
        star_arg = params.star_arg
        star_kwarg = params.star_kwarg
        changed = False

        def annotate_param(param: cst.Param) -> cst.Param:
            nonlocal changed
            if param.annotation is not None:
                return param
            name = param.name.value
            if name in {"self", "cls"}:
                return param
            param_type = PARAM_TYPES.get(name)
            if param_type is None:
                annotation = "Any"
                self.needs_any = True
                param = param.with_changes(annotation=cst.Annotation(cst.Name(annotation)))
            else:
                if param_type.annotation == "Any":
                    self.needs_any = True
                annotation_node = cst.parse_expression(param_type.annotation)
                param = param.with_changes(annotation=cst.Annotation(annotation_node))
                self._ensure_imports(param_type.imports)
            changed = True
            return param

        for idx, plist in enumerate(param_lists):
            if not plist:
                continue
            param_lists[idx] = [annotate_param(param) for param in plist]

        if isinstance(star_arg, cst.Param) and star_arg.annotation is None:
            star_arg = star_arg.with_changes(
                annotation=cst.Annotation(cst.Name("Any"))
            )
            self.needs_any = True
            changed = True
        if isinstance(star_kwarg, cst.Param) and star_kwarg.annotation is None:
            star_kwarg = star_kwarg.with_changes(
                annotation=cst.Annotation(cst.Name("Any"))
            )
            self.needs_any = True
            changed = True

        if changed:
            params = params.with_changes(
                posonly_params=tuple(param_lists[0]),
                params=tuple(param_lists[1]),
                kwonly_params=tuple(param_lists[2]),
                star_arg=star_arg,
                star_kwarg=star_kwarg,
            )
            updated_node = updated_node.with_changes(params=params)

        def _is_name_annotation(ann: cst.Annotation | None, name: str) -> bool:
            return (
                isinstance(ann, cst.Annotation)
                and isinstance(ann.annotation, cst.Name)
                and ann.annotation.value == name
            )

        if updated_node.returns is None:
            if is_test:
                new_return = cst.Annotation(cst.Name("None"))
            else:
                new_return = cst.Annotation(cst.Name("Any"))
                self.needs_any = True
            updated_node = updated_node.with_changes(returns=new_return)
            changed = True
        elif is_fixture and _is_name_annotation(updated_node.returns, "None"):
            updated_node = updated_node.with_changes(
                returns=cst.Annotation(cst.Name("Any"))
            )
            self.needs_any = True
            changed = True

        if changed:
            self.modified = True
        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        if self.needs_any and not self.has_any_import:
            self._ensure_imports((("typing", "Any"),))
            self.has_any_import = True
        return updated_node


def annotate_file(path: Path) -> None:
    source = path.read_text()
    module = cst.parse_module(source)
    context = CodemodContext()
    transformer = AnnotateTestsTransformer(context)
    updated = module.visit(transformer)
    if transformer.modified:
        updated = updated.visit(AddImportsVisitor(context))
        path.write_text(updated.code)


def main() -> None:
    root = Path("tests")
    for path in sorted(root.rglob("*.py")):
        if "unit" in path.parts or "evaluation" in path.parts:
            annotate_file(path)


if __name__ == "__main__":
    main()
