"""Adaptive output formatting for CLI and automation contexts.

This module provides functionality to format query responses in different formats
based on the context in which they are being displayed. It supports multiple output
formats including:

- JSON: Structured format suitable for programmatic consumption
- Plain text: Simple text format for basic terminal output
- Markdown: Rich text format with headings and lists for documentation
- Custom templates: User-defined templates for specialized output formats

The formatting system validates that the input conforms to the expected QueryResponse
structure before formatting, ensuring consistent output regardless of the source of
the data.

Typical usage:
    ```python
    from autoresearch.output_format import OutputFormatter

    # Format a query response as Markdown
    OutputFormatter.format(query_result, "markdown")

    # Format a query response as JSON
    OutputFormatter.format(query_result, "json")

    # Format a query response as plain text
    OutputFormatter.format(query_result, "plain")

    # Format a query response using a custom template
    OutputFormatter.format(query_result, "template:my_template")
    ```
"""

import os
import sys
import string
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError
from .models import QueryResponse
from .errors import ValidationError as AutoresearchValidationError
from .config import ConfigLoader
from .logging_utils import get_logger

log = get_logger(__name__)


class FormatTemplate(BaseModel):
    """A template for formatting query responses.

    This class represents a format template that can be used to format QueryResponse
    objects. It uses the string.Template syntax for variable substitution, where
    variables are referenced as ${variable_name} in the template text.

    Attributes:
        name: The name of the template.
        description: An optional description of the template.
        template: The template text with variable placeholders.
    """
    name: str
    description: Optional[str] = None
    template: str

    def render(self, response: QueryResponse) -> str:
        """Render the template with the given QueryResponse.

        Args:
            response: The QueryResponse object to format.

        Returns:
            The rendered template as a string.

        Raises:
            KeyError: If a variable referenced in the template is not available in the response.
        """
        # Create a dictionary of variables from the response
        variables = {
            "answer": response.answer,
            "citations": "\n".join([f"- {c}" for c in response.citations]),
            "reasoning": "\n".join([f"- {r}" for r in response.reasoning]),
            "metrics": "\n".join([f"- {k}: {v}" for k, v in response.metrics.items()]),
        }

        # Add individual metrics as variables
        for k, v in response.metrics.items():
            variables[f"metric_{k}"] = str(v)

        # Use string.Template for variable substitution
        template = string.Template(self.template)
        try:
            return template.substitute(variables)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise KeyError(
                f"Missing required variable '{missing_var}' for format template '{self.name}'. "
                f"Available variables: {', '.join(variables.keys())}"
            )


class TemplateRegistry:
    """Registry for format templates.

    This class provides a centralized registry for storing and retrieving format templates.
    It maintains a dictionary of templates indexed by name and provides methods for
    registering, retrieving, and loading templates from configuration and files.
    """
    _templates: Dict[str, FormatTemplate] = {}
    _default_templates: Dict[str, Dict[str, Any]] = {
        "markdown": {
            "name": "markdown",
            "description": "Markdown format with headings and lists",
            "template": """# Answer
${answer}

## Citations
${citations}

## Reasoning
${reasoning}

## Metrics
${metrics}
"""
        },
        "plain": {
            "name": "plain",
            "description": "Simple text format for basic terminal output",
            "template": """Answer:
${answer}

Citations:
${citations}

Reasoning:
${reasoning}

Metrics:
${metrics}
"""
        }
    }

    @classmethod
    def register(cls, template: FormatTemplate) -> None:
        """Register a format template in the registry.

        Args:
            template: The template to register.
        """
        cls._templates[template.name] = template
        log.debug(f"Registered format template: {template.name}")

    @classmethod
    def get(cls, name: str) -> FormatTemplate:
        """Get a format template by name.

        Args:
            name: The name of the template.

        Returns:
            The format template.

        Raises:
            KeyError: If the template is not found.
        """
        if name not in cls._templates:
            # If the template is not registered, try to load it from the default templates
            if name in cls._default_templates:
                cls.register(FormatTemplate(**cls._default_templates[name]))
            else:
                # Try to load from template directory
                cls._load_template_from_file(name)

            if name not in cls._templates:
                raise KeyError(f"Format template '{name}' not found")

        return cls._templates[name]

    @classmethod
    def _load_template_from_file(cls, name: str) -> None:
        """Load a template from a file.

        Args:
            name: The name of the template.
        """
        config = ConfigLoader().config
        template_dir = getattr(config, "template_dir", None)

        if not template_dir:
            # Check common locations
            locations = [
                Path.cwd() / "templates",
                Path.home() / ".config" / "autoresearch" / "templates",
                Path("/etc/autoresearch/templates"),
            ]

            for loc in locations:
                if loc.exists() and loc.is_dir():
                    template_dir = str(loc)
                    break

        if not template_dir:
            return

        template_path = Path(template_dir) / f"{name}.tpl"

        if not template_path.exists():
            return

        try:
            with open(template_path, "r") as f:
                template_text = f.read()

            # First line can be a description
            lines = template_text.split("\n")
            description = None
            if lines and lines[0].startswith("#"):
                description = lines[0][1:].strip()
                template_text = "\n".join(lines[1:])

            template = FormatTemplate(
                name=name,
                description=description,
                template=template_text
            )
            cls.register(template)
        except Exception as e:
            log.warning(f"Failed to load template from {template_path}: {e}")

    @classmethod
    def load_from_config(cls) -> None:
        """Load templates from configuration."""
        config = ConfigLoader().config
        templates = getattr(config, "output_templates", {})

        for name, template_data in templates.items():
            if isinstance(template_data, dict) and "template" in template_data:
                try:
                    template = FormatTemplate(name=name, **template_data)
                    cls.register(template)
                except Exception as e:
                    log.warning(f"Failed to load template '{name}' from config: {e}")


