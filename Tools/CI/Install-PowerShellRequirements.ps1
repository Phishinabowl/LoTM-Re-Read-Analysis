param(
    [Parameter(Mandatory)][string]$Destination,
    [string]$RequirementsPath = 'requirements-powershell-dev.txt'
)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
. (Join-Path $repoRoot 'Tools/Commands/Environment/Private/Requirements.ps1')
if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion -lt [version]'7.4') {
    throw 'Install dependencies with PowerShell 7.4+ Core.'
}
$requirements = @(Read-ExactModuleRequirements -Path (Join-Path $repoRoot $RequirementsPath) -Root $repoRoot)
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
foreach ($requirement in $requirements) {
    Save-Module -Name $requirement.Name -RequiredVersion $requirement.Version -Repository PSGallery `
        -Path $Destination -Force -ErrorAction Stop
}
