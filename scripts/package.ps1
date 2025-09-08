<#
.SYNOPSIS
Build source and wheel distributions in a container.
.DESCRIPTION
Usage: scripts/package.ps1 [-DistDir <path>]
If invoked outside a container, the script runs inside a container image.
#>
param(
    [string]$DistDir = "dist"
)

if ($env:IN_CONTAINER) {
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
    exit 0
}

$Engine = $env:CONTAINER_ENGINE
if (-not $Engine) { $Engine = "docker" }
$Image = $env:CONTAINER_IMAGE
if (-not $Image) { $Image = "autoresearch-windows" }

if (-not (Get-Command $Engine -ErrorAction SilentlyContinue)) {
    Write-Error "Container engine '$Engine' not found."
    exit 1
}

$RepoPath = (Get-Location).ProviderPath
& $Engine run --rm `
    -v "${RepoPath}:C:\workspace" `
    -w "C:\workspace" `
    -e IN_CONTAINER=1 `
    $Image `
    powershell -File scripts\package.ps1 -DistDir $DistDir

