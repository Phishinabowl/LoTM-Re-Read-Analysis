param(
    [string]$Root,
    [string]$RequirementsPath = "requirements-powershell.txt",
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
. (Join-Path (Split-Path -Parent $runtimeModule) 'Private\PowerShell-Host.ps1')
$hostStatus = Get-KnowledgePowerShellHostStatus
$repoRoot = $null
if ($hostStatus.host_supported) {
    Import-Module $runtimeModule -Force
    $repoRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
}

function Get-RequiredModules {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
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
}
else {
    if ($null -ne $repoRoot) {
        Join-Path $repoRoot $RequirementsPath
    }
    else {
        $RequirementsPath
    }
}

$requiredModules = if ($hostStatus.host_supported) {
    @(Get-RequiredModules $requirementsFullPath)
}
else {
    @()
}
$moduleResults = @()
foreach ($moduleName in $requiredModules) {
    $available = @(Get-Module -ListAvailable -Name $moduleName)
    $usable = $false
    $importDetail = ''
    if ($available.Count -gt 0) {
        try {
            $selectedModule = $available | Sort-Object Version -Descending | Select-Object -First 1
            $null = Import-Module $selectedModule.Path -Force -PassThru -ErrorAction Stop
            $usable = $true
            $importDetail = 'Module discovery and import checks passed.'
        }
        catch {
            $importDetail = "Module found but import failed: $($_.Exception.Message)"
        }
    }
    $moduleResults += [ordered]@{
        module = $moduleName
        present = $available.Count -gt 0
        usable = $usable
        version = if ($available.Count -gt 0) {
            [string]($available | Sort-Object Version -Descending | Select-Object -First 1).Version
        }
        else {
            ""
        }
        path = if ($available.Count -gt 0) {
            ($available | Sort-Object Version -Descending | Select-Object -First 1).Path
        }
        else {
            ""
        }
        detail = if ($available.Count -gt 0) {
            $importDetail
        }
        else {
            "Module not found. Run: Install-Module $moduleName -Scope CurrentUser -Force -AllowClobber"
        }
    }
}

$requirementsAvailable = $hostStatus.host_supported -and (Test-Path -LiteralPath $requirementsFullPath -PathType Leaf)
$ready = $requirementsAvailable -and -not ($moduleResults | Where-Object { -not $_.usable })
$result = [ordered]@{
    ready = $ready
    host_supported = $hostStatus.host_supported
    minimum_powershell_version = $hostStatus.minimum_powershell_version
    powershell_version = [string]$PSVersionTable.PSVersion
    edition = if ($PSVersionTable.ContainsKey("PSEdition")) {
        $PSVersionTable.PSEdition
    }
    else {
        "Desktop"
    }
    executable = (Get-Process -Id $PID).Path
    requirements_path = $requirementsFullPath
    modules = @($moduleResults)
    message = if (-not $hostStatus.host_supported) {
        $hostStatus.message
    }
    elseif (-not $requirementsAvailable) {
        "PowerShell requirements file not found: $requirementsFullPath. Supply an existing -RequirementsPath."
    }
    elseif ($ready) {
        'Supported PowerShell host and module requirements are usable.'
    }
    else {
        'PowerShell module requirements are missing or cannot be imported.'
    }
}

if ($Json) {
    $result | ConvertTo-Json -Depth 5
    exit $(if ($ready) {
            0
        }
        else {
            1
        })
}

Write-Output "PowerShell $($result.powershell_version) ($($result.edition))"
Write-Output "Executable: $($result.executable)"
Write-Output "Requirements: $($result.requirements_path)"
foreach ($module in $moduleResults) {
    if ($module.usable) {
        Write-Output "Module OK: $($module.module) $($module.version)"
    }
    else {
        Write-Output "Unusable module: $($module.module)"
        Write-Output $module.detail
    }
}
Write-Output $result.message
exit $(if ($ready) {
        0
    }
    else {
        1
    })
