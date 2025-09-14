# Development Workflow

This guide summarizes the development process and specification workflow.

## Specification workflow
- Begin new modules by drafting a spec using the template in the
  inspirational documents.
- Document algorithms, invariants, and proofs for each module.
- Add a **Traceability** section linking modules and tests.

## Contribution steps
- Implement code and spec together on a feature branch.
- Run `task check` early and `task verify` before submitting a pull request.
- Build documentation with `uv run mkdocs build` to ensure it compiles.
