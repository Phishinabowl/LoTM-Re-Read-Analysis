param(
  [switch]$Json,
  [string]$RequirementsPath = "requirements-python.txt"
)

$ErrorActionPreference = "Stop"

$candidates = @("python", "python3", "py")
$moduleNameOverrides = @{
  "pyyaml" = "yaml"
}

function Get-RequirementModules {
  param(
    [string]$Path
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    return @()
  }

  $modules = @()
  foreach ($line in Get-Content -LiteralPath $Path) {
    $clean = ($line -replace "#.*$", "").Trim()
    if (-not $clean) {
      continue
    }
    if ($clean.StartsWith("-")) {
      continue
    }
    $package = ($clean -split "[<>=!~\[\]; ]", 2)[0].Trim()
    if (-not $package) {
      continue
    }
    $lookup = $package.ToLowerInvariant()
    if ($moduleNameOverrides.ContainsKey($lookup)) {
      $moduleName = $moduleNameOverrides[$lookup]
    } else {
      $moduleName = $package.Replace("-", "_")
    }
    $modules += [ordered]@{
      package = $package
      module = $moduleName
    }
  }
  return @($modules)
}

$checked = @()
$result = [ordered]@{
  available = $false
  ready = $false
  command = $null
  version = $null
  executable = $null
  requirements_path = $RequirementsPath
  requirements_checked = $false
  requirements_available = $true
  requirements = @()
  checked = @()
  message = "Python unavailable. Use documented PowerShell fallback scripts."
}

foreach ($candidate in $candidates) {
  $command = Get-Command $candidate -ErrorAction SilentlyContinue
  if ($null -eq $command) {
    $checked += [ordered]@{
      command = $candidate
      found = $false
      usable = $false
      detail = "Command not found on PATH."
    }
    continue
  }

  $versionOutput = $null
  $versionExitCode = $null
  try {
    $versionOutput = & $command.Source --version 2>&1
    $versionExitCode = $LASTEXITCODE
  } catch {
    $checked += [ordered]@{
      command = $candidate
      found = $true
      usable = $false
      path = $command.Source
      detail = $_.Exception.Message
    }
    continue
  }

  if ($versionExitCode -ne 0) {
    $checked += [ordered]@{
      command = $candidate
      found = $true
      usable = $false
      path = $command.Source
      detail = "Version check failed with exit code $versionExitCode. $versionOutput"
    }
    continue
  }

  $executableOutput = $null
  $executableExitCode = $null
  try {
    $executableOutput = & $command.Source -c "import sys; print(sys.executable)" 2>&1
    $executableExitCode = $LASTEXITCODE
  } catch {
    $checked += [ordered]@{
      command = $candidate
      found = $true
      usable = $false
      path = $command.Source
      version = ($versionOutput -join "`n").Trim()
      detail = $_.Exception.Message
    }
    continue
  }

  if ($executableExitCode -ne 0) {
    $checked += [ordered]@{
      command = $candidate
      found = $true
      usable = $false
      path = $command.Source
      version = ($versionOutput -join "`n").Trim()
      detail = "Executable check failed with exit code $executableExitCode. $executableOutput"
    }
    continue
  }

  $version = ($versionOutput -join "`n").Trim()
  $executable = ($executableOutput -join "`n").Trim()
  $requirements = @()
  $requirementsAvailable = $true
  $requirementModules = Get-RequirementModules -Path $RequirementsPath
  foreach ($requirement in $requirementModules) {
    $moduleOutput = $null
    $moduleExitCode = $null
    try {
      $moduleOutput = & $command.Source -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$($requirement.module)') else 1)" 2>&1
      $moduleExitCode = $LASTEXITCODE
    } catch {
      $moduleExitCode = 1
      $moduleOutput = $_.Exception.Message
    }
    $present = ($moduleExitCode -eq 0)
    if (-not $present) {
      $requirementsAvailable = $false
    }
    $requirements += [ordered]@{
      package = $requirement.package
      module = $requirement.module
      available = $present
      detail = if ($present) { "Module import check passed." } else { "Module import check failed. $moduleOutput".Trim() }
    }
  }

  $checked += [ordered]@{
    command = $candidate
    found = $true
    usable = $true
    path = $command.Source
    version = $version
    executable = $executable
    requirements_available = $requirementsAvailable
    requirements = $requirements
  }

  $result.available = $true
  $result.ready = $requirementsAvailable
  $result.command = $candidate
  $result.version = $version
  $result.executable = $executable
  $result.requirements_checked = ($requirementModules.Count -gt 0)
  $result.requirements_available = $requirementsAvailable
  $result.requirements = $requirements
  if ($requirementsAvailable) {
    $result.message = "Python available. Use preferred Python scripts."
  } else {
    $result.message = "Python available, but required Python modules are missing. Run: python -m pip install -r $RequirementsPath"
  }
  break
}

$result.checked = $checked

if ($Json) {
  $result | ConvertTo-Json -Depth 5
  exit 0
}

if ($result.available) {
  Write-Output "Python available."
  Write-Output "Command: $($result.command)"
  Write-Output "Version: $($result.version)"
  Write-Output "Executable: $($result.executable)"
  if ($result.requirements_checked) {
    if ($result.requirements_available) {
      Write-Output "Python requirements available: $($result.requirements_path)"
    } else {
      Write-Output "Python requirements missing: $($result.requirements_path)"
      foreach ($requirement in $result.requirements) {
        if (-not $requirement.available) {
          Write-Output "Missing module: $($requirement.module) (package $($requirement.package))"
        }
      }
      Write-Output "Install with: python -m pip install -r $($result.requirements_path)"
    }
  }
} else {
  Write-Output "Python unavailable."
  Write-Output "Use documented PowerShell fallback scripts."
}

exit 0
