<#
.SYNOPSIS
Runs registered PowerShell framework conformance suites.

.DESCRIPTION
Validates Tools/Conformance/suites.json, selects a named profile or explicit
suite IDs, and runs each selected PowerShell conformance runner in an isolated
child process. The command fails when the registry is malformed, its discovery
inventory has drifted, or any selected suite fails.

.PARAMETER Root
Project root. When omitted, the command discovers Project_Config/project.yaml
from the current directory or script location.

.PARAMETER Profile
Registered profile to run. Defaults to baseline and is ignored when Suite is
specified.

.PARAMETER Suite
One or more registered suite IDs to run instead of a profile.

.PARAMETER List
Lists registered profiles and suites without running conformance.

.PARAMETER Json
Emits the complete stable structured result suitable for parity checks and semantic automation.

.PARAMETER SummaryJson
Emits a concise validation-run-summary without nested suite summaries.

.PARAMETER ReportOutput
Writes the complete stable JSON result to a file beneath the project root.

.EXAMPLE
./Tools/Conformance/Run-Conformance.ps1 -Profile baseline -Json

.EXAMPLE
./Tools/Conformance/Run-Conformance.ps1 -Suite temporal,chronology
#>
[CmdletBinding()]
param(
    [string]$Root,
    [string]$Profile = 'baseline',
    [string[]]$Suite = @(),
    [switch]$List,
    [switch]$Json,
    [switch]$SummaryJson,
    [string]$ReportOutput
)

$ErrorActionPreference = 'Stop'
$toolsRoot = Split-Path -Parent $PSScriptRoot
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

$registryRelativePath = 'Tools/Conformance/suites.json'
$stableIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'
$failureExcerptLines = 20
$failureExcerptBytes = 4096

function Assert-JsonObject {
    param(
        [object]$Value,
        [string]$Context
    )

    if ($null -eq $Value -or $Value -isnot [System.Management.Automation.PSCustomObject]) {
        throw "Conformance registry '$Context' must be a mapping."
    }
}

function Assert-ObjectKeys {
    param(
        [object]$Value,
        [string[]]$Allowed,
        [string]$Context
    )

    Assert-JsonObject $Value $Context
    $unknown = @($Value.PSObject.Properties.Name | Where-Object { $Allowed -cnotcontains $_ })
    if ($unknown.Count -gt 0) {
        throw "Conformance registry '$Context' has unsupported fields: $($unknown -join ', ')"
    }
}

function Test-JsonInteger {
    param([object]$Value)

    return (
        $Value -is [sbyte] -or $Value -is [byte] -or
        $Value -is [int16] -or $Value -is [uint16] -or
        $Value -is [int32] -or $Value -is [uint32] -or
        $Value -is [int64] -or $Value -is [uint64]
    )
}

function Get-RequiredString {
    param(
        [object]$Value,
        [string]$Context
    )

    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value)) {
        throw "Conformance registry '$Context' must be a non-empty string."
    }
    return $Value.Trim()
}

function Get-StringList {
    param(
        [object]$Value,
        [string]$Context
    )

    if ($Value -isnot [System.Array]) {
        throw "Conformance registry '$Context' must be a string list."
    }
    $result = New-Object 'System.Collections.Generic.List[string]'
    foreach ($item in @($Value)) {
        if ($item -isnot [string] -or [string]::IsNullOrEmpty($item)) {
            throw "Conformance registry '$Context' must be a string list."
        }
        $result.Add([string]$item)
    }
    return @($result)
}

