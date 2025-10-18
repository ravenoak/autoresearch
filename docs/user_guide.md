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

## Planner graph conditioning

Knowledge graph signals can be threaded into planner prompts when retrieval
surfaces contradictions or informative neighbours. Enable the feature in
`search.context_aware` by setting `planner_graph_conditioning = true` after the
graph pipeline has been validated for your deployment. The toggle works best
for sessions that ingest at least one retrieval batch; the planner reuses
stored contradictions, neighbour previews, and provenance to seed the prompt.
The AUTO workflow now ships with
`tests/behavior/features/reasoning_modes/planner_graph_conditioning.feature` so
operators can confirm the cues before enabling the option in production.

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

## Interactive re-verification

Each response now exposes a state identifier whenever claim audits are present.
The Streamlit claim panel adds a **Refresh claim audits** button plus optional
controls for broadening retrieval or selecting an alternate
`fact_checker.verification.<variant>` prompt. Pressing the button replays the
FactChecker with the chosen settings and refreshes the badges, provenance,
and source list without rerunning the full query. The CLI mirrors the workflow via
`autoresearch reverify <state_id> --broaden-sources --max-results 12` so audits
can be updated in scripted environments. The API also accepts
`POST /query/reverify` with the same parameters, enabling integrations to
refresh provenance programmatically.

## Socratic prompts and traces

Socratic prompts adapt to the visible findings, citations, gate telemetry, and
claims, encouraging users to question evidence and explore follow-up angles.
The per-claim detail toggles pipe the same payload into the Socratic expander,
so prompts reference the selected claim ID and supporting evidence. The full
trace toggle governs both reasoning steps and ReAct event visualisations, making
it simple to switch between quick summaries and full audit trails. Trace
downloads retain the depth selection so exported Markdown or JSON matches the
on-screen view.

## Enhanced CLI Interface

### Log Format Control

Autoresearch now provides intelligent log formatting that adapts to your usage context:

**Auto-Detection**: The system automatically detects whether you're using an interactive terminal or automation context:
- **Interactive terminals**: Human-readable console format
- **Automation/redirected output**: Structured JSON format for machine parsing

**Manual Control**: Override auto-detection with explicit format options:
```bash
# Force console format for human readability
autoresearch search "query" --log-format console

# Force JSON format for automation
autoresearch search "query" --log-format json

# Use auto-detection (default)
autoresearch search "query" --log-format auto
```

### Quiet Mode

Suppress diagnostic log messages while preserving errors and warnings:
```bash
# Only show errors and warnings
autoresearch search "query" --quiet-logs
```

### Bare Mode for Accessibility

Enable simplified output for screen readers and text-only interfaces:
```bash
# Disable colors, symbols, and decorative formatting
autoresearch search "query" --bare-mode
```

This mode provides:
- Plain text labels (SUCCESS, ERROR, WARNING, INFO)
- No Unicode symbols
- No ANSI color codes
- Essential functionality preserved

### Section-Level Control

Fine-tune which sections appear in your output:

**Show Available Sections**:
```bash
# See what sections are available for a depth level
autoresearch search "query" --depth standard --show-sections
```

**Include Specific Sections**:
```bash
# Include reasoning section even at concise depth
autoresearch search "query" --depth concise --include=reasoning

# Include multiple sections
autoresearch search "query" --include=metrics,reasoning
```

**Exclude Specific Sections**:
```bash
# Exclude raw response at trace depth
autoresearch search "query" --depth trace --exclude=raw_response

# Exclude multiple sections
autoresearch search "query" --exclude=raw_response,citations
```

**Combine Include and Exclude**:
```bash
# Include metrics but exclude citations
autoresearch search "query" --include=metrics --exclude=citations
```

### Improved Error Messages

All error messages now include:
- **Clear descriptions** of what went wrong
- **Actionable suggestions** for resolution
- **Code examples** showing correct usage
- **Consistent formatting** across all interfaces

**Example**:
```bash
autoresearch search "query" --log-format invalid
# Error: Invalid log format: invalid. Valid options: json, console, auto
# Suggestion: Use --log-format console for human-readable output
# Example: autoresearch search "query" --log-format console
```

## Output Stream Management

### Clean Separation

- **stdout**: Application results and user-facing content
- **stderr**: Diagnostic logs, progress indicators, and status messages
- **No mixing**: Human-readable content never mixed with JSON logs in normal usage

### Automation-Friendly

When stdout is redirected or in automation contexts:
```bash
# JSON logs go to stderr, results to stdout
autoresearch search "query" > results.json

# Both streams can be captured separately
autoresearch search "query" > results.json 2> logs.json
```

## Cross-Interface Consistency

### Unified Experience

All interfaces (CLI, Streamlit GUI, API, MCP) now provide:
- **Same depth levels** with identical section availability
- **Consistent error messaging** with actionable suggestions
- **Unified response schemas** for programmatic consumption
- **Same metadata fields** (state_id, correlation_id)

### Interface-Specific Features

**CLI Interface**:
- Command-line options for all features
- Intelligent format detection
- Section-level control
- Bare mode for accessibility

**Desktop GUI**:
- Interactive depth controls
- Real-time log viewer
- Section toggles
- Export functionality

**API Interface**:
- JSON responses with consistent schema
- Correlation ID tracking
- Standardized error formats
- Programmatic access to all features

## Troubleshooting

### Common Issues and Solutions

**JSON logs appearing in CLI output**:
- This should not happen in normal usage
- If it occurs, check that you're using an interactive terminal
- Try: `autoresearch search "query" --log-format console`

**Output appears duplicated**:
- Check for multiple print statements in error handling
- Use `--quiet-logs` to suppress diagnostic messages
- Report as a bug if it persists

**Colors not displaying correctly**:
- Use `--bare-mode` for text-only output
- Check terminal color support
- Try a different terminal emulator

**Screen reader compatibility issues**:
- Always use `--bare-mode` for screen readers
- Report any remaining accessibility issues
- Check that all images have alt text

### Getting Help

**Command Help**:
```bash
# Get help for any command
autoresearch search --help
autoresearch --help
```

**Feature Documentation**:
- This user guide for general usage
- CLI help for command-specific options
- API documentation for programmatic usage

**Community Support**:
- GitHub issues for bug reports and feature requests
- Documentation for detailed technical information
- Community forums for user discussions

## Migration Guide

### From Previous Versions

**New CLI Options**:
- `--log-format`: Control log output format
- `--quiet-logs`: Suppress diagnostic messages
- `--bare-mode`: Enable accessibility mode
- `--show-sections`: Display available sections
- `--include`/`--exclude`: Control section visibility

**Behavioral Changes**:
- Log format auto-detection (may change output format)
- Enhanced error messages (more detailed and actionable)
- Improved output stream separation

**Configuration Updates**:
- No configuration changes required
- All new features work with existing configurations
- Environment variables available for advanced customization

### Breaking Changes

**None**: All changes are backward compatible and additive.