class OutputFormatter:
    """Utility class for formatting query responses in various output formats.

    This class provides static methods to format QueryResponse objects into
    different output formats suitable for various contexts, such as CLI output,
    API responses, or documentation.

    The class validates that the input conforms to the QueryResponse structure
    before formatting, ensuring consistent output regardless of the source of
    the data.

    Supported formats:
        - json: Structured JSON format for programmatic consumption
        - plain/text: Simple text format for basic terminal output
        - markdown (default): Rich text format with headings and lists
        - template:<name>: Custom template format (e.g., "template:html")
    """

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the formatter by loading templates from configuration."""
        try:
            TemplateRegistry.load_from_config()
        except Exception as e:
            log.warning(f"Failed to load templates from config: {e}")
    @classmethod
    def format(cls, result: Any, format_type: str = "markdown") -> None:
        """Validate and format a query result to the specified output format.

        This method takes a query result (either a QueryResponse object or a
        dictionary that can be converted to one) and formats it according to
        the specified format type. The formatted output is written directly
        to stdout.

        The method first validates that the input conforms to the QueryResponse
        structure, then formats it according to the specified format type.

        Args:
            result (Any): The query result to format. Can be a QueryResponse object
                or a dictionary that can be converted to one.
            format_type (str, optional): The output format to use. Supported values:
                - "json": Structured JSON format
                - "plain" or "text": Simple text format
                - "markdown": Markdown format with headings and lists
                - "template:<name>": Custom template format (e.g., "template:html")
                Defaults to "markdown".

        Raises:
            AutoresearchValidationError: If the result cannot be validated as a
                QueryResponse object.
            KeyError: If the specified template is not found.

        Note:
            This method writes directly to stdout and does not return a value.
            For programmatic use where you need the formatted string, you may
            need to capture stdout or modify this method to return the string.
        """
        # Initialize templates if needed
        cls._initialize()

        try:
            response = (
                result
                if isinstance(result, QueryResponse)
                else QueryResponse.model_validate(result)
            )
        except ValidationError as exc:  # pragma: no cover - handled by caller
            raise AutoresearchValidationError(f"Invalid response format", cause=exc) from exc

        fmt = format_type.lower()

        if fmt == "json":
            sys.stdout.write(response.model_dump_json(indent=2) + "\n")
        elif fmt.startswith("template:"):
            # Custom template format
            template_name = fmt.split(":", 1)[1]
            try:
                template = TemplateRegistry.get(template_name)
                output = template.render(response)
                sys.stdout.write(output + "\n")
            except KeyError as e:
                log.error(f"Template error: {e}")
                # Fall back to markdown if template not found
                log.warning(f"Template '{template_name}' not found, falling back to markdown")
                cls.format(result, "markdown")
        elif fmt in {"plain", "text"}:
            try:
                template = TemplateRegistry.get("plain")
                output = template.render(response)
                sys.stdout.write(output + "\n")
            except KeyError:
                # Fall back to hardcoded plain format if template not found
                sys.stdout.write("Answer:\n")
                sys.stdout.write(response.answer + "\n\n")
                sys.stdout.write("Citations:\n")
                for c in response.citations:
                    sys.stdout.write(f"{c}\n")
                sys.stdout.write("\nReasoning:\n")
                for r in response.reasoning:
                    sys.stdout.write(f"{r}\n")
                sys.stdout.write("\nMetrics:\n")
                for k, v in response.metrics.items():
                    sys.stdout.write(f"{k}: {v}\n")
        else:
            # Markdown output (default)
            try:
                template = TemplateRegistry.get("markdown")
                output = template.render(response)
                sys.stdout.write(output + "\n")
            except KeyError:
                # Fall back to hardcoded markdown format if template not found
                sys.stdout.write("# Answer\n")
                sys.stdout.write(response.answer + "\n\n")
                sys.stdout.write("## Citations\n")
                for c in response.citations:
                    sys.stdout.write(f"- {c}\n")
                sys.stdout.write("\n## Reasoning\n")
                for r in response.reasoning:
                    sys.stdout.write(f"- {r}\n")
                sys.stdout.write("\n## Metrics\n")
                for k, v in response.metrics.items():
                    sys.stdout.write(f"- **{k}**: {v}\n")
