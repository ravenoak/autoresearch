# Output Format Module Specification

The output formatting module (`src/autoresearch/output_format.py`)
renders query responses in multiple formats such as Markdown, JSON,
plain text, graph views, or custom templates.

## Key behaviors

- Validate and format responses into Markdown, JSON, or plain text.
- Render a knowledge graph view with `--output graph`.
- Load and apply user-defined templates via `TemplateRegistry`.

## Traceability

- Modules
  - [src/autoresearch/output_format.py][m1]
- Tests
  - [tests/behavior/features/output_formatting.feature][t1]
  - [tests/unit/test_output_format.py][t2]

[m1]: ../../src/autoresearch/output_format.py
[t1]: ../../tests/behavior/features/output_formatting.feature
[t2]: ../../tests/unit/test_output_format.py
