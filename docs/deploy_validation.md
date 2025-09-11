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
