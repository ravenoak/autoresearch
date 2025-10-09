"""Type hints for :mod:`tests.unit.test_main_app` to satisfy strict mypy."""

from typing import Any


class TestMainApp:
    """Stubbed test class for CLI app smoke tests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


class TestCliEvaluation:
    """Stubbed test class for evaluation CLI smoke tests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


class TestDistributedExecutors:
    """Stubbed test class for distributed executor utilities."""

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


__all__ = [
    "TestMainApp",
    "TestCliEvaluation",
    "TestDistributedExecutors",
]
