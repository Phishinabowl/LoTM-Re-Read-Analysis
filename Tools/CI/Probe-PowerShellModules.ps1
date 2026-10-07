param(
    [string]$RequirementsPath = 'requirements-powershell-dev.txt',
    [string]$ModulePath
)

$ErrorActionPreference = 'Stop'
if ($ModulePath) {
    # pwsh startup can insert agent/global paths ahead of an inherited PSModulePath.
    $env:PSModulePath = $ModulePath
}
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
. (Join-Path $repoRoot 'Tools/Commands/Environment/Private/Requirements.ps1')
$modules = @(Read-ExactModuleRequirements -Path (Join-Path $repoRoot $RequirementsPath) -Root $repoRoot)
$results = foreach ($requirement in $modules) {
    $loaded = Import-Module $requirement.Name -RequiredVersion $requirement.Version -PassThru -ErrorAction Stop
    [ordered]@{ name = $requirement.Name
        version = [string]$loaded.Version
        path = $loaded.Path
    }
}
[ordered]@{
    edition = $PSVersionTable.PSEdition
    version = $PSVersionTable.PSVersion.ToString()
    executable = (Get-Process -Id $PID).Path
    modules = @($results)
} | ConvertTo-Json -Depth 5 -Compress
