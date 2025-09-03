# Spec-Driven Development

This guide outlines how to write and maintain module specifications.

## Workflow

1. Copy `spec_template.md` into `docs/specs/`.
2. Fill every section: overview, algorithms, invariants, proof sketch,
   simulation expectations, and traceability.
3. Link to implementation modules and tests using relative paths.
4. Stage the spec and run `pre-commit run --files <spec>` to invoke the
   spec check hook.
5. Implement code and tests.
6. Run `task check` for quick validation.
7. Run `task verify` before committing.

## Maintenance

- Update specs when behavior or interfaces change.
- Keep links to code and tests current.
- Run `uv run mkdocs build` to validate documentation.
- Use simulations to explore edge cases and assumptions.

## Review

- Discuss assumptions and invariants with peers before merging code.
- Reject changes that lack matching spec updates.
