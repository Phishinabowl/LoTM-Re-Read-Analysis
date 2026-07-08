param(
  [string]$RequirementsPath = "requirements-powershell.txt",
  [switch]$Json
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function Get-RequiredModules {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return @()
  }
  $modules = @()
  foreach ($line in Get-Content -LiteralPath $Path) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) {
      continue
    }
    $moduleName = ($trimmed -split "\s+")[0]
    if ($moduleName) {
      $modules += $moduleName
    }
  }
  return @($modules)
}

$requirementsFullPath = if ([System.IO.Path]::IsPathRooted($RequirementsPath)) {
  $RequirementsPath
} else {
  Join-Path (Get-Location).Path $RequirementsPath
}

$requiredModules = @(Get-RequiredModules $requirementsFullPath)
$moduleResults = @()
foreach ($moduleName in $requiredModules) {
  $available = @(Get-Module -ListAvailable -Name $moduleName)
  $moduleResults += [ordered]@{
    module = $moduleName
    present = $available.Count -gt 0
    version = if ($available.Count -gt 0) { [string]($available | Sort-Object Version -Descending | Select-Object -First 1).Version } else { "" }
    path = if ($available.Count -gt 0) { ($available | Sort-Object Version -Descending | Select-Object -First 1).Path } else { "" }
    detail = if ($available.Count -gt 0) { "Module discovery check passed." } else { "Module not found. Run: Install-Module $moduleName -Scope CurrentUser -Force -AllowClobber" }
  }
}

$allPresent = -not ($moduleResults | Where-Object { -not $_.present })
$result = [ordered]@{
  ready = $allPresent
  powershell_version = [string]$PSVersionTable.PSVersion
  edition = if ($PSVersionTable.ContainsKey("PSEdition")) { $PSVersionTable.PSEdition } else { "Desktop" }
  executable = (Get-Process -Id $PID).Path
  requirements_path = $requirementsFullPath
  modules = @($moduleResults)
  message = if ($allPresent) { "PowerShell module requirements are available." } else { "PowerShell module requirements are missing." }
}

if ($Json) {
  $result | ConvertTo-Json -Depth 5
  exit $(if ($allPresent) { 0 } else { 1 })
}

Write-Output "PowerShell $($result.powershell_version) ($($result.edition))"
Write-Output "Executable: $($result.executable)"
Write-Output "Requirements: $($result.requirements_path)"
foreach ($module in $moduleResults) {
  if ($module.present) {
    Write-Output "Module OK: $($module.module) $($module.version)"
  } else {
    Write-Output "Missing module: $($module.module)"
    Write-Output $module.detail
  }
}
Write-Output $result.message
exit $(if ($allPresent) { 0 } else { 1 })
