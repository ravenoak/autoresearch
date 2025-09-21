#!/usr/bin/env python3
"""Validate prerequisites for running ``task verify`` with optional extras.

The script imports representative packages for each requested extra and
optionally verifies that GPU wheels are hydrated. Run it from the repository
root:

```
uv run python scripts/check_full_verify_prereqs.py
uv run python scripts/check_full_verify_prereqs.py --extras "nlp ui"
```

Providing ``--extras`` checks only the specified groups. Without the flag the
Taskfile ``ALL_EXTRAS`` set is used, ensuring the preflight mirrors the heavy
``task verify`` invocation.
"""

from __future__ import annotations

import argparse
import importlib
import shlex
import sys
from pathlib import Path
from typing import Iterable, Sequence

from packaging.utils import canonicalize_name, parse_wheel_filename

DEFAULT_EXTRAS: tuple[str, ...] = (
    "nlp",
    "ui",
    "vss",
    "git",
    "distributed",
    "analysis",
    "llm",
    "parsers",
    "gpu",
)

EXTRA_IMPORT_PROBES: dict[str, tuple[str, ...]] = {
    "nlp": ("spacy",),
    "ui": ("streamlit",),
    "vss": ("duckdb_extension_vss",),
    "git": ("git",),
    "distributed": ("ray",),
    "analysis": ("polars",),
    "llm": ("fastembed",),
    "parsers": ("docx",),
    "gpu": ("bertopic",),
}

GPU_WHEEL_REQUIREMENTS: tuple[str, ...] = (
    "bertopic",
    "pynndescent",
    "scipy",
    "lmstudio",
)

REPO_ROOT = Path(__file__).resolve().parent.parent
GPU_WHEEL_DIR = REPO_ROOT / "wheels" / "gpu"


def _parse_extras(raw_value: str | None) -> list[str]:
    """Return the requested extras, defaulting to the Taskfile ``ALL_EXTRAS``."""

    if raw_value is None:
        return list(DEFAULT_EXTRAS)

    try:
        extras = shlex.split(raw_value)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise SystemExit(f"Failed to parse --extras: {exc}") from exc

    deduped = []
    for extra in extras:
        cleaned = extra.strip()
        if not cleaned:
            continue
        if cleaned not in deduped:
            deduped.append(cleaned)
    return deduped


def _validate_imports(extras: Iterable[str]) -> list[str]:
    """Attempt to import representative modules for each requested extra."""

    errors: list[str] = []
    for extra in extras:
        probes = EXTRA_IMPORT_PROBES.get(extra)
        if probes is None:
            errors.append(f"Unknown extra '{extra}'.")
            continue
        for module_name in probes:
            try:
                importlib.import_module(module_name)
            except ModuleNotFoundError as exc:
                errors.append(
                    "Extra '%s' requires module '%s', but import failed: %s"
                    % (extra, module_name, exc)
                )
    return errors


def _validate_gpu_wheels(directory: Path, required: Sequence[str]) -> list[str]:
    """Ensure ``wheels/gpu`` contains the documented wheel archives."""

    errors: list[str] = []
    if not directory.exists():
        return [
            (
                "GPU wheels directory '%s' is missing. Hydrate it per "
                "wheels/gpu/README.md."
            )
            % directory
        ]

    found = {canonicalize_name(name): False for name in required}
    wheel_files = sorted(directory.glob("*.whl"))

    if not wheel_files:
        return [
            (
                "No wheel files found in '%s'. Populate it according to "
                "wheels/gpu/README.md."
            )
            % directory
        ]

    for wheel in wheel_files:
        try:
            distribution, _, _, _ = parse_wheel_filename(wheel.name)
        except ValueError:
            # Ignore unexpected files; they may be auxiliary downloads.
            continue
        normalized = canonicalize_name(distribution)
        if normalized in found:
            found[normalized] = True

    missing = [name for name, present in found.items() if not present]
    if missing:
        errors.append(
            (
                "Missing wheel(s) %s in '%s'. Populate the directory per "
                "wheels/gpu/README.md."
            )
            % (", ".join(missing), directory)
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that optional extras are ready for task verify."
    )
    parser.add_argument(
        "--extras",
        metavar="EXTRAS",
        help=(
            "Space-separated extras to validate. Defaults to the Taskfile "
            "ALL_EXTRAS set."
        ),
    )
    args = parser.parse_args()

    extras = _parse_extras(args.extras)
    errors = _validate_imports(extras)

    if "gpu" in extras:
        errors.extend(_validate_gpu_wheels(GPU_WHEEL_DIR, GPU_WHEEL_REQUIREMENTS))

    if errors:
        print("Preflight checks failed:", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1

    if extras:
        print(
            "All requested extras passed import and wheel preflight checks: %s"
            % ", ".join(extras)
        )
    else:
        print("No extras requested; nothing to validate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
