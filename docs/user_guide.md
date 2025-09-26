# User Guide

This guide highlights the depth-aware output controls introduced for the CLI and
Streamlit interfaces. It assumes you have already completed the installation
steps in [docs/installation.md](installation.md) and can run `autoresearch`
commands locally.

## CLI depth flags

The `autoresearch search` command accepts a repeatable `--depth` flag that
activates richer sections of the final answer. Choose one or more of the
following layers:

- `tldr` – prepend a concise summary above the main answer.
- `findings` – list the key findings extracted from the reasoning chain.
- `claims` – render a table with each claim, its confidence, and supporting
  evidence.
- `trace` – include the agent trace captured by the audit pipeline.
- `full` – enable every layer at once.

Example:

```
autoresearch search "compare llama models" --depth tldr --depth claims --depth trace
```

The JSON renderer adds a `depth_sections` object so automation can parse the
same details. When no depth flags are supplied, the formatter behaves exactly as
in previous releases.

## Streamlit depth toggles

The Streamlit UI mirrors these controls in the query form. Select the desired
layers before running a query to add TL;DR summaries, key findings, claim tables,
and traces to the answer view. The export buttons include the same information in
Markdown and JSON downloads.

## Provenance verification

Results now include a **Provenance** tab that surfaces:

- Audit trail entries recorded during orchestration.
- GraphRAG artifacts, rendered as GraphViz diagrams when node and edge data are
  available.

Use this panel to confirm the lineage of each claim and to inspect how GraphRAG
connected evidence. The provenance view complements the existing knowledge graph
and metrics tabs, giving you a single location to verify supporting data.
