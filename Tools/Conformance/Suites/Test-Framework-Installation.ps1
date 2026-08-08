[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)

    $parent = [System.IO.Path]::GetDirectoryName($Path)
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        $null = New-Item -ItemType Directory -Path $parent -Force
    }
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

function New-TestFrameworkMarker {
    param([string]$Path)

    Write-Utf8NoBom (Join-Path $Path 'Framework\framework.yaml') "schema_version: 1`n"
    return [System.IO.Path]::GetFullPath($Path)
}

function Assert-Rejected {
    param(
        [scriptblock]$Action,
        [string]$ExpectedText
    )

    try {
        & $Action
    }
    catch {
        if (-not $_.Exception.Message.Contains($ExpectedText)) {
            throw "Expected error containing '$ExpectedText', got: $($_.Exception.Message)"
        }
        return
    }
    throw "Expected rejection containing '$ExpectedText'."
}

function New-ConfigRoot {
    param(
        [string]$SourceRoot,
        [string]$TargetRoot,
        [string]$ManifestSource
    )

    $framework = Join-Path $TargetRoot 'Framework'
    $null = New-Item -ItemType Directory -Path (Join-Path $framework 'Packs') -Force
    $data = Join-Path $framework 'Data'
    $null = New-Item -ItemType Directory -Path $data
    Copy-Item `
        -LiteralPath (Join-Path $SourceRoot 'Framework\Data\unicode-lookup-16.0.0.json') `
        -Destination $data
    Copy-Item -LiteralPath $ManifestSource -Destination (Join-Path $framework 'framework.yaml')
    return [System.IO.Path]::GetFullPath($TargetRoot)
}

