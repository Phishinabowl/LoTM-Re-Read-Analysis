# Dependency-free startup policy, also used before the framework module can be imported.
function Get-KnowledgePowerShellHostStatus {
    param([System.Collections.IDictionary]$VersionTable = $PSVersionTable)

    $edition = if ($VersionTable.Contains('PSEdition')) {
        [string]$VersionTable.PSEdition
    }
    else {
        'Desktop'
    }
    $version = [version]$VersionTable.PSVersion
    $supported = $edition -ceq 'Core' -and $version -ge [version]'7.4'
    return [pscustomobject]@{
        host_supported = $supported
        minimum_powershell_version = '7.4'
        powershell_version = [string]$version
        edition = $edition
        message = if ($supported) {
            'Supported PowerShell host.'
        }
        else {
            "Unsupported PowerShell host: $version ($edition). Install PowerShell 7.4+ Core and run this command with pwsh. No automatic host switch is performed."
        }
    }
}

function Assert-KnowledgePowerShellHost {
    $status = Get-KnowledgePowerShellHostStatus
    if (-not $status.host_supported) {
        throw $status.message
    }
}

function Resolve-KnowledgePowerShellExecutable {
    param([string]$Executable = (Get-Process -Id $PID).Path)

    Assert-KnowledgePowerShellHost
    if ([string]::IsNullOrWhiteSpace($Executable) -or -not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw 'The current supported PowerShell executable is unavailable; launch this command using an installed pwsh executable.'
    }
    $currentExecutable = (Get-Process -Id $PID).Path
    if ([System.IO.Path]::GetFullPath($Executable) -cne [System.IO.Path]::GetFullPath($currentExecutable)) {
        throw 'Conformance children must use the current supported PowerShell executable; alternate hosts are not allowed.'
    }
    return [System.IO.Path]::GetFullPath($Executable)
}
