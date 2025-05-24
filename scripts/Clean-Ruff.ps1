<#
.SYNOPSIS
  Remove any existing [tool.ruff] sections from pyproject.toml and append a basic configuration.

.DESCRIPTION
  PowerShell script used to fix the pyproject.toml when previous modifications left
  stray ruff configuration lines. This script removes all `[tool.ruff]` and `[tool.ruff.*]`
  blocks using a regex that consumes entire blocks. It then appends a minimal ruff
  configuration to the file.

.EXAMPLE
  ./Clean-Ruff.ps1
#>

$pyproject = "pyproject.toml"
$raw = Get-Content $pyproject -Raw
$pattern = '(?ms)^\[tool\.ruff(?:\.[^\]]+)?\][\s\S]*?(?=^\[tool\.|\Z)'
$clean = [regex]::Replace($raw, $pattern, '')
$clean | Set-Content $pyproject -Encoding UTF8

@'
[tool.ruff]
extend-exclude = ["sdk-py", "httpx", "redis", "requests", "plugins"]

[tool.ruff.lint]
extend-ignore = ["E402"]
'@ | Add-Content $pyproject -Encoding UTF8

Write-Host "Updated $pyproject with cleaned ruff configuration."