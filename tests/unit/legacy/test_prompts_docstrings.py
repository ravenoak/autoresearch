# mypy: ignore-errors
import inspect
from autoresearch.agents.prompts import (
    PromptTemplate,
    PromptTemplateRegistry,
    get_prompt_template,
    render_prompt,
)


def test_module_docstring():
    """Test that the module has a comprehensive docstring."""
    import autoresearch.agents.prompts as prompts_module

    # Check that the module has a docstring
    assert prompts_module.__doc__ is not None, "Module should have a docstring"

    # Check that the docstring is comprehensive
    docstring = prompts_module.__doc__
    assert len(docstring.strip().split("\n")) >= 3, (
        "Module docstring should have at least 3 lines"
    )
    assert "This module provides" in docstring, (
        "Module docstring should explain what the module provides"
    )


def test_class_docstrings():
    """Test that classes have comprehensive docstrings."""
    from pydantic import BaseModel

    classes = [PromptTemplate, PromptTemplateRegistry]

    for cls in classes:
        # Check that the class has a docstring
        assert cls.__doc__ is not None, f"{cls.__name__} should have a docstring"

        # Check that the docstring is comprehensive
        docstring = cls.__doc__
        assert len(docstring.strip().split("\n")) >= 1, (
            f"{cls.__name__} docstring should have at least 1 line"
        )

        # For Pydantic models, only check methods defined in the class itself, not inherited from BaseModel
        if issubclass(cls, BaseModel):
            # Get methods defined in the class itself
            class_methods = {
                name: method
                for name, method in inspect.getmembers(cls, inspect.isfunction)
                if method.__qualname__.startswith(cls.__name__)
            }
        else:
            # Get all methods
            class_methods = {
                name: method
                for name, method in inspect.getmembers(cls, inspect.isfunction)
            }

        # Check methods have docstrings
        for name, method in class_methods.items():
            # Skip private methods
            if name.startswith("_"):
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
            if (
                sig.return_annotation is not inspect.Signature.empty
                and sig.return_annotation is not None
            ):
                assert "Returns:" in method_doc, (
                    f"{cls.__name__}.{name} docstring should have a Returns section"
                )

            # Check for Raises section if the method can raise exceptions
            if "raise" in inspect.getsource(method):
                assert "Raises:" in method_doc, (
                    f"{cls.__name__}.{name} docstring should have a Raises section"
                )


def test_function_docstrings():
    """Test that functions have comprehensive docstrings."""
    functions = [get_prompt_template, render_prompt]

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
        if (
            sig.return_annotation is not inspect.Signature.empty
            and sig.return_annotation is not None
        ):
            assert "Returns:" in docstring, (
                f"{func.__name__} docstring should have a Returns section"
            )

        # Check for Raises section if the function can raise exceptions
        if "raise" in inspect.getsource(func):
            assert "Raises:" in docstring, (
                f"{func.__name__} docstring should have a Raises section"
            )
