"""Adaptive output formatting for CLI and automation contexts.

This module provides functionality to format query responses in different formats
based on the context in which they are being displayed. It supports multiple output
formats including:

- JSON: Structured format suitable for programmatic consumption
- Plain text: Simple text format for basic terminal output
- Markdown: Rich text format with headings and lists for documentation

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
    ```
"""

import sys
from typing import Any
from pydantic import ValidationError
from .models import QueryResponse
from .errors import ValidationError as AutoresearchValidationError


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
    """
    @staticmethod
    def format(result: Any, format_type: str = "markdown") -> None:
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
                - Any other value (including "markdown"): Markdown format
                Defaults to "markdown".

        Raises:
            AutoresearchValidationError: If the result cannot be validated as a
                QueryResponse object.

        Note:
            This method writes directly to stdout and does not return a value.
            For programmatic use where you need the formatted string, you may
            need to capture stdout or modify this method to return the string.
        """
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
        elif fmt in {"plain", "text"}:
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
            # Markdown output
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
