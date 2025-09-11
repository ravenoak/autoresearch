# Deployment Validation

Run `scripts/validate_deploy.py` to confirm deployment readiness. The script
checks required environment variables, validates `deploy.yml` and `.env` files,
and reports precise schema errors.

## Usage

```
uv run scripts/validate_deploy.py
```

## Troubleshooting

- Errors appear as `path: message`; fix the field and rerun the script.
- Ensure `DEPLOY_ENV` and `CONFIG_DIR` are set before invocation.
- Use absolute paths for `CONFIG_DIR` to avoid resolution problems.

## Reload procedure

1. Update `deploy.yml` or `.env` in the target directory.
2. Run `uv run scripts/validate_deploy.py` to recheck schema rules.
3. Execute `uv run scripts/deploy.py` to verify required settings and an
   optional health check. The script honours `AUTORESEARCH_CONFIG_FILE` when a
   custom path is needed.
4. Repeat after addressing any reported errors until both scripts succeed.
