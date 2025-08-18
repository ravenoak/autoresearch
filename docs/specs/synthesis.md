# Synthesis utilities

Helpers for building answers and rationales with token-aware compression.

## Key behaviors

- `build_answer` combines up to the first three claim `content` values and appends the total count when more are provided.
- `build_answer` returns "No answer found for '<query>'." when no claims are supplied.
- `build_rationale` lists every claim `content` as bullet points or reports "No rationale available."
- `compress_prompt` splits on whitespace and keeps the first and last halves, inserting an ellipsis when tokens exceed the budget (`half = max(1, token_budget // 2)`).
- `compress_claims` iterates through claims, retaining those within the token budget and truncating the final overlong claim with an ellipsis.

## Traceability

- **Modules**
  - `src/autoresearch/synthesis.py`
- **Tests**
  - `../../tests/behavior/features/synthesis.feature`
