"""Simulate template rendering and validation for `OutputFormatter`.

Problem: demonstrate how custom templates render `QueryResponse` data and how
validation errors surface. Alternative approaches include using
`OutputFormatter.format` with dictionaries for automatic validation.
"""

from autoresearch.output_format import OutputFormatter, FormatTemplate, TemplateRegistry
from autoresearch.models import QueryResponse
from autoresearch.errors import ValidationError as AutoresearchValidationError

# Register a custom template with a metric placeholder.
TemplateRegistry.register(
    FormatTemplate(
        name="demo",
        description="Demo template",
        template="Answer: ${answer}\nMetric: ${metric_latency}\n",
    )
)

resp = QueryResponse(answer="ok", citations=[], reasoning=[], metrics={"latency": 1})

# Render using the custom template.
OutputFormatter.format(resp, "template:demo")

# Trigger a validation error using an incomplete dictionary.
try:
    OutputFormatter.format({"answer": "oops"}, "json")
except AutoresearchValidationError as exc:  # pragma: no cover - example
    print(f"Validation failed: {exc}")
