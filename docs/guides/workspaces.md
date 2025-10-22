# Workspace Manifests Guide

This guide explains how to create, version, and consume workspace manifests in
Autoresearch. Workspaces define the curated resources that dialectical agents
must cite during debates.

## Creating a Workspace

Use the CLI to bootstrap a manifest:

```
autoresearch workspace create "alignment-audit" \
  --resource repo:core-engine@HEAD \
  --resource repo:toolkit@latest \
  --resource file:./notes/graph_hypotheses.md \
  --resource paper:arxiv:2401.01234
```

- Resources follow the `kind:reference` format. Append `?optional` to mark a
  resource that agents are encouraged, but not required, to cite.
- Each invocation versions the manifest. Use `--slug` to override the default
  slug derived from the workspace name.

## Inspecting Existing Manifests

List or view manifests through the CLI:

- `autoresearch workspace select <slug>` prints the latest version.
- Add `--version <n>` or `--manifest-id <id>` to target a specific revision.

The desktop application mirrors this functionality. Open the Sessions dock and
use the Workspaces panel to create or select manifests. New entries appear in
the list alongside existing versions.

## Running Workspace Debates

- CLI: `autoresearch workspace debate <slug> "prompt"` scopes the orchestration
  to the selected manifest.
- Desktop: Select a workspace in the Sessions dock and choose **Start Debate**
  to supply the prompt directly from the UI.

When `WorkspaceOrchestrator` is available, contrarian and fact-checker roles
must cite every required resource. Coverage metrics appear in the response
payload under `metrics.workspace`.

If the workspace-aware orchestrator is not installed, both interfaces fall
back to the baseline orchestrator and emit a warning indicating that citation
enforcement is disabled.
