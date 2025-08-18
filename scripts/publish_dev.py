#!/usr/bin/env python
"""Publish a development build to the TestPyPI repository."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Build the package and upload it to TestPyPI using ``twine``."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the package but skip uploading",
    )
    args = parser.parse_args(argv)

    dist = Path("dist")
    if dist.exists():
        shutil.rmtree(dist)

    build_cmd = ["uv", "run", "python", "-m", "build"]
    if subprocess.call(build_cmd):
        return 1

    files = [str(p) for p in dist.glob("*") if p.is_file()]
    if not files:
        print("No distribution files found in 'dist'")
        return 1

    if args.dry_run:
        print("Dry run selected; skipping upload")
        return 0

    upload_cmd = ["uv", "run", "twine", "upload", "--repository", "testpypi", *files]
    return subprocess.call(upload_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
