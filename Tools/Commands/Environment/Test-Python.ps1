param(
    [string]$Root,
    [switch]$Json,
    [string]$RequirementsPath = 'requirements-python.txt'
)

$ErrorActionPreference = 'Stop'
$toolsRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1'
. (Join-Path (Split-Path -Parent $runtimeModule) 'Private/PowerShell-Host.ps1')
Assert-KnowledgePowerShellHost
Import-Module $runtimeModule -Force
$repoRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$requirementsFullPath = if ([IO.Path]::IsPathRooted($RequirementsPath)) {
    $RequirementsPath
}
else {
    Join-Path $repoRoot $RequirementsPath
}
$result = [ordered]@{
    available = $false
    ready = $false
    command = $null
    version = $null
    executable = $null
    requirements_path = $requirementsFullPath
    requirements_checked = $false
    requirements_available = $false
    requirements = @()
    checked = @()
    message = 'Python 3.14+ unavailable; install the declared interpreter before explicit bootstrap.'
}
foreach ($candidate in @('python', 'python3', 'py')) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        $result.checked += [ordered]@{ command = $candidate
            found = $false
            usable = $false
        }
        continue
    }
    try {
        $output = & $command.Source (Join-Path $PSScriptRoot 'check_python.py') --root $repoRoot --requirements $requirementsFullPath 2>&1
        $code = $LASTEXITCODE
        $probe = ($output -join "`n") | ConvertFrom-Json -ErrorAction Stop
        $result.available = $true
        $result.ready = $code -eq 0 -and $probe.ready
        $result.command = $candidate
        $result.version = $probe.version
        $result.executable = $probe.executable
        $result.requirements_checked = $true
        $result.requirements_available = $probe.requirements_available
        $result.requirements = @($probe.requirements)
        $result.message = $probe.message
        $result.checked += [ordered]@{
            command = $candidate
            found = $true
            usable = $result.ready
            detail = $probe.message
        }
        break
    }
    catch {
        $result.checked += [ordered]@{
            command = $candidate
            found = $true
            usable = $false
            detail = $_.Exception.Message
        }
    }
}
if ($Json) {
    $result | ConvertTo-Json -Depth 8
}
else {
    Write-Output $result.message
    if ($result.executable) {
        Write-Output "Python $($result.version): $($result.executable)"
    }
    foreach ($requirement in $result.requirements) {
        Write-Output "$($requirement.package) $($requirement.expected_version): $($requirement.detail)"
    }
}
exit $(if ($result.ready) {
        0
    }
    else {
        1
    })
