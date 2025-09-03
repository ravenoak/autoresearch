# Spec-Driven Development

This guide outlines how to write and maintain module specifications.

## Writing Specs

- Copy `spec_template.md` into `docs/specs/`.
- Fill all sections: overview, algorithms, invariants, proof sketch, simulation
  expectations, and traceability.

## Maintenance

- Update specs when behavior or interfaces change.
- Keep links to code and tests current.
- Run `uv run mkdocs build` to validate documentation.
- Use simulations to explore edge cases and assumptions.

## Review

- Discuss assumptions and invariants with peers before merging code.
- Reject changes that lack matching spec updates.
