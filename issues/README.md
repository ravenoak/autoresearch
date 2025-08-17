# Issue tracking

This directory holds planning tickets. Write each issue in the following format:

```
# Title in sentence case

## Context
Describe background and motivation.

## Acceptance Criteria
List the requirements for completion.

## Status
Open
```

## Style guide

- Titles are written in **sentence case**.
- Include the `Context`, `Acceptance Criteria`, and `Status` sections with
  those exact headings.

## Naming
File names must be slugged (kebab-case) titles with no numeric prefixes.
For example: `refactor-orchestrator-instance-circuit-breaker.md`.
Do not include numeric identifiers in ticket titles or content; reference tickets by slugged filenames.

## Workflow
Set `Status` to `Open` while work is active. When finished, change it to
`Archived` and move the file into the `archive/` subdirectory without
renaming.

Open tickets live in this directory. Archived tickets share the same
slugged file name under the `archive/` subdirectory.
