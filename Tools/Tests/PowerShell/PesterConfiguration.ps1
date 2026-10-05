param(
    [string[]]$Path,
    [ValidateSet('Unit', 'Integration')][string[]]$Tag,
    [switch]$Discover
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion -lt [version]'7.4') {
    throw 'Native PowerShell tests require PowerShell 7.4+ Core.'
}
Import-Module Pester -RequiredVersion 6.2.0 -ErrorAction Stop
$nativeRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$paths = if ($PSBoundParameters.ContainsKey('Path')) {
    if (-not $Path -or @($Path | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
        throw 'An explicit Pester selection cannot be empty.'
    }
    foreach ($candidate in $Path) {
        $resolved = (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path
        $relative = [IO.Path]::GetRelativePath($nativeRoot, $resolved)
        if ($relative.StartsWith('..') -or [IO.Path]::IsPathRooted($relative) -or
            -not $resolved.EndsWith('.Tests.ps1', [StringComparison]::OrdinalIgnoreCase) -or
            -not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
            throw "Pester selection must be an existing native .Tests.ps1 file: $candidate"
        }
        $resolved
    }
}
else {
    Get-ChildItem -LiteralPath $nativeRoot -Filter '*.Tests.ps1' -File | Select-Object -ExpandProperty FullName
}
$paths = @($paths | Sort-Object -Unique)
if ($paths.Count -eq 0) {
    throw 'No native Pester files selected.'
}
$configuration = New-PesterConfiguration
$configuration.Run.Path = $paths
$configuration.Run.RepoRoot = $nativeRoot
$configuration.Run.PassThru = $true
$configuration.Run.SkipRun = [bool]$Discover
$configuration.Run.Parallel = $false
$configuration.Run.Shuffle = $false
$configuration.Run.Exit = $false
$configuration.TestRegistry.Enabled = $false
$configuration.Output.Verbosity = 'Minimal'
if ($Tag) {
    $configuration.Filter.Tag = $Tag
}
$configuration
