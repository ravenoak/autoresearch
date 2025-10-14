#!/usr/bin/env python
"""Verify package builds and metadata for release.

Usage:
    uv run scripts/publish_dev.py [--dry-run]

The script builds the package and verifies it can be uploaded without errors.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Build the package and verify it for release."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the package but skip uploading",
    )
    parser.add_argument(
        "--repository",
        default="testpypi",
        help="Repository name for twine upload",
    )
    args = parser.parse_args(argv)

    dist = Path("dist")
    if dist.exists():
        shutil.rmtree(dist)

    build_cmd = ["uv", "run", "--extra", "build", "python", "-m", "build"]
    if subprocess.call(build_cmd):
        return 1

    files = [str(p) for p in dist.glob("*") if p.is_file()]
    if not files:
        print("No distribution files found in 'dist'")
        return 1

    if args.dry_run:
        print("Dry run selected; skipping upload")
        return 0

    env = os.environ.copy()
    token = env.get("TWINE_API_TOKEN")
    username = env.get("TWINE_USERNAME")
    password = env.get("TWINE_PASSWORD")
    if token:
        env.setdefault("TWINE_USERNAME", "__token__")
        env.setdefault("TWINE_PASSWORD", token)
    elif not username or not password:
        print(
            "Set TWINE_API_TOKEN or both TWINE_USERNAME and TWINE_PASSWORD in the environment"
        )
        return 1

    upload_cmd = [
        "uv",
        "run",
        "twine",
        "upload",
        "--repository",
        args.repository,
        *files,
    ]
    result = subprocess.run(upload_cmd, capture_output=True, text=True, env=env)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        out = result.stdout + result.stderr
        if "403" in out or "401" in out or "Forbidden" in out or "Unauthorized" in out:
            print("Authentication failed: check your credentials")
            return 1
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
