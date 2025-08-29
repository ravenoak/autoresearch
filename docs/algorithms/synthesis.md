# Synthesis

Functions that craft answers and rationales from claims.

## Answer and rationale
- `build_answer` concatenates up to three claim contents.
- `build_rationale` lists all claims as bullet points.

## Compression
- `compress_prompt` preserves start and end tokens within a budget.
- `compress_claims` trims claim texts to fit token limits.

## References
- [`synthesis.py`](../../src/autoresearch/synthesis.py)
- [../specs/synthesis.md](../specs/synthesis.md)
