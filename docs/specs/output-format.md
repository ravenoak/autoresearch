# Output Format Module Specification

## Overview

The output formatting module (`src/autoresearch/output_format.py`) renders
query responses in formats such as Markdown, JSON, plain text, graph views, or
custom templates.

## Algorithms

### Markdown renderer

1. Validate or construct a `QueryResponse` object.
2. Load the markdown template from the registry or a hard-coded fallback.
3. Substitute answer, citations, reasoning, and metrics into the template.
4. Emit the rendered string with sections: Answer, Citations, Reasoning, and
   Metrics.

**Invariants and complexity**

- Runs in `O(n)` time relative to the length of formatted fields.
- Order of sections is fixed and appears exactly once.
- Any field containing control characters, zero-width spaces, or
  whitespace-only text is rendered inside a fenced `text` block with
  `\uXXXX` escapes so the payload cannot collapse or truncate in
  Markdown viewers.
- Output is deterministic and contains no ANSI escape sequences.

### JSON renderer

1. Validate or construct a `QueryResponse` object.
2. Serialize the model with `model_dump_json(indent=2)`.
3. Write the resulting string to stdout.

**Invariants and complexity**

- Runs in `O(n)` time where `n` is the serialized length.
- Field order follows the pydantic model definition.
- Strings are emitted verbatim (aside from JSON-required escaping) so
  byte-for-byte payloads survive round-trips without trimming or
  normalisation.
- Output contains only UTF-8 text and no ANSI codes.

### Graph renderer

1. Build a `rich.tree.Tree` rooted at "Knowledge Graph".
2. Add an "Answer" node containing the answer text.
3. Nest "Citations" beneath the answer and add each citation as a child.
4. Add sibling branches for "Reasoning" and "Metrics" with their entries.
5. Render the tree using a `rich.console.Console` and write it to stdout.

**Invariants and complexity**

- Runs in `O(n)` nodes where `n` is the total items across fields.
- Tree always has a single root labeled "Knowledge Graph".
- Rendering is deterministic and free of color sequences.

### Template renderer

1. Parse the format specifier to obtain the template name.
2. Retrieve the template from the registry, loading defaults on first use.
3. Construct a variable map from response fields and individual metrics.
4. Substitute variables via `string.Template`.
5. Write the result to stdout or fall back to markdown if lookup fails.

**Invariants and complexity**

- Runs in `O(n)` where `n` is the template size plus variable count.
- Missing variables raise `KeyError` with available placeholder names.
- Template lookup is deterministic; absence triggers markdown fallback.

## Invariants

- Every renderer is deterministic for a given `QueryResponse`.
- Unknown format strings fall back to markdown output.

## Proof Sketch

Assume `render_output` receives a response object and a format specifier.
Each renderer maps the response to a deterministic string representation.
The dispatch table binds formats to renderer functions, so every supported
format resolves to a total function. Fallback to plain text ensures totality
for unknown formats.

## Simulation Expectations

BDD scenarios and unit tests exercise Markdown, JSON, and graph renderers.
The refreshed property suite verifies that control characters, zero-width
spaces, and whitespace-only strings survive JSON round-trips and render in
Markdown as fenced blocks with `\uXXXX` escapes. The behaviour feature now
asserts that the CLI surfaces the escaped blocks instead of truncating or
silently dropping characters. On 2025-10-05, `pytest
tests/unit/test_output_formatter_property.py` and the updated behaviour
scenario passed under `uv run --extra test pytest`.

## Traceability


- Modules
  - [src/autoresearch/output_format.py][m1]
- Tests
  - [tests/behavior/features/output_formatting.feature][t1]
  - [tests/unit/test_output_formatter_property.py][t2]

[m1]: ../../src/autoresearch/output_format.py
[t1]: ../../tests/behavior/features/output_formatting.feature
[t2]: ../../tests/unit/test_output_formatter_property.py
