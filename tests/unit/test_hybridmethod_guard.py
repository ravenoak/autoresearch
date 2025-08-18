import pytest

from autoresearch.search.core import hybridmethod


class NoGetInstance:
    @hybridmethod
    def foo(self) -> str:
        return "foo"


def test_hybridmethod_requires_get_instance() -> None:
    with pytest.raises(AttributeError, match="get_instance"):
        NoGetInstance.foo()


class WithGetInstance:
    _instance: "WithGetInstance | None" = None

    @classmethod
    def get_instance(cls) -> "WithGetInstance":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @hybridmethod
    def foo(self, value: int) -> int:
        self.value = value
        return self.value


def test_hybridmethod_class_and_instance_calls() -> None:
    obj = WithGetInstance()
    assert obj.foo(1) == 1
    assert WithGetInstance.foo(2) == 2
