#!/usr/bin/env pwsh
<##
.SYNOPSIS
    Validate configuration and deploy on Windows.
.DESCRIPTION
    Runs validation and then executes the deployment helper.
#>

uv run scripts/validate_deploy.py
uv run python scripts/deploy.py
