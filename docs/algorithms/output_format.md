# Output Format

The `output_format` module adapts query responses for human or machine
consumers. It validates `QueryResponse` data and renders multiple formats.

## Formatting logic
- `OutputFormatter` ensures the input matches `QueryResponse` using Pydantic.
- Supported formats include `json`, `plain`, `markdown`, `graph`, and
  `template:<name>`.
- `TemplateRegistry` loads built in templates (`markdown`, `plain`) and
  custom ones from config or `*.tpl` files.
- Templates use `string.Template` variables like `${answer}` and
  `${metric_latency}`.

## Edge cases
- Missing templates fall back to the `markdown` template.
- Undefined template variables raise `KeyError` with available names listed.
- Invalid input raises `ValidationError` wrapped as
  `errors.ValidationError`.
- `graph` format relies on `rich.tree`; if unavailable it can be skipped.

## References
- [`output_format.py`](../../src/autoresearch/output_format.py)
- [`test_output_format.py`](../../tests/unit/test_output_format.py)

## Simulation

Automated tests confirm output format behavior.

- [Spec](../specs/output-format.md)
- [Tests](../../tests/unit/test_formattemplate_property.py)
