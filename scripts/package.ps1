<#
.SYNOPSIS
Build source and wheel distributions.
.DESCRIPTION
Usage: scripts/package.ps1 [-DistDir <path>]
#>
param(
    [string]$DistDir = "dist"
)

uv build --wheel --sdist --out-dir $DistDir
