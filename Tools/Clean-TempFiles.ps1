param(
  [switch]$Delete,
  [switch]$Json
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$allowedDirectoryNames = @("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox")

function Test-IsWithinRepo {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Root
  )

  $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
  $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
  return $resolvedPath.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)
}

$targets = @(
  Get-ChildItem -Path $repoRoot -Directory -Recurse -Force |
    Where-Object { $allowedDirectoryNames -contains $_.Name } |
    Sort-Object FullName
)

$results = @()
foreach ($target in $targets) {
  $resolved = (Resolve-Path -LiteralPath $target.FullName).Path
  if (-not (Test-IsWithinRepo -Path $resolved -Root $repoRoot)) {
    continue
  }

  if ($Delete) {
    Remove-Item -LiteralPath $resolved -Recurse -Force
    $status = "deleted"
  } else {
    $status = "would_delete"
  }

  $results += [ordered]@{
    path = $resolved
    status = $status
  }
}

$output = [ordered]@{
  repo_root = $repoRoot
  delete = [bool]$Delete
  allowed_directory_names = $allowedDirectoryNames
  count = $results.Count
  results = $results
}

if ($Json) {
  $output | ConvertTo-Json -Depth 5
  exit 0
}

if ($results.Count -eq 0) {
  Write-Output "No allowlisted cache directories found."
  exit 0
}

$action = if ($Delete) { "Deleted" } else { "Would delete" }
foreach ($result in $results) {
  Write-Output "${action}: $($result.path)"
}
