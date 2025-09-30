# Output Formats

Autoresearch emits multiple views of a completed query so humans and
integrations can choose the right fidelity. Markdown and plain text target
interactive reviews, JSON enables downstream automation, and custom templates
let operators project a consistent report layout.

## Standard format features

Every format exposes the same core artifacts:

- **Answer** – the synthesized response for the query.
- **Citations** – ranked evidence items with snippets and stable source IDs.
- **Reasoning** – the ordered dialogue between dialectical agents.
- **Metrics** – latency, token usage, and gate telemetry captured during the
  run.
- **Claim audits** – FEVER-style verification records with provenance maps.
- **State ID** – reusable identifier for refreshing claim audits via CLI, UI, or
  API.

## Layered UX and exports

Depth controls in the CLI (`--depth`) and Streamlit share the same sequence of
levels—TL;DR, Concise, Standard, and Trace. Each level now publishes its enabled
sections so operators know when TL;DR summaries, key findings, claim tables,
knowledge graph panels, and graph exports are available. The Streamlit radio
syncs with these options and surfaces toggle switches for each section.

Claim audits gain dedicated toggles per row. Selecting **Show details for
claim** reveals the audit JSON, top sources, and analyst notes. Badges mirror
the CLI table: green (supported), amber (needs review), and red (unsupported).
The Socratic prompt expander reuses the same depth payload to recommend
follow-up questions grounded in the visible findings, citations, and claim
statuses.

Evaluation runs export the enriched metrics as Parquet and CSV pairs. The CSVs
include the config signature, citation coverage, contradiction rate, average
planner depth, routing deltas, and average routing decision count so telemetry
pipelines can diff regressions without re-opening the database files.

### Markdown

The default Markdown renderer highlights the TL;DR, answer, citations, and claim
verification table. Enable the trace depth to surface the full reasoning log,
raw JSON payload, and the audit table that now mirrors the CLI schema.

```bash
autoresearch search "What is quantum computing?" --output markdown
```

### JSON

JSON is ideal for programmatic consumers. The payload mirrors the
`QueryResponse` model and now includes:

- `claim_audits`: full FEVER-style audit rows, including `provenance` with the
  `retrieval`, `backoff`, and `evidence` namespaces.
- `state_id`: handle for the cached query state that powers
  `POST /query/reverify` and `autoresearch reverify`.
- `metrics.scout_gate`: the structured gate decision containing heuristics,
  thresholds, rationales, and telemetry for coverage and contradiction totals.
- `metrics.scout_stage`: persisted scout snippets, heuristics, and coverage
  roll-ups so external dashboards can compare scout and debate phases.

```bash
autoresearch search "What is quantum computing?" --depth trace --output json \
    > result.json
```

### Plain text

The plain text view keeps headings, answer, citations, and reasoning bullets but
omits the table layout. It still lists claim audits in the same order as the
JSON payload, making it useful for log streaming.

### Custom templates

Templates use `string.Template` variables such as `${answer}` and
`${claim_audits}`. The claim audit variable renders Markdown by default, so the
new provenance fields appear automatically in bespoke reports.

## Claim audit schema

Each audit row aligns with `ClaimAuditRecord.to_payload()` and now surfaces the
provenance namespaces alongside headline metrics:

| Field | Description |
| ----- | ----------- |
| `claim_id` | Stable identifier for the verified claim. |
| `status` | `supported`, `unsupported`, or `needs_review`. |
| `entailment_score` | Mean entailment confidence, if available. |
| `entailment_variance` | Sample variance supporting the mean score. |
| `instability_flag` | Boolean marker when entailment signals conflict. |
| `sample_size` | Number of snippets scored for the audit. |
| `sources` | Ordered list of evidence snippets with `source_id`. |
| `provenance` | Structured map with retrieval, backoff, and evidence keys. |

The CLI and Streamlit table render the same records while exposing the
provenance map through expandable panels.

## Gate decision telemetry and overrides

AUTO mode persists the scout decision under `metrics.scout_gate`. The object
contains:

- `heuristics`: final numeric signal values (overlap, conflict, complexity,
  coverage gap, retrieval confidence).
- `rationales`: comparator metadata indicating whether each signal crossed its
  threshold, the original baseline value, and any operator override applied.
- `telemetry`: coverage counts, contradiction totals, and sample sizes so UX
  layers and notebooks can quantify debate escalations.

Operators can override the policy via `gate_user_overrides` in configuration or
Streamlit. Overrides record their value in the matching `rationales[*].override`
field, making reviews and compliance sign-off easier.

## Persisted scout snippets

Before debate resets state, the orchestrator now stores `metrics.scout_stage`
with:

- `heuristics` and `rationales`: the same structures captured in
  `metrics.scout_gate`.
- `coverage` and `retrieval_confidence`: the detailed counters backing the
  heuristics.
- `snippets`: the first five scout snippets (title, URL, snippet, backend,
  source ID) so debate participants and dashboards can reference the original
  retrieval context.

These additions keep the CLI, JSON, and Streamlit views in sync while providing
traceable hooks for audit and override workflows.
