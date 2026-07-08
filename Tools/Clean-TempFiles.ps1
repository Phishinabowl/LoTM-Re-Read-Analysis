param(
  [switch]$Delete,
  [switch]$IncludeTmp,
  [string[]]$TmpPath = @(),
  [switch]$Json
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$allowedDirectoryNames = @("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox")
$tmpRoot = Join-Path $repoRoot ".tmp"

function Test-IsWithinRepo {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Root
  )

  $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
  $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
  return (
    $resolvedPath -eq $resolvedRoot -or
    $resolvedPath.StartsWith($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)
  )
}

function Test-IsWithinTmp {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$TmpRoot
  )

  $resolvedPath = (Resolve-Path -LiteralPath $Path).Path
  $resolvedTmp = (Resolve-Path -LiteralPath $TmpRoot).Path
  return (
    $resolvedPath -ne $resolvedTmp -and
    $resolvedPath.StartsWith($resolvedTmp + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)
  )
}

$cacheTargets = @(
  Get-ChildItem -Path $repoRoot -Directory -Recurse -Force |
    Where-Object { $allowedDirectoryNames -contains $_.Name } |
    Sort-Object FullName
)
$tmpTargets = @()
if ($IncludeTmp -and (Test-Path -LiteralPath $tmpRoot)) {
  $tmpTargets = @(
    Get-ChildItem -LiteralPath $tmpRoot -Force |
      Sort-Object FullName
  )
}
$scopedTmpTargets = @()
foreach ($pathValue in @($TmpPath)) {
  $candidate = if ([System.IO.Path]::IsPathRooted($pathValue)) { $pathValue } else { Join-Path $repoRoot $pathValue }
  if (-not (Test-Path -LiteralPath $candidate)) {
    continue
  }
  $resolvedCandidate = (Resolve-Path -LiteralPath $candidate).Path
  if ((Test-IsWithinRepo -Path $resolvedCandidate -Root $repoRoot) -and (Test-IsWithinTmp -Path $resolvedCandidate -TmpRoot $tmpRoot)) {
    $scopedTmpTargets += Get-Item -LiteralPath $resolvedCandidate -Force
  }
}
$targets = @($cacheTargets + $tmpTargets + ($scopedTmpTargets | Sort-Object FullName -Unique))

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
  allowed_directory_names = @($allowedDirectoryNames | Sort-Object)
  include_tmp = [bool]$IncludeTmp
  tmp_root = $tmpRoot
  cache_count = @($cacheTargets).Count
  tmp_count = @($tmpTargets).Count
  scoped_tmp_count = @($scopedTmpTargets).Count
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
