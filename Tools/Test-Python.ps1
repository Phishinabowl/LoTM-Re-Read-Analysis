param(
  [switch]$Json
)

$ErrorActionPreference = "Stop"

$candidates = @("python", "python3", "py")
$checked = @()
$result = [ordered]@{
  available = $false
  command = $null
  version = $null
  executable = $null
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
  $checked += [ordered]@{
    command = $candidate
    found = $true
    usable = $true
    path = $command.Source
    version = $version
    executable = $executable
  }

  $result.available = $true
  $result.command = $candidate
  $result.version = $version
  $result.executable = $executable
  $result.message = "Python available. Use preferred Python scripts."
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
} else {
  Write-Output "Python unavailable."
  Write-Output "Use documented PowerShell fallback scripts."
}

exit 0
