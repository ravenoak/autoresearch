# Module Specifications

This directory contains specifications for Autoresearch modules.
Each spec summarizes the module's responsibilities and links to
behavior-driven development (BDD) feature files that validate the
documented behaviour.

## Mapping specs to tests

- Specs reference the feature files in `tests/behavior/features/` that
  exercise the described behavior.
- When adding new behaviour or features, create or update a feature file
  and link to it from the relevant spec.

## Extending specs

1. Create a new spec file in this directory named after the module.
2. Describe the module's purpose and key workflows.
3. List the associated feature files under a **Related tests** section
   using relative links (e.g., `../../tests/behavior/features/example.feature`).
4. Run `task verify` to ensure the new documentation and tests pass.
