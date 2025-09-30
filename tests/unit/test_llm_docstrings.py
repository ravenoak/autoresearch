import inspect
from autoresearch.llm import (
    LLMAdapter,
    LLMFactory,
    get_llm_adapter,
    DummyAdapter,
    LMStudioAdapter,
    OpenAIAdapter,
)
from autoresearch.llm.token_counting import (
    TokenCountingAdapter,
    count_tokens,
    with_token_counting,
)


def test_module_docstrings() -> None:
    """Test that all llm modules have comprehensive docstrings."""
    import autoresearch.llm as llm_module
    import autoresearch.llm.adapters as adapters_module
    import autoresearch.llm.registry as registry_module
    import autoresearch.llm.token_counting as token_counting_module

    modules = [
        (llm_module, "llm"),
        (adapters_module, "adapters"),
        (registry_module, "registry"),
        (token_counting_module, "token_counting"),
    ]

    for module, name in modules:
        # Check that the module has a docstring
        assert module.__doc__ is not None, f"{name} module should have a docstring"

        # Check that the docstring is comprehensive
        docstring = module.__doc__
        assert len(docstring.strip().split("\n")) >= 1, (
            f"{name} module docstring should have at least 1 line"
        )

        # For all modules except __init__, check for more comprehensive docstrings
        if name != "llm":
            assert len(docstring.strip().split("\n")) >= 2, (
                f"{name} module docstring should have at least 2 lines"
            )
            assert (
                "This module" in docstring
                or "Module for" in docstring
                or "Provides" in docstring
            ), f"{name} module docstring should explain what the module provides"


def test_class_docstrings() -> None:
    """Test that classes have comprehensive docstrings."""
    classes = [
        LLMAdapter,
        LLMFactory,
        DummyAdapter,
        LMStudioAdapter,
        OpenAIAdapter,
        TokenCountingAdapter,
    ]

    for cls in classes:
        # Check that the class has a docstring
        assert cls.__doc__ is not None, f"{cls.__name__} should have a docstring"

        # Check that the docstring is comprehensive
        docstring = cls.__doc__
        assert len(docstring.strip().split("\n")) >= 1, (
            f"{cls.__name__} docstring should have at least 1 line"
        )

        # Get methods defined in the class itself
        class_methods = {
            name: method
            for name, method in inspect.getmembers(cls, inspect.isfunction)
            if method.__qualname__.startswith(cls.__name__)
        }

        # Check methods have docstrings
        for name, method in class_methods.items():
            # Skip private methods
            if name.startswith("_") and not name == "__init__":
                continue

            assert method.__doc__ is not None, (
                f"{cls.__name__}.{name} should have a docstring"
            )

            # Check that the method docstring is comprehensive
            method_doc = method.__doc__
            assert len(method_doc.strip().split("\n")) >= 1, (
                f"{cls.__name__}.{name} docstring should have at least 1 line"
            )

            # Check for Args section if the method has parameters
            sig = inspect.signature(method)
            params = [
                p
                for p in sig.parameters.values()
                if p.name != "self" and p.name != "cls"
            ]
            if params:
                assert "Args:" in method_doc, (
                    f"{cls.__name__}.{name} docstring should have an Args section"
                )

            # Check for Returns section if the method returns something
            # Skip __init__ methods as they implicitly return None
            if (
                sig.return_annotation is not inspect.Signature.empty
                and sig.return_annotation is not None
                and name != "__init__"
            ):
                assert "Returns:" in method_doc, (
                    f"{cls.__name__}.{name} docstring should have a Returns section"
                )

            # Check for Raises section if the method can raise exceptions
            if "raise" in inspect.getsource(method):
                assert "Raises:" in method_doc, (
                    f"{cls.__name__}.{name} docstring should have a Raises section"
                )


def test_function_docstrings() -> None:
    """Test that functions have comprehensive docstrings."""
    functions = [get_llm_adapter, count_tokens, with_token_counting]

    for func in functions:
        # Check that the function has a docstring
        assert func.__doc__ is not None, f"{func.__name__} should have a docstring"

        # Check that the docstring is comprehensive
        docstring = func.__doc__
        assert len(docstring.strip().split("\n")) >= 1, (
            f"{func.__name__} docstring should have at least 1 line"
        )

        # Check for Args section if the function has parameters
        sig = inspect.signature(func)
        params = [
            p for p in sig.parameters.values() if p.name != "self" and p.name != "cls"
        ]
        if params:
            assert "Args:" in docstring, (
                f"{func.__name__} docstring should have an Args section"
            )

        # Check for Returns section if the function returns something
        # For context managers, check for Yields section instead
        if (
            sig.return_annotation is not inspect.Signature.empty
            and sig.return_annotation is not None
        ):
            if "@contextmanager" in inspect.getsource(
                func
            ) or "yield" in inspect.getsource(func):
                assert "Yields:" in docstring, (
                    f"{func.__name__} docstring should have a Yields section"
                )
            else:
                assert "Returns:" in docstring, (
                    f"{func.__name__} docstring should have a Returns section"
                )

        # Check for Raises section if the function can raise exceptions
        if "raise" in inspect.getsource(func):
            assert "Raises:" in docstring, (
                f"{func.__name__} docstring should have a Raises section"
            )
