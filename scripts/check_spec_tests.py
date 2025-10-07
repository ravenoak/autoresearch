#!/usr/bin/env python3
"""Verify that each spec references existing tests.

Usage:
    uv run python scripts/check_spec_tests.py
"""
from __future__ import annotations

import pathlib
import re
from collections import defaultdict


ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "docs" / "specs"
MANIFEST_PATH = ROOT / "SPEC_COVERAGE.md"

EXTRA_SPECS = [
    ROOT / "docs" / "algorithms" / "storage_eviction.md",
    ROOT / "docs" / "orchestrator_state_spec.md",
]


def _load_manifest() -> tuple[
    dict[pathlib.Path, set[pathlib.Path]],
    dict[str, str],
    dict[pathlib.Path, list[str]],
]:
    """Load SPEC_COVERAGE mappings from spec files to test targets."""

    text = MANIFEST_PATH.read_text().splitlines()
    test_ref_pattern = re.compile(r"^\[(t\d+)]:\s+(.+)$")
    spec_link_pattern = re.compile(r"\((docs/specs/[^)]+)\)")
    test_id_pattern = re.compile(r"\[(t\d+)\]")

    id_to_target: dict[str, str] = {}
    for line in text:
        match = test_ref_pattern.match(line.strip())
        if not match:
            continue
        test_id, target = match.groups()
        id_to_target[test_id] = target.strip()

    manifest: dict[pathlib.Path, set[pathlib.Path]] = defaultdict(set)
    manifest_ids: dict[pathlib.Path, list[str]] = defaultdict(list)
    for line in text:
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().split("|")]
        if len(parts) < 5:
            continue
        spec_cell = parts[2]
        proof_cell = parts[3]
        spec_links = spec_link_pattern.findall(spec_cell)
        if not spec_links:
            continue
        test_ids = test_id_pattern.findall(proof_cell)
        if not test_ids:
            continue
        for spec_link in spec_links:
            spec_path = (ROOT / spec_link).resolve()
            rel_spec = spec_path.relative_to(ROOT)
            bucket = manifest[rel_spec]
            for test_id in test_ids:
                raw_target = id_to_target.get(test_id)
                if raw_target is None:
                    continue
                base_target = raw_target.split("::", 1)[0]
                candidate = (ROOT / base_target).resolve()
                if not candidate.exists():
                    continue
                manifest_ids[rel_spec].append(test_id)
                bucket.add(candidate.relative_to(ROOT))

    return manifest, id_to_target, manifest_ids


def main() -> int:
    manifest, manifest_ids, manifest_index = _load_manifest()
    stale_manifest: dict[str, str] = {}
    for test_id, raw_target in manifest_ids.items():
        base_target = raw_target.split("::", 1)[0]
        candidate = (ROOT / base_target).resolve()
        if not candidate.exists():
            stale_manifest[test_id] = raw_target

    missing: dict[pathlib.Path, list[str]] = {}
    coverage_gaps: dict[pathlib.Path, set[pathlib.Path]] = {}
    pattern = re.compile(r"\.\./(?:\.\./)?tests/[\w/._-]+")
    spec_files = [p for p in SPEC_DIR.glob("*.md") if p.name != "README.md"]
    spec_files.extend(EXTRA_SPECS)
    for path in spec_files:
        text = path.read_text()
        refs = pattern.findall(text)
        resolved_refs: set[pathlib.Path] = set()
        bad = []
        for ref in refs:
            target = (path.parent / ref).resolve()
            if not target.exists():
                bad.append(ref)
                continue
            resolved_refs.add(target.relative_to(ROOT))
        if not refs or bad:
            missing[path] = bad
            continue

        spec_key = path.resolve().relative_to(ROOT)
        expected = manifest.get(spec_key, set())
        if expected:
            missing_targets = expected.difference(resolved_refs)
            if missing_targets:
                coverage_gaps[path] = missing_targets

    if stale_manifest:
        print("SPEC_COVERAGE.md references missing test targets:")
        for test_id, target in sorted(stale_manifest.items()):
            print(f"- {test_id}: {target}")
        return 1
    if missing:
        print("Spec files with missing test references:")
        for spec, refs in missing.items():
            print(f"- {spec.relative_to(ROOT)}")
            for ref in refs:
                print(f"  {ref}")
        return 1
    if coverage_gaps:
        print("Spec files missing manifest-aligned test references:")
        for spec, targets in coverage_gaps.items():
            print(f"- {spec.relative_to(ROOT)}")
            for target in sorted(targets):
                print(f"  {target}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
