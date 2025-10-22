# Scholarly Ingestion Guide

The scholarly connectors allow workspaces to capture arXiv and Hugging Face
Papers content for offline research. This guide explains how to fetch papers,
verify cached metadata, and attach sources to workspace manifests from both the
CLI and desktop UI.

## Prerequisites

- Ensure the Autoresearch CLI is installed and configured (`autoresearch
  config init`).
- Initialise storage so DuckDB tables and cache directories exist (`autoresearch
  workspace list`).
- Optional: activate a workspace before running the commands below.

## CLI Workflow

1. Search for papers using multiple providers:

   ```bash
   autoresearch workspace papers search "retrieval augmented generation" \
       --provider arxiv --provider huggingface
   ```

   The CLI prints the top matches grouped by provider with the normalised
   identifier that can be used during ingestion.

2. Ingest a paper and cache each content variant:

   ```bash
   autoresearch workspace papers ingest arxiv 2401.01234v1 --workspace audit-notes
   ```

   The command downloads the abstract, HTML, and PDF assets, stores them under
   deterministic paths in `scholarly_cache/`, and records provenance metadata
   (source URL, checksum, provider version, and retrieval latency) in DuckDB.
   Use `--no-attach` to skip manifest updates when scripting batch imports.

3. Attach a cached paper to the active workspace manifest:

   ```bash
   autoresearch workspace papers attach audit-notes arxiv 2401.01234v1
   ```

   Each attached resource now carries namespace-aware provenance, a list of
   cached content variants, and supplemental asset links so debates cite the
   correct version while offline.

## Desktop Workflow

- Use the **Resources → Search Scholarly Papers…** menu to run provider queries
  without leaving the desktop client.
- Select **Ingest Scholarly Paper…** to cache a DOI or arXiv identifier. When a
  workspace is active, the UI prompts to attach the paper immediately.
- Choose **Attach Cached Paper…** to browse previously ingested items for the
  current workspace.

## Offline Replay

Once a paper has been cached the metadata lives in the `scholarly_papers`
DuckDB table. Behaviour tests verify that disconnecting from the network still
allows the agent to surface cached content and cite the preserved provenance.
Check the `provenance.retrieved_at` timestamp and `contents` payload to confirm
the last sync time and available formats.
