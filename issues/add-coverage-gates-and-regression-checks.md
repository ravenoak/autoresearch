# Add coverage gates and regression checks

## Context
The project currently has about 67% test coverage and lacks CI enforcement.
To reach the alpha release target, coverage thresholds and regression checks must run in CI.

## Acceptance Criteria
- Configure CI to fail when coverage drops below 90%.
- Add regression checks to ensure coverage does not decrease on new code.
- Document how to run coverage locally using `task coverage`.

## Status
Open
