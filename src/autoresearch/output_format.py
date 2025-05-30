"""
Adaptive output formatting for CLI and automation contexts.
"""
import sys
import json
from .models import QueryResponse

class OutputFormatter:
    @staticmethod
    def format(result: QueryResponse, format_type: str) -> None:
        """Print result as JSON or Markdown based on format_type."""
        if format_type.lower() == "json":
            sys.stdout.write(result.json(indent=2) + "\n")
        else:
            # Markdown output
            sys.stdout.write("# Answer\n")
            sys.stdout.write(result.answer + "\n\n")
            sys.stdout.write("## Citations\n")
            for c in result.citations:
                sys.stdout.write(f"- {c}\n")
            sys.stdout.write("\n## Reasoning\n")
            for r in result.reasoning:
                sys.stdout.write(f"- {r}\n")
            sys.stdout.write("\n## Metrics\n")
            for k, v in result.metrics.items():
                sys.stdout.write(f"- **{k}**: {v}\n")

