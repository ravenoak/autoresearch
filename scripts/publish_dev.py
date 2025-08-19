#!/usr/bin/env python
"""Publish a development build to the TestPyPI repository.

Usage:
    uv run scripts/publish_dev.py [--dry-run]

Required environment variables:
    TWINE_USERNAME -- TestPyPI username
    TWINE_PASSWORD -- TestPyPI password

The script builds the package and uploads it to TestPyPI using ``twine``.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import os
import sys
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

    if not os.getenv("TWINE_USERNAME") or not os.getenv("TWINE_PASSWORD"):
        print("TWINE_USERNAME and TWINE_PASSWORD must be set in the environment")
        return 1

    upload_cmd = ["uv", "run", "twine", "upload", "--repository", "testpypi", *files]
    result = subprocess.run(upload_cmd, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        if "403" in result.stdout or "403" in result.stderr:
            print("Upload failed: received HTTP 403 from repository")
            return 1
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
