# User Guide

This guide highlights the most important controls for navigating Autoresearch
outputs.

## Depth controls

Autoresearch responses are organised by depth levels that determine how much
context is displayed. Depth can be selected from the CLI with `--depth` or via
the Streamlit radio group. Each depth level now advertises the sections it
unlocks—TL;DR summaries, key findings, claim tables, the knowledge graph, graph
export links, and the full reasoning trace. The CLI `--help` output lists these
combinations, and JSON exports include a `sections` map so that downstream tools
can enforce depth-aware policies.

The Streamlit app mirrors these options with toggle switches for every layer:
**Show TL;DR**, **Show key findings**, **Show claim table**, **Show full
trace**, **Show knowledge graph**, and **Enable graph exports**. Toggle defaults
are bound to the current depth so that moving to deeper views surfaces more
context without retaining stale preferences.

## Provenance verification

Claim verification is surfaced through the dedicated Provenance panel. Claim
statuses are summarised in natural order (supported, needs review, unsupported)
and the detailed table remains available when the claim table toggle is active.
Each row exposes a **Show details for claim** toggle that reveals the full audit
payload, top sources, and analyst notes. Badges reuse the CLI legend—green for
supported, amber for needs review, red for unsupported—so the table, CLI, and
CSV exports convey the same meaning. GraphRAG artifacts are also exposed in the
Provenance panel to verify that graph reasoning supplied the cited evidence. At
lower depths the panel explains which artefacts are hidden and how to reveal
them.

## Socratic prompts and traces

Socratic prompts adapt to the visible findings, citations, gate telemetry, and
claims, encouraging users to question evidence and explore follow-up angles.
The per-claim detail toggles pipe the same payload into the Socratic expander,
so prompts reference the selected claim ID and supporting evidence. The full
trace toggle governs both reasoning steps and ReAct event visualisations, making
it simple to switch between quick summaries and full audit trails. Trace
downloads retain the depth selection so exported Markdown or JSON matches the
on-screen view.
