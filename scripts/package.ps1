<#
.SYNOPSIS
Build source and wheel distributions.
.DESCRIPTION
Usage: scripts/package.ps1 [-DistDir <path>]
The script checks for a configuration file before building. Override the
default with $env:AUTORESEARCH_BUILD_CONFIG.
#>
param(
    [string]$DistDir = "dist"
)

$ConfigFile = $env:AUTORESEARCH_BUILD_CONFIG
if (-not $ConfigFile) {
    $ConfigFile = "pyproject.toml"
}

if (-not (Test-Path $ConfigFile)) {
    Write-Error "Configuration file '$ConfigFile' not found."
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required but not installed."
    exit 1
}

uv build --wheel --sdist --out-dir $DistDir
