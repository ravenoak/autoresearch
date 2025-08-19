# Output Format Module Specification

The output formatting module (`src/autoresearch/output_format.py`)
renders query responses in multiple formats such as Markdown, JSON,
plain text, graph views, or custom templates.

## Key behaviors

- Validate and format responses into Markdown, JSON, or plain text.
- Render a knowledge graph view with `--output graph`.
- Load and apply user-defined templates via `TemplateRegistry`.

## Traceability

- **Modules**
  - `src/autoresearch/output_format.py`
- **Tests**
  - [output_formatting.feature](../../tests/behavior/features/output_formatting.feature)
  - `../../tests/unit/test_output_format.py`
  - `../../tests/unit/test_template.py`

## Extending

Add new behaviours with accompanying feature files and reference them
under **Traceability**.