$actualRoot = Resolve-KnowledgeFrameworkRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$fixtureRoot = Join-Path $actualRoot 'Framework\Data\Framework-Installation'
$expectations = ConvertFrom-Json -InputObject ([System.IO.File]::ReadAllText((Join-Path $fixtureRoot 'expectations.json')))
$originalLocation = (Get-Location).Path
$originalEnvironmentRoot = [Environment]::GetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT')
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('knowledge-framework-installation-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
$rootVectors = 0
$configVectors = 0

try {
    $frameworkA = New-TestFrameworkMarker (Join-Path $tempRoot 'framework-a')
    $frameworkB = New-TestFrameworkMarker (Join-Path $tempRoot 'framework-b')
    $nestedA = Join-Path $frameworkA 'one\two'
    $null = New-Item -ItemType Directory -Path $nestedA -Force
    $nestedB = Join-Path $frameworkB 'nested'
    $null = New-Item -ItemType Directory -Path $nestedB
    $executableB = Join-Path $nestedB 'command.ps1'
    Write-Utf8NoBom $executableB "# fixture`n"
    $unrelated = Join-Path $tempRoot 'unrelated'
    $null = New-Item -ItemType Directory -Path $unrelated
    $unrelatedExecutable = Join-Path $unrelated 'command.ps1'
    Write-Utf8NoBom $unrelatedExecutable "# fixture`n"
    $gitOnly = Join-Path $tempRoot 'git-only'
    $null = New-Item -ItemType Directory -Path (Join-Path $gitOnly '.git') -Force

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT', $frameworkB)
    if ((Resolve-KnowledgeFrameworkRoot -ExplicitRoot $actualRoot) -cne $actualRoot) {
        throw 'Explicit framework root did not take precedence over the environment override.'
    }
    $rootVectors++
    if ((Resolve-KnowledgeFrameworkRoot) -cne $frameworkB) {
        throw 'Environment framework root did not resolve.'
    }
    $rootVectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT', $unrelated)
    Assert-Rejected { Resolve-KnowledgeFrameworkRoot } 'missing required manifest'
    $rootVectors++
    [Environment]::SetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT', 'relative/framework')
    Assert-Rejected { Resolve-KnowledgeFrameworkRoot } 'must be an absolute path'
    $rootVectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT', $null)
    if ((Resolve-KnowledgeFrameworkRoot -CurrentDirectory $nestedA) -cne $frameworkA) {
        throw 'Current-directory framework ancestry did not resolve.'
    }
    $rootVectors++
    if ((Resolve-KnowledgeFrameworkRoot -ExecutablePath $executableB -CurrentDirectory $unrelated) -cne $frameworkB) {
        throw 'Executable framework ancestry did not resolve after current-directory search failed.'
    }
    $rootVectors++
    if ((Resolve-KnowledgeFrameworkRoot -ExecutablePath $executableB -CurrentDirectory $nestedA) -cne $frameworkA) {
        throw 'Current-directory framework ancestry did not take precedence over executable ancestry.'
    }
    $rootVectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT', $frameworkB)
    if ((Resolve-KnowledgeFrameworkRoot -ExecutablePath $executableB -CurrentDirectory $nestedA) -cne $frameworkB) {
        throw 'Environment framework root did not take precedence over ancestry searches.'
    }
    $rootVectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT', $null)
    Assert-Rejected {
        Resolve-KnowledgeFrameworkRoot -ExecutablePath $unrelatedExecutable -CurrentDirectory $gitOnly
    } 'Could not auto-detect'
    $rootVectors++
    Assert-Rejected {
        Resolve-KnowledgeFrameworkRoot -ExecutablePath $unrelatedExecutable -CurrentDirectory $unrelated
    } 'Expected manifest: Framework/framework.yaml'
    $rootVectors++
    if ((Get-Location).Path -cne $originalLocation) {
        throw 'Framework-root discovery changed the working directory.'
    }
    $rootVectors++

    $canonical = Get-KnowledgeFrameworkConfig $actualRoot
    if ($canonical.framework_id -cne $expectations.framework_id) {
        throw 'Canonical framework ID differs from expectations.'
    }
    if ($canonical.packs_relative_path -cne $expectations.packs_relative_path) {
        throw 'Canonical pack-root path differs from expectations.'
    }
    if ($canonical.lookup_keys_relative_path -cne $expectations.lookup_keys_relative_path) {
        throw 'Canonical lookup-registry path differs from expectations.'
    }
    if ($canonical.lookup_keys.unicode_version -cne $expectations.unicode_version) {
        throw 'Canonical lookup Unicode version differs from expectations.'
    }
    if ($canonical.lookup_keys.algorithm -cne $expectations.algorithm) {
        throw 'Canonical lookup algorithm differs from expectations.'
    }
    $configVectors++

    $multiRoot = New-ConfigRoot `
        $actualRoot `
    (Join-Path $tempRoot 'multiple-lookups') `
    (Join-Path $actualRoot 'Framework\framework.yaml')
    Write-Utf8NoBom `
    (Join-Path $multiRoot 'Framework\Data\unicode-lookup-99.0.0.json') `
        "{`"schema_version`":0}`n"
    $multiple = Get-KnowledgeFrameworkConfig $multiRoot
    if ($multiple.lookup_keys.unicode_version -cne $expectations.unicode_version) {
        throw 'Framework configuration inferred the wrong lookup registry when multiple datasets existed.'
    }
    $configVectors++

    $caseIndex = 0
    foreach ($case in @($expectations.invalid_cases)) {
        $caseRoot = New-ConfigRoot `
            $actualRoot `
        (Join-Path $tempRoot "invalid-$caseIndex") `
        (Join-Path $fixtureRoot $case.file)
        Copy-Item `
            -LiteralPath (Join-Path $fixtureRoot 'invalid-lookup.json') `
            -Destination (Join-Path $caseRoot 'Framework\Data\invalid-lookup.json')
        Assert-Rejected { Get-KnowledgeFrameworkConfig $caseRoot } $case.error
        $configVectors++
        $caseIndex++
    }
}
finally {
    [Environment]::SetEnvironmentVariable('KNOWLEDGE_FRAMEWORK_ROOT', $originalEnvironmentRoot)
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

if ($rootVectors -ne [int]$expectations.root_vectors) {
    throw "Expected $($expectations.root_vectors) root vectors, got $rootVectors."
}

$summary = [ordered]@{
    algorithm = [string]$expectations.algorithm
    config_vectors = $configVectors
    environment_variable = 'KNOWLEDGE_FRAMEWORK_ROOT'
    framework_id = [string]$expectations.framework_id
    invalid_cases = @($expectations.invalid_cases).Count
    marker = 'Framework/framework.yaml'
    root_vectors = $rootVectors
    schema_version = [int]$expectations.schema_version
    unicode_version = [string]$expectations.unicode_version
    working_directory_preserved = (Get-Location).Path -ceq $originalLocation
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Framework-installation conformance passed: ' +
        "$rootVectors root vectors, $configVectors config vectors, " +
        "$(@($expectations.invalid_cases).Count) invalid cases."
    )
}
