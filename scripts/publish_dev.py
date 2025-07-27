#!/usr/bin/env python
"""Publish a development build to the TestPyPI repository."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Build the package and upload it to TestPyPI using ``twine``."""

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

    upload_cmd = ["uv", "run", "twine", "upload", "--repository", "testpypi", *files]
    return subprocess.call(upload_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
