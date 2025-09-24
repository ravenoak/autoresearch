# Finalize search parser backends

## Context
The document parser unit tests remain guarded by `xfail` markers:
`tests/unit/test_search_parsers.py::test_extract_pdf_text`,
`tests/unit/test_search_parsers.py::test_extract_docx_text`, and
`tests/unit/test_search_parsers.py::test_search_local_file_backend`. The
September 24 unit run of `uv run --extra test pytest tests/unit -m "not
slow" -rxX` shows all three cases as XFAIL, citing flaky PDF extraction,
DOCX parsing gaps, and an incomplete local file backend. Documentation in
`docs/algorithms/search.md` advertises support for document ingestion,
while installation instructions flag optional parser extras. The mismatch
between docs, code, and tests blocks a confident 0.1.0a1 tag.

A multi-disciplinary review needs to weigh the ergonomics of bringing the
parsers into the default bundle versus clarifying optional support. The
Socratic approach should surface the minimal guarantees we can uphold in
an alpha release and the dialectical step should challenge whether the
existing heuristics suffice without real parsers.

## Dependencies
- _None_

## Acceptance Criteria
- Decide whether PDF and DOCX parsing ship in 0.1.0a1 or remain optional,
  documenting the rationale in `docs/algorithms/search.md` and
  `docs/algorithms/cache.md`.
- Implement stable parser integrations (or deterministic shims) in
  `src/autoresearch/search/parsers.py` and related helpers so the unit
  tests pass without `xfail` markers.
- Add regression coverage for failure modes (e.g., corrupted files) and
  update the tests to assert on specific parser outputs.
- Note any environment requirements in `README.md` and
  `docs/installation.md`, including extras or optional dependencies.
- Update `SPEC_COVERAGE.md` to reference the finalized parser coverage
  and record the change in `CHANGELOG.md` under Unreleased.

## Resolution
- Cross-checked the Unreleased changelog entry that links to this ticket
  and records the parser backend stabilization alongside refreshed tests,
  docs, and installation guidance.
- Verified `tests/unit/test_search_parsers.py` now asserts deterministic
  PDF, DOCX, and local file behavior without `xfail` guards and that
  `README.md`, `docs/installation.md`, and `SPEC_COVERAGE.md` describe the
  finalized coverage.
- Parser integrations and documentation now align with the 0.1.0a1 scope,
  so the issue can be archived.

## Status
Archived
