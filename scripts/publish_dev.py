#!/usr/bin/env python
"""Publish a development build to the TestPyPI repository."""
from __future__ import annotations
import subprocess
import sys

CMD = [
    "poetry",
    "publish",
    "--build",
    "--repository",
    "testpypi",
]

sys.exit(subprocess.call(CMD))
