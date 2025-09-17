# Documentation Guidelines

These instructions apply to files in the `docs/` directory.

## Snapshot
- **Purpose:** project documentation and references.
- **Primary language:** Markdown.
- **Key outputs:** user guides, specifications, and design docs.

## Setup
- Preview locally with `uv run mkdocs serve`.
- Run `task docs` (or `uv run --extra docs mkdocs build`) to verify docs
  compile without errors.

## Conventions
- Provide a working URL or relative path for every citation.
- Use inline links or reference-style footnotes.
- `docs/inspirational_docs/` materials are for ideation only and must not be
  cited.
- Cite external research from `docs/external_research_papers/` or other
  verified sources.
- Write Markdown with a single `#` heading at the top.
- Wrap lines at 80 characters.
- Use `-` for unordered lists and leave a blank line around headings.
- Avoid committing binary assets; prefer SVG or text-based diagrams.
- When applying the current date, derive it from the system time.

## Reasoning and Continuous Improvement
- Question assumptions, compare sources, and clarify rationale in prose.
- Update documentation when workflows change and note lessons learned.

## AGENTS.md Compliance
- Scope: `docs/` directory; nested `AGENTS.md` files override these rules.
- This AGENTS.md follows the [AGENTS.md spec](https://gist.github.com).
