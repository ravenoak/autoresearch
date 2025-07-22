# Frequently Asked Questions

## How do I enable dark mode in the GUI?
Set `Dark Mode` in the sidebar of the Streamlit interface.

## Why do my token counts change after upgrading?
Token counts may vary slightly with model updates. Run `Taskfile check-baselines` to ensure usage is within expected limits.

## Why does the CI run `task test:all`?
The workflow runs on Python 3.12 and 3.13 and executes `task test:all` to catch edge cases early.
