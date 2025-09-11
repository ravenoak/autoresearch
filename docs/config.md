# Configuration Reload Workflow

Autoresearch swaps configuration files atomically. Updates are applied only
after the new configuration parses successfully. When a change cannot be
loaded, the previous settings remain active and an error is logged.

## Live Reload Troubleshooting

- Ensure watched paths exist; missing files are ignored with a log warning.
- Check logs for messages like "Error reloading config" to diagnose issues.
- Validate changes with `uv run scripts/validate_deploy.py` before editing in
  place.
