"""
Adaptive output formatting for CLI and automation contexts.
"""
import sys
from typing import Any
from pydantic import ValidationError
from .models import QueryResponse

class OutputFormatter:
    @staticmethod
    def format(result: Any, format_type: str) -> None:
        """Validate and print result as JSON or Markdown based on format_type."""
        try:
            response = result if isinstance(result, QueryResponse) else QueryResponse.model_validate(result)
        except ValidationError as exc:  # pragma: no cover - handled by caller
            raise ValueError(f"Invalid response: {exc}") from exc

        if format_type.lower() == "json":
            sys.stdout.write(response.model_dump_json(indent=2) + "\n")
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

