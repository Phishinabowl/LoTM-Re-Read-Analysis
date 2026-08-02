[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Project-Config.ps1')
. (Join-Path $PSScriptRoot 'Lookup-Key-Config.ps1')
$Root = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath

function ConvertFrom-TestCodePoints {
    param([object[]]$CodePoints)

    $builder = New-Object System.Text.StringBuilder
    foreach ($codePoint in @($CodePoints)) {
        [void]$builder.Append([char]::ConvertFromUtf32([int]$codePoint))
    }
    return , $builder.ToString()
}

function Assert-Rejected {
    param(
        [scriptblock]$Action,
        [string]$Message
    )

    $rejected = $false
    try {
        & $Action
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw $Message
    }
}

function Set-InvalidLookupRegistryCase {
    param(
        [object]$Registry,
        [string]$CaseId
    )

    switch ($CaseId) {
        'unknown-root-field' {
            $Registry | Add-Member -NotePropertyName unexpected -NotePropertyValue $true
        }
        'schema-version-string' {
            $Registry.schema_version = '1'
        }
        'unsupported-algorithm' {
            $Registry.algorithm = 'runtime-default'
        }
        'trim-not-array' {
            $Registry.trim_codepoints = '32'
        }
        'trim-surrogate' {
            $Registry.trim_codepoints = @([int]0xD800)
        }
        'case-folding-invalid-key' {
            $Registry.case_folding = '{"D800":[97]}' | ConvertFrom-Json
        }
        'case-folding-empty-sequence' {
            $Registry.case_folding = '{"0041":[]}' | ConvertFrom-Json
        }
        'case-folding-noninteger-sequence' {
            $Registry.case_folding = '{"0041":["97"]}' | ConvertFrom-Json
        }
        'combining-class-zero' {
            $Registry.canonical_combining_class = '{"0300":0}' | ConvertFrom-Json
        }
        'composition-malformed-key' {
            $Registry.canonical_composition = '{"0041":65}' | ConvertFrom-Json
        }
        'composition-surrogate-target' {
            $Registry.canonical_composition = '{"0041+0300":55296}' | ConvertFrom-Json
        }
        'declared-count-mismatch' {
            $Registry.counts.case_folding = [int]$Registry.counts.case_folding + 1
        }
        default {
            throw "Unknown lookup-key mutation case: $CaseId"
        }
    }
    return $Registry
}

$project = Get-KnowledgeProjectConfig $Root
$config = Get-KnowledgeLookupKeyConfig $project
$dataRoot = Join-Path $Root 'Framework\Data'
$vectors = Get-Content -Raw (Join-Path $dataRoot 'lookup-key-regression-vectors.json') | ConvertFrom-Json
$invalid = Get-Content -Raw (Join-Path $dataRoot 'Lookup-Key\invalid-cases.json') | ConvertFrom-Json
if (
    -not (Test-KnowledgeJsonInteger $vectors.schema_version) -or [int]$vectors.schema_version -ne 1 -or
    [string]$vectors.algorithm -cne [string]$config.algorithm
) {
    throw 'Lookup-key vector schema or algorithm does not match the loaded registry.'
}
if (-not (Test-KnowledgeJsonInteger $invalid.schema_version) -or [int]$invalid.schema_version -ne 1) {
    throw 'Unsupported malformed lookup-key fixture schema.'
}

foreach ($case in @($vectors.equivalent)) {
    $left = ConvertTo-KnowledgeLookupKey (ConvertFrom-TestCodePoints $case.left) $config
    $right = ConvertTo-KnowledgeLookupKey (ConvertFrom-TestCodePoints $case.right) $config
    if (-not (Test-KnowledgeLookupKeysEqual $left $right)) {
        throw "Equivalent lookup-key vector remained distinct: $($case.id)"
    }
}
foreach ($case in @($vectors.distinct)) {
    $left = ConvertTo-KnowledgeLookupKey (ConvertFrom-TestCodePoints $case.left) $config
    $right = ConvertTo-KnowledgeLookupKey (ConvertFrom-TestCodePoints $case.right) $config
    if (Test-KnowledgeLookupKeysEqual $left $right) {
        throw "Distinct lookup-key vector collided: $($case.id)"
    }
}
foreach ($case in @($vectors.normalized)) {
    $actualValue = ConvertTo-KnowledgeLookupKey (ConvertFrom-TestCodePoints $case.input) $config
    $actual = @((ConvertTo-KnowledgeCodePoints $actualValue) | ForEach-Object { [int]$_ })
    $expected = @($case.expected | ForEach-Object { [int]$_ })
    if (($actual -join ',') -cne ($expected -join ',')) {
        throw "Lookup-key normalized output differed: $($case.id)"
    }
}

Assert-Rejected {
    $null = ConvertTo-KnowledgeLookupKey 123 $config
} 'Non-string lookup-key input was accepted.'
$unpairedSurrogate = [string][char]0xD800
Assert-Rejected {
    $null = ConvertTo-KnowledgeLookupKey $unpairedSurrogate $config
} 'Unpaired-surrogate lookup-key input was accepted.'

$canonicalPath = [System.IO.Path]::GetFullPath($project.lookup_keys_registry)
$canonicalJson = [System.IO.File]::ReadAllText($canonicalPath, [System.Text.Encoding]::ASCII)
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-lookup-key-{0}" -f [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
try {
    foreach ($case in @($invalid.cases)) {
        $path = Join-Path $tempRoot ("{0}.json" -f $case.id)
        if ($case.id -ceq 'malformed-json') {
            $content = '{"schema_version":1,'
        }
        else {
            $registry = $canonicalJson | ConvertFrom-Json
            $registry = Set-InvalidLookupRegistryCase $registry ([string]$case.id)
            $content = $registry | ConvertTo-Json -Depth 100 -Compress
        }
        [System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::ASCII)
        $testProject = $project.PSObject.Copy()
        $testProject.lookup_keys_registry = [System.IO.Path]::GetFullPath($path)
        Assert-Rejected {
            $null = Get-KnowledgeLookupKeyConfig $testProject
        } "Malformed lookup-key registry was accepted: $($case.id)"
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    distinct_vectors = [int]@($vectors.distinct).Count
    equivalent_vectors = [int]@($vectors.equivalent).Count
    invalid_input_cases = 2
    invalid_registry_cases = [int]@($invalid.cases).Count
    normalized_vectors = [int]@($vectors.normalized).Count
    schema_version = 1
    unicode_version = [string]$config.unicode_version
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Lookup-key conformance passed: Unicode {0}, {1} equivalent, {2} distinct, {3} exact-output, ' +
        '{4} malformed-registry, and {5} invalid-input cases.' -f
        $summary.unicode_version,
        $summary.equivalent_vectors,
        $summary.distinct_vectors,
        $summary.normalized_vectors,
        $summary.invalid_registry_cases,
        $summary.invalid_input_cases
    )
}
