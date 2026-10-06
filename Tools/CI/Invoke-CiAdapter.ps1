<#
.SYNOPSIS
Runs fixed PowerShell preflight or formatting over an owned adapter request.
.DESCRIPTION
Verifies exact host/module versions or forwards explicit captured source paths to the existing formatter.
Does not install modules, select test membership, or modify source files.
.PARAMETER Request
Absolute owned JSON request produced by the repository CI adapter.
.EXAMPLE
./Tools/CI/Invoke-CiAdapter.ps1 -Request .tmp/ci/request.json
#>
[CmdletBinding()]
param([Parameter(Mandatory)][string]$Request)
$ErrorActionPreference = 'Stop'
$OutputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
try {
    $document = Get-Content -LiteralPath $Request -Raw | ConvertFrom-Json
    if ($document.mode -eq 'powershell-preflight') {
        if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion.ToString() -ne $document.version) {
            throw 'Exact adopted PowerShell Core host required.'
        }
        $packages = [ordered]@{}
        foreach ($property in $document.packages.PSObject.Properties) {
            $module = Import-Module $property.Name -RequiredVersion $property.Value -PassThru -ErrorAction Stop
            $base = [IO.Path]::GetFullPath($module.ModuleBase)
            $owner = [IO.Path]::GetFullPath($document.module_root).TrimEnd([IO.Path]::DirectorySeparatorChar)
            if (-not $base.StartsWith($owner + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Module loaded outside the selected owner: $($property.Name)"
            }
            $packages[$property.Name] = $module.Version.ToString()
        }
        @{ status = 'passed'
            version = $PSVersionTable.PSVersion.ToString()
            packages = $packages
        } | ConvertTo-Json -Depth 10 -Compress
    }
    elseif ($document.mode -eq 'format') {
        $representation = if ($document.source_representation) {
            $document.source_representation
        }
        else {
            'Worktree'
        }
        & (Join-Path $document.root 'Tools/Static/Format-PowerShell.ps1') -Root $document.root `
            -Path @($document.paths) -SourceRepresentation $representation -Json
        exit $LASTEXITCODE
    }
    else {
        throw 'Unknown fixed PowerShell adapter mode.'
    }
}
catch {
    @{ status = 'error'
        error = $_.Exception.Message
    } | ConvertTo-Json -Compress
    exit 1
}
