"""Custom template tests referencing documentation.

See `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

from autoresearch.output_format import FormatTemplate, TemplateRegistry
from autoresearch.models import QueryResponse


def test_custom_template_render() -> None:
    template = FormatTemplate(name="t", template="A:${answer}")
    TemplateRegistry.register(template)
    resp = QueryResponse(answer="hi", citations=[], reasoning=[], metrics={})
    assert TemplateRegistry.get("t").render(resp) == "A:hi"
