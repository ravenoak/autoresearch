# Issue tracking

This directory holds planning tickets. Write each issue in the following format:

```
# Title of the issue

## Context
Describe background and motivation.

## Acceptance Criteria
List the requirements for completion.

## Status
Open
```

## Naming
File names must be slugged (kebab-case) titles with no numeric prefixes.
For example: `refactor-orchestrator-instance-circuit-breaker.md`.

## Workflow
Set `Status` to `Open` while work is active. When finished, change it to
`Archived` and move the file into the `archive/` subdirectory without
renaming.

Open tickets live in this directory. Archived tickets share the same
slugged file name under the `archive/` subdirectory.
