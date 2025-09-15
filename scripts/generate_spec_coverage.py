#!/usr/bin/env python3
"""Generate SPEC_COVERAGE.md from specification traceability links.

Usage:
    uv run python scripts/generate_spec_coverage.py [--output SPEC_COVERAGE.md]

The script inspects documentation in ``docs/specs`` and infers which source
modules are covered by specifications and which proofs or simulations support
them. It cross-references the inferred coverage with top-level packages in the
``src`` tree and writes a Markdown table summarising the results.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict, OrderedDict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "docs" / "specs"
SRC_DIR = ROOT / "src"


@dataclass
class CoverageEntry:
    """Collected specification and proof references for a module."""

    specs: set[str]
    proofs: set[str]


FOOTNOTE_PATTERN = re.compile(r"^\[(?P<id>[^\]]+)\]:\s*(?P<target>\S+)", re.MULTILINE)
REF_PATTERN = re.compile(r"\[[^\]]+\]\[(?P<id>[^\]]+)\]")
INLINE_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def canonical_module(path: Path) -> str | None:
    """Return a canonical module string for ``path`` or ``None`` if not code."""

    parts = path.parts
    if not parts or parts[0] != "src":
        return None
    pieces = list(parts[1:])
    if not pieces:
        return None
    if pieces[-1] == "__init__.py":
        pieces = pieces[:-1]
    module = "/".join(pieces)
    return module or None


def normalize_reference(spec_path: Path, target: str) -> Path | None:
    """Resolve ``target`` relative to ``spec_path`` and normalise anchors."""

    if not target or target.startswith("http"):
        return None
    clean = target.split("#", 1)[0]
    try:
        resolved = (spec_path.parent / clean).resolve()
    except OSError:  # pragma: no cover - defensive guard
        return None
    try:
        return resolved.relative_to(ROOT)
    except ValueError:
        return None


def parse_spec(spec_path: Path) -> tuple[set[str], set[str]]:
    """Extract modules and proofs referenced by ``spec_path``."""

    text = spec_path.read_text(encoding="utf-8")
    footnotes = {
        match.group("id"): match.group("target").split("#", 1)[0]
        for match in FOOTNOTE_PATTERN.finditer(text)
    }
    targets: list[str] = []
    targets.extend(
        footnotes.get(match.group("id")) for match in REF_PATTERN.finditer(text)
    )
    targets.extend(match.group(1) for match in INLINE_PATTERN.finditer(text))

    modules: set[str] = set()
    proofs: set[str] = set()
    for target in targets:
        relative = normalize_reference(spec_path, target)
        if relative is None:
            continue
        rel_str = relative.as_posix()
        module = canonical_module(relative)
        if module:
            modules.add(module)
            continue
        if rel_str.startswith("docs/algorithms/"):
            proofs.add(rel_str)
        elif rel_str.startswith("tests/"):
            proofs.add(rel_str)
        elif rel_str.startswith("scripts/"):
            proofs.add(rel_str)
    return modules, proofs


def collect_expected_modules() -> set[str]:
    """Return the set of top-level modules that must appear in the summary."""

    expected: set[str] = set()
    for package in ("autoresearch", "git"):
        base = SRC_DIR / package
        if not base.exists():
            continue
        expected.add(package)
        for path in base.iterdir():
            if path.is_file() and path.suffix == ".py" and path.name != "__init__.py":
                expected.add(f"{package}/{path.name}")
            elif path.is_dir() and (path / "__init__.py").exists():
                expected.add(f"{package}/{path.name}")
    return expected


def maybe_add_parent(
    module: str,
    spec_path: Path,
    proofs: set[str],
    entry_map: dict[str, CoverageEntry],
    spec_rel: str,
) -> None:
    """Propagate coverage to the parent package when the spec names it."""

    parts = module.split("/")
    if len(parts) <= 2:
        return
    parent = "/".join(parts[:-1])
    parent_name = parent.split("/")[-1]
    spec_name = spec_path.stem.replace("-", "_")
    if spec_name != parent_name:
        return
    parent_path = SRC_DIR / parent
    if not parent_path.exists():
        return
    entry = entry_map.setdefault(parent, CoverageEntry(set(), set()))
    entry.specs.add(spec_rel)
    entry.proofs.update(proofs)


def gather_coverage() -> dict[str, CoverageEntry]:
    """Collect coverage details from specification documents."""

    coverage: dict[str, CoverageEntry] = {}
    for spec_path in SPEC_DIR.glob("*.md"):
        if spec_path.name == "README.md":
            continue
        modules, proofs = parse_spec(spec_path)
        if not modules and not proofs:
            continue
        spec_rel = spec_path.relative_to(ROOT).as_posix()
        for module in modules:
            entry = coverage.setdefault(module, CoverageEntry(set(), set()))
            entry.specs.add(spec_rel)
            entry.proofs.update(proofs)
            maybe_add_parent(module, spec_path, proofs, coverage, spec_rel)
    return coverage


def determine_status(entry: CoverageEntry) -> str:
    """Return a human-readable coverage status for ``entry``."""

    if not entry.specs:
        return "Missing spec"
    if not entry.proofs:
        return "Missing proof"
    return "OK"


class FootnoteRegistry:
    """Assign stable identifiers to proof references."""

    def __init__(self) -> None:
        self._mapping: OrderedDict[str, str] = OrderedDict()
        self._counters: defaultdict[str, int] = defaultdict(int)

    @staticmethod
    def _prefix(path: str) -> str:
        if path.startswith("docs/algorithms/"):
            return "p"
        if path.startswith("scripts/"):
            return "s"
        if path.startswith("tests/"):
            return "t"
        return "d"

    def reference(self, path: str) -> str:
        """Return the identifier for ``path``, allocating one if needed."""

        path = path.replace("\\", "/")
        if path not in self._mapping:
            prefix = self._prefix(path)
            self._counters[prefix] += 1
            self._mapping[path] = f"{prefix}{self._counters[prefix]}"
        return self._mapping[path]

    def items(self) -> list[tuple[str, str]]:
        """Return ``(label, path)`` pairs in insertion order."""

        return [(label, path) for path, label in self._mapping.items()]


def build_table(entries: dict[str, CoverageEntry]) -> tuple[str, list[str]]:
    """Return the Markdown table and footnote definitions."""

    footnotes = FootnoteRegistry()
    lines = [
        "| Module | Spec | Proof/Simulation | Status |",
        "| --- | --- | --- | --- |",
    ]

    for module in sorted(entries):
        entry = entries[module]
        specs = sorted(entry.specs)
        proofs = sorted(entry.proofs)

        if specs:
            spec_links = [f"[{Path(spec).name}]({spec})" for spec in specs]
            spec_cell = "<br>".join(spec_links)
        else:
            spec_cell = "—"

        if proofs:
            def sort_key(path: str) -> tuple[int, str]:
                if path.startswith("docs/algorithms/"):
                    return (0, path)
                if path.startswith("scripts/"):
                    return (1, path)
                if path.startswith("tests/"):
                    return (2, path)
                return (3, path)

            proof_refs = []
            for proof in sorted(proofs, key=sort_key):
                label = footnotes.reference(proof)
                proof_refs.append(f"[{label}]")
            proof_cell = ", ".join(proof_refs)
        else:
            proof_cell = "—"

        status = determine_status(entry)
        lines.append(f"| `{module}` | {spec_cell} | {proof_cell} | {status} |")

    footnote_lines = [f"[{label}]: {path}" for label, path in footnotes.items()]
    return "\n".join(lines), footnote_lines


def write_spec_coverage(output: Path) -> tuple[list[str], list[str]]:
    """Generate the coverage table and persist it to ``output``."""

    coverage = gather_coverage()
    expected = collect_expected_modules()
    all_modules = expected | set(coverage)

    entries: dict[str, CoverageEntry] = {}
    for module in all_modules:
        if module in coverage:
            entry = coverage[module]
            entries[module] = CoverageEntry(set(entry.specs), set(entry.proofs))
        else:
            entries[module] = CoverageEntry(set(), set())

    table, footnotes = build_table(entries)
    content = "\n".join([table, "", *footnotes]) if footnotes else table
    output.write_text(content + "\n", encoding="utf-8")

    missing_specs = sorted(module for module, entry in entries.items() if not entry.specs)
    missing_proofs = sorted(
        module for module, entry in entries.items() if entry.specs and not entry.proofs
    )
    return missing_specs, missing_proofs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SPEC_COVERAGE.md")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "SPEC_COVERAGE.md",
        help="Destination file for the coverage table",
    )
    args = parser.parse_args()

    missing_specs, missing_proofs = write_spec_coverage(args.output)

    if missing_specs:
        print("Modules missing specs:")
        for module in missing_specs:
            print(f"- {module}")
    if missing_proofs:
        print("Modules missing proofs:")
        for module in missing_proofs:
            print(f"- {module}")
    print(f"Wrote spec coverage to {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
