"""Placeholder steps for server commands feature."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.pending(reason="Step implementations pending")

scenarios("../features/serve_commands.feature")
