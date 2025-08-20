# Optimize task install dependencies

## Context
Running `task install` synchronizes all extras, triggering multi-gigabyte
downloads for GPU and UI packages. This slows developer onboarding and can
exceed container limits. A leaner default install using the `dev-minimal`
extras would improve setup time while still enabling linting and tests.

## Acceptance Criteria
- `task install` installs only the `dev-minimal` extras by default.
- Documentation notes how to install heavy extras on demand.
- scripts/codex_setup.sh reflects the streamlined dependency set.

## Status
Archived
