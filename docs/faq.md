# Frequently Asked Questions

## How do I enable dark mode in the GUI?
Set `Dark Mode` in the sidebar of the Streamlit interface.

## Why do my token counts change after upgrading?
Token counts may vary slightly with model updates. Run `Taskfile check-baselines` to ensure usage is within expected limits.

## Why does the CI run `task test:all`?
Running the entire suite, including slow tests, helps catch edge cases before release.