function Resolve-ConformancePath {
    param(
        [string]$RepoRoot,
        [object]$Value,
        [string]$Context,
        [switch]$RequireFile
    )

    $relative = Get-RequiredString $Value $Context
    if ([System.IO.Path]::IsPathRooted($relative)) {
        throw "Conformance registry '$Context' must be repository-relative."
    }
    $resolvedRoot = [System.IO.Path]::GetFullPath($RepoRoot)
    $resolved = [System.IO.Path]::GetFullPath((Join-Path $resolvedRoot $relative))
    $rootPrefix = $resolvedRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if ($resolved -cne $resolvedRoot -and -not $resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Conformance registry '$Context' escapes the project root."
    }
    if ($RequireFile -and -not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "Conformance runner does not exist: $relative"
    }
    return [pscustomobject]@{
        relative = $relative.Replace('\', '/')
        resolved = $resolved
    }
}

function Assert-UniqueStrings {
    param(
        [string[]]$Values,
        [string]$Context
    )

    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($value in @($Values)) {
        if (-not $seen.Add($value)) {
            throw "Conformance registry '$Context' contains duplicate value '$value'."
        }
    }
}

function Get-RepositoryRelativePath {
    param(
        [string]$RepoRoot,
        [string]$Path
    )

    $resolvedRoot = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\', '/')
    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    $rootPrefix = $resolvedRoot + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolvedPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Discovered conformance path is outside the project root: $resolvedPath"
    }
    return $resolvedPath.Substring($rootPrefix.Length).Replace('\', '/')
}

function Test-ConformanceDiscovery {
    param(
        [string]$RepoRoot,
        [object]$Discovery,
        [object]$RuntimePaths
    )

    Assert-ObjectKeys $Discovery @('python', 'powershell') 'discovery'
    foreach ($runtime in @('python', 'powershell')) {
        $rules = @($Discovery.PSObject.Properties[$runtime].Value)
        if ($rules.Count -eq 0) {
            throw "Conformance registry 'discovery.$runtime' must be a non-empty list."
        }
        $discovered = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $excluded = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        for ($index = 0; $index -lt $rules.Count; $index += 1) {
            $rule = $rules[$index]
            Assert-ObjectKeys $rule @('directory', 'pattern', 'exclude') "discovery.$runtime[$index]"
            $directory = Resolve-ConformancePath $RepoRoot $rule.directory "discovery.$runtime[$index].directory"
            if (-not (Test-Path -LiteralPath $directory.resolved -PathType Container)) {
                throw "Conformance discovery directory does not exist: $($directory.relative)"
            }
            $pattern = Get-RequiredString $rule.pattern "discovery.$runtime[$index].pattern"
            foreach ($path in @(Get-ChildItem -LiteralPath $directory.resolved -Filter $pattern -File)) {
                $relative = Get-RepositoryRelativePath $RepoRoot $path.FullName
                [void]$discovered.Add($relative)
            }
            foreach ($relative in @(Get-StringList $rule.exclude "discovery.$runtime[$index].exclude")) {
                [void]$excluded.Add($relative.Replace('\', '/'))
            }
        }
        $unregistered = @($discovered | Where-Object { -not $excluded.Contains($_) -and -not $RuntimePaths[$runtime].Contains($_) })
        $staleExclusions = @($excluded | Where-Object { -not $discovered.Contains($_) })
        if ($unregistered.Count -gt 0) {
            throw "Unregistered $runtime conformance runners: $($unregistered -join ', ')"
        }
        if ($staleExclusions.Count -gt 0) {
            throw "Stale $runtime conformance exclusions: $($staleExclusions -join ', ')"
        }
    }
}

function Get-ConformanceRegistry {
    param([string]$RepoRoot)

    $registryPath = Join-Path $RepoRoot $registryRelativePath
    $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
    Assert-ObjectKeys $registry @('schema_version', 'profiles', 'suites', 'discovery') 'root'
    if (-not (Test-JsonInteger $registry.schema_version) -or [int]$registry.schema_version -ne 1) {
        throw 'Unsupported conformance registry schema_version.'
    }
    if ($registry.suites -isnot [System.Array] -or @($registry.suites).Count -eq 0) {
        throw "Conformance registry 'suites' must be a non-empty list."
    }

    $suites = [ordered]@{}
    $runtimePaths = @{
        python = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        powershell = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    }
    for ($index = 0; $index -lt @($registry.suites).Count; $index += 1) {
        $suite = @($registry.suites)[$index]
        Assert-ObjectKeys $suite @('id', 'python', 'powershell', 'tags') "suites[$index]"
        $suiteId = Get-RequiredString $suite.id "suites[$index].id"
        if ($suiteId -cnotmatch $stableIdPattern -or $suites.Contains($suiteId)) {
            throw "Invalid or duplicate conformance suite ID: $suiteId"
        }
        $tags = @(Get-StringList $suite.tags "$suiteId.tags")
        Assert-UniqueStrings $tags "$suiteId.tags"
        $python = Resolve-ConformancePath $RepoRoot $suite.python "$suiteId.python" -RequireFile
        $powershell = Resolve-ConformancePath $RepoRoot $suite.powershell "$suiteId.powershell" -RequireFile
        if (-not $runtimePaths.python.Add($python.relative)) {
            throw "Duplicate python conformance runner: $($python.relative)"
        }
        if (-not $runtimePaths.powershell.Add($powershell.relative)) {
            throw "Duplicate powershell conformance runner: $($powershell.relative)"
        }
        $suites[$suiteId] = [pscustomobject]@{
            id = $suiteId
            tags = $tags
            python = $python.relative
            python_path = $python.resolved
            powershell = $powershell.relative
            powershell_path = $powershell.resolved
        }
    }

    Assert-JsonObject $registry.profiles 'profiles'
    foreach ($property in $registry.profiles.PSObject.Properties) {
        if ($property.Name -cnotmatch $stableIdPattern) {
            throw "Invalid conformance profile ID: $($property.Name)"
        }
        $members = @(Get-StringList $property.Value "profiles.$($property.Name)")
        if ($members.Count -eq 0) {
            throw "Conformance profile '$($property.Name)' must contain suites."
        }
        Assert-UniqueStrings $members "profiles.$($property.Name)"
        $unknown = @($members | Where-Object { -not $suites.Contains($_) })
        if ($unknown.Count -gt 0) {
            throw "Conformance profile '$($property.Name)' references unknown suites: $($unknown -join ', ')"
        }
    }

    Test-ConformanceDiscovery $RepoRoot $registry.discovery $runtimePaths
    return [pscustomobject]@{
        raw = $registry
        suites = $suites
    }
}

function Get-SelectedSuites {
    param(
        [object]$Registry,
        [string]$ProfileId,
        [string[]]$SuiteIds
    )

    if ($SuiteIds.Count -gt 0) {
        Assert-UniqueStrings $SuiteIds 'selected suites'
        $unknown = @($SuiteIds | Where-Object { -not $Registry.suites.Contains($_) })
        if ($unknown.Count -gt 0) {
            throw "Unknown conformance suite(s): $($unknown -join ', ')"
        }
        return [pscustomobject]@{
            profile = 'selected'
            suites = @($SuiteIds | ForEach-Object { $Registry.suites[$_] })
        }
    }
    $profileNames = @($Registry.raw.profiles.PSObject.Properties.Name)
    if ($profileNames -cnotcontains $ProfileId) {
        throw "Unknown conformance profile '$ProfileId'; choose from $($profileNames -join ', ')"
    }
    $members = @($Registry.raw.profiles.PSObject.Properties[$ProfileId].Value)
    return [pscustomobject]@{
        profile = $ProfileId
        suites = @($members | ForEach-Object { $Registry.suites[[string]$_] })
    }
}

function Invoke-ConformanceSuite {
    param(
        [string]$RepoRoot,
        [object]$SuiteDefinition
    )

    try {
        $executable = (Get-Process -Id $PID).Path
        $arguments = @('-NoProfile')
        if ($PSVersionTable.PSEdition -ceq 'Desktop') {
            $arguments += @('-ExecutionPolicy', 'Bypass')
        }
        $arguments += @('-File', $SuiteDefinition.powershell_path, '-Root', $RepoRoot, '-Json')
        $output = @(& $executable @arguments 2>&1)
        if ($LASTEXITCODE -ne 0) {
            $detail = @($output | ForEach-Object { [string]$_ } | Where-Object { $_ }) -join [Environment]::NewLine
            throw ($detail.Trim())
        }
        $lines = @($output | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
        if ($lines.Count -eq 0) {
            throw "Conformance suite '$($SuiteDefinition.id)' emitted no JSON summary."
        }
        $summary = $lines[$lines.Count - 1] | ConvertFrom-Json
        Assert-JsonObject $summary "$($SuiteDefinition.id) summary"
        return [ordered]@{
            id = $SuiteDefinition.id
            status = 'passed'
            summary = $summary
        }
    }
    catch {
        return [ordered]@{
            id = $SuiteDefinition.id
            status = 'failed'
            error = $_.Exception.Message
        }
    }
}

function Resolve-ConformanceReportOutput {
    param(
        [string]$RepoRoot,
        [string]$Value
    )

    $candidate = if ([System.IO.Path]::IsPathRooted($Value)) {
        $Value
    }
    else {
        Join-Path $RepoRoot $Value
    }
    $resolved = [System.IO.Path]::GetFullPath($candidate)
    $rootPath = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $rootPrefix = $rootPath + [System.IO.Path]::DirectorySeparatorChar
    if (
        $resolved -ceq $rootPath -or
        -not $resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "Conformance report output must be a file beneath the project root: $resolved"
    }
    if ((Test-Path -LiteralPath $resolved) -and (Get-Item -LiteralPath $resolved).PSIsContainer) {
        throw "Conformance report output must be a file path: $resolved"
    }
    return $resolved
}

function New-AutomaticFailureReportPath {
    param([string]$RepoRoot)

    $runId = "run-$([DateTime]::UtcNow.Ticks)-$PID"
    return Join-Path $RepoRoot ".tmp\conformance\$runId\report.json"
}

function Write-DetailedConformanceReport {
    param(
        [string]$Path,
        [object]$Summary
    )

    $parent = Split-Path -Parent $Path
    [void](New-Item -ItemType Directory -Path $parent -Force)
    $serialized = ($Summary | ConvertTo-Json -Depth 100 -Compress) + "`n"
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $serialized, $utf8)
}

function Get-BoundedFailureExcerpt {
    param([object]$Value)

    $normalized = if ($null -eq $Value -or -not ([string]$Value)) {
        'Runner exited without output.'
    }
    else {
        ([string]$Value).Replace("`r`n", "`n").Replace("`r", "`n")
    }
    $lines = @($normalized.Split([char]"`n"))
    $truncated = $lines.Count -gt $failureExcerptLines
    $selectedLines = @($lines | Select-Object -First $failureExcerptLines)
    $excerpt = $selectedLines -join "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($excerpt)
    if ($bytes.Length -gt $failureExcerptBytes) {
        $truncated = $true
        $length = $failureExcerptBytes
        $strictUtf8 = New-Object System.Text.UTF8Encoding($false, $true)
        while ($length -gt 0) {
            try {
                $excerpt = $strictUtf8.GetString($bytes, 0, $length)
                break
            }
            catch [System.Text.DecoderFallbackException] {
                $length--
            }
        }
    }
    return [ordered]@{
        excerpt = $excerpt
        truncated = [bool]$truncated
    }
}

function New-ConciseConformanceSummary {
    param(
        [string]$ProfileId,
        [object[]]$Results,
        [double]$ElapsedSeconds,
        [AllowNull()]
        [string]$ReportPath
    )

    $normalizedReportPath = if ([string]::IsNullOrEmpty($ReportPath)) {
        $null
    }
    else {
        $ReportPath
    }
    $conciseResults = New-Object 'System.Collections.Generic.List[object]'
    $failures = New-Object 'System.Collections.Generic.List[object]'
    foreach ($result in @($Results)) {
        $conciseResults.Add([ordered]@{
                id = [string]$result.id
                kind = $null
                status = [string]$result.status
            })
        if ($result.status -ceq 'failed') {
            $bounded = Get-BoundedFailureExcerpt $result.error
            $failures.Add([ordered]@{
                    classification = 'suite-failure'
                    excerpt = [string]$bounded.excerpt
                    excerpt_truncated = [bool]$bounded.truncated
                    id = [string]$result.id
                })
        }
    }
    $requestedIds = @($Results | ForEach-Object { [string]$_.id })
    return [ordered]@{
        canonical_outputs_unchanged = $null
        contract = 'validation-run-summary'
        contract_version = 1
        elapsed_seconds = [math]::Round($ElapsedSeconds, 3)
        failed = [int]$failures.Count
        failures = $failures.ToArray()
        output_kept = $null -ne $normalizedReportPath
        passed = [int]($Results.Count - $failures.Count)
        profile = $ProfileId
        report_path = $normalizedReportPath
        requested_ids = $requestedIds
        results = $conciseResults.ToArray()
        runner = 'framework-conformance'
        selected_count = [int]$requestedIds.Count
        status = if ($failures.Count -gt 0) {
            'failed'
        }
        else {
            'passed'
        }
    }
}

function New-ConciseConformanceFailure {
    param([object]$ErrorValue)

    $bounded = Get-BoundedFailureExcerpt $ErrorValue
    return [ordered]@{
        canonical_outputs_unchanged = $null
        contract = 'validation-run-summary'
        contract_version = 1
        elapsed_seconds = $null
        failed = 1
        failures = @(
            [ordered]@{
                classification = 'orchestration-failure'
                excerpt = [string]$bounded.excerpt
                excerpt_truncated = [bool]$bounded.truncated
                id = $null
            }
        )
        output_kept = $false
        passed = 0
        profile = $null
        report_path = $null
        requested_ids = @()
        results = @()
        runner = 'framework-conformance'
        selected_count = 0
        status = 'failed'
    }
}

trap {
    if ($SummaryJson) {
        New-ConciseConformanceFailure $_.Exception.Message | ConvertTo-Json -Depth 100 -Compress
    }
    else {
        Write-Error $_
    }
    exit 1
}

if ($Json -and $SummaryJson) {
    throw '-Json and -SummaryJson are mutually exclusive.'
}
if ($List -and ($SummaryJson -or $ReportOutput)) {
    throw '-List cannot be combined with -SummaryJson or -ReportOutput.'
}

$repoRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$reportOutputPath = if ($ReportOutput) {
    Resolve-ConformanceReportOutput $repoRoot $ReportOutput
}
else {
    $null
}
$registry = Get-ConformanceRegistry $repoRoot
if ($List) {
    $listing = [ordered]@{
        profiles = $registry.raw.profiles
        schema_version = 1
        suites = @($registry.suites.Keys)
    }
    if ($Json) {
        $listing | ConvertTo-Json -Depth 20 -Compress
    }
    else {
        $listing | ConvertTo-Json -Depth 20
    }
    exit 0
}

$selection = Get-SelectedSuites $registry $Profile $Suite
$results = New-Object 'System.Collections.Generic.List[object]'
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
foreach ($suiteDefinition in @($selection.suites)) {
    if (-not $Json -and -not $SummaryJson) {
        Write-Output "RUN: $($suiteDefinition.id)"
    }
    $result = Invoke-ConformanceSuite $repoRoot $suiteDefinition
    $results.Add($result)
    if (-not $Json -and -not $SummaryJson) {
        Write-Output "$(([string]$result.status).ToUpper()): $($suiteDefinition.id)"
    }
}
$stopwatch.Stop()
$failed = @($results | Where-Object { $_.status -ceq 'failed' }).Count
$summary = [ordered]@{
    failed = [int]$failed
    passed = [int]($results.Count - $failed)
    profile = [string]$selection.profile
    schema_version = 1
    suite_count = [int]$results.Count
    suites = $results.ToArray()
}
if ($failed -gt 0 -and $null -eq $reportOutputPath -and -not $Json) {
    $reportOutputPath = New-AutomaticFailureReportPath $repoRoot
}
if ($null -ne $reportOutputPath) {
    Write-DetailedConformanceReport $reportOutputPath $summary
}
$reportRelativePath = if ($null -ne $reportOutputPath) {
    $reportOutputPath.Substring($repoRoot.TrimEnd('\').Length + 1).Replace('\', '/')
}
else {
    $null
}
if ($Json) {
    $summary | ConvertTo-Json -Depth 100 -Compress
}
elseif ($SummaryJson) {
    New-ConciseConformanceSummary `
        -ProfileId $selection.profile `
        -Results $results.ToArray() `
        -ElapsedSeconds $stopwatch.Elapsed.TotalSeconds `
        -ReportPath $reportRelativePath |
        ConvertTo-Json -Depth 100 -Compress
}
else {
    Write-Output "Conformance $($selection.profile): $($summary.passed) passed, $($summary.failed) failed."
    if ($null -ne $reportRelativePath) {
        Write-Output "Detailed report: $reportRelativePath"
    }
}
if ($failed -gt 0) {
    exit 1
}
