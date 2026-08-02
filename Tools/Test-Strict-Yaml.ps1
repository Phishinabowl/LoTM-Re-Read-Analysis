[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent $PSScriptRoot
}
$Root = [System.IO.Path]::GetFullPath($Root)

. (Join-Path $PSScriptRoot 'Strict-Yaml.ps1')

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

function Test-JsonInteger {
    param([object]$Value)

    return (
        $Value -is [sbyte] -or $Value -is [byte] -or
        $Value -is [int16] -or $Value -is [uint16] -or
        $Value -is [int32] -or $Value -is [uint32] -or
        $Value -is [int64] -or $Value -is [uint64]
    )
}

$fixtures = Join-Path $Root 'Framework\Data\Strict-Yaml'
$expectations = Get-Content -Raw (Join-Path $fixtures 'expectations.json') | ConvertFrom-Json
if (-not (Test-JsonInteger $expectations.schema_version) -or [int]$expectations.schema_version -ne 1) {
    throw 'Unsupported strict-YAML expectation schema.'
}
$mappingKeys = ConvertFrom-KnowledgeYamlFile (Join-Path $fixtures 'valid-mapping-keys.yaml') 1 'Strict YAML fixture'
$expectedKeys = @('1', 'true', 'on', 'dotted.key', 'hyphen-key', 'underscore_key')
$actualKeys = @($mappingKeys.mapping_keys.Keys | Sort-Object)
if (($actualKeys -join '|') -cne (($expectedKeys | Sort-Object) -join '|')) {
    throw 'Canonical mapping-key fixture did not preserve string keys.'
}
foreach ($key in $actualKeys) {
    if ($key -isnot [string]) {
        throw 'Canonical mapping-key fixture produced a non-string key.'
    }
}

$scalars = ConvertFrom-KnowledgeYamlFile (Join-Path $fixtures 'valid-scalars.yaml') 1 'Strict YAML fixture'
if (
    $scalars.Count -ne 13 -or -not $scalars.Contains('explicit_null') -or
    $scalars.boolean_true -isnot [bool] -or -not $scalars.boolean_true -or
    $scalars.boolean_false -isnot [bool] -or $scalars.boolean_false -or
    $null -ne $scalars.explicit_null -or
    $scalars.zero -isnot [int] -or $scalars.zero -ne 0 -or
    $scalars.negative_integer -isnot [int] -or $scalars.negative_integer -ne -12 -or
    $scalars.positive_integer -isnot [int] -or $scalars.positive_integer -ne 12 -or
    [string]$scalars.legacy_on -cne 'on' -or
    [string]$scalars.legacy_off -cne 'off' -or
    [string]$scalars.legacy_yes -cne 'yes' -or
    [string]$scalars.legacy_no -cne 'no' -or
    [string]$scalars.quoted_decimal -cne '1.5' -or
    [string]$scalars.quoted_timestamp -cne '2026-08-02T12:34:56Z'
) {
    throw 'Portable scalar fixture did not retain exact values and types.'
}

$invalidMappingFixtures = @(
    'invalid-boolean-key.yaml'
    'invalid-integer-key.yaml'
    'invalid-empty-key.yaml'
    'invalid-uppercase-key.yaml'
    'invalid-case-collision.yaml'
    'invalid-unicode-key.yaml'
    'invalid-punctuation-key.yaml'
    'invalid-complex-key.yaml'
    'invalid-duplicate-key.yaml'
)
foreach ($name in $invalidMappingFixtures) {
    Assert-Rejected {
        $null = ConvertFrom-KnowledgeYamlFile (Join-Path $fixtures $name) 1 'Strict YAML fixture'
    } "Noncanonical mapping-key fixture was accepted: $name"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-strict-yaml-{0}" -f [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
try {
    foreach ($case in @($expectations.invalid_sources)) {
        $path = Join-Path $tempRoot ("{0}.yaml" -f $case.id)
        [System.IO.File]::WriteAllText($path, [string]$case.source, [System.Text.UTF8Encoding]::new($false))
        Assert-Rejected {
            $null = ConvertFrom-KnowledgeYamlFile $path 1 'Strict YAML fixture'
        } "Nonportable YAML source was accepted: $($case.id)"
    }

    $validBytes = [System.IO.File]::ReadAllBytes((Join-Path $fixtures 'valid-scalars.yaml'))
    $bomPath = Join-Path $tempRoot 'utf8-bom.yaml'
    $bomBytes = [byte[]]::new($validBytes.Length + 3)
    $bomPrefix = [byte[]](0xEF, 0xBB, 0xBF)
    $bomPrefix.CopyTo($bomBytes, 0)
    $validBytes.CopyTo($bomBytes, 3)
    [System.IO.File]::WriteAllBytes($bomPath, $bomBytes)
    Assert-Rejected {
        $null = ConvertFrom-KnowledgeYamlFile $bomPath 1 'Strict YAML fixture'
    } 'UTF-8 BOM fixture was accepted.'

    $invalidUtf8Path = Join-Path $tempRoot 'invalid-utf8.yaml'
    [System.IO.File]::WriteAllBytes(
        $invalidUtf8Path,
        [byte[]](0x73, 0x63, 0x68, 0x65, 0x6D, 0x61, 0x5F, 0x76, 0x65, 0x72, 0x73, 0x69, 0x6F, 0x6E, 0x3A, 0x20, 0x31, 0x0A, 0xFF)
    )
    Assert-Rejected {
        $null = ConvertFrom-KnowledgeYamlFile $invalidUtf8Path 1 'Strict YAML fixture'
    } 'Malformed UTF-8 fixture was accepted.'

    $budgetPath = Join-Path $tempRoot 'budget.yaml'
    Assert-Rejected {
        Assert-KnowledgeYamlSource "value: 12`n" 'Test registry' $budgetPath -MaxBytes 9
    } 'YAML file-byte budget was not enforced.'
    $emoji = [char]::ConvertFromUtf32(0x1F600)
    Assert-Rejected {
        Assert-KnowledgeYamlSource "value: $emoji$emoji`n" 'Test registry' $budgetPath -MaxScalarBytes 7
    } 'YAML scalar-byte budget was not enforced.'
    Assert-Rejected {
        Assert-KnowledgeYamlSource "value: [1, 2, 3]`n" 'Test registry' $budgetPath -MaxNodes 3
    } 'YAML node-count budget was not enforced.'
    Assert-Rejected {
        Assert-KnowledgeYamlSource "value: [[[[0]]]]`n" 'Test registry' $budgetPath -MaxDepth 3
    } 'YAML nesting-depth budget was not enforced.'
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

foreach ($codePoints in @($expectations.rfc3339_valid)) {
    $value = -join @($codePoints | ForEach-Object { [char][int]$_ })
    if (-not (Test-KnowledgeRfc3339Timestamp $value)) {
        throw "Valid RFC 3339 timestamp was rejected: $value"
    }
}
foreach ($codePoints in @($expectations.rfc3339_invalid)) {
    $value = -join @($codePoints | ForEach-Object { [char][int]$_ })
    if (Test-KnowledgeRfc3339Timestamp $value) {
        throw "Invalid RFC 3339 timestamp was accepted: $value"
    }
}

$summary = [ordered]@{
    budget_cases = 4
    byte_cases = 2
    invalid_mapping_key_fixtures = [int]$invalidMappingFixtures.Count
    invalid_source_cases = [int]@($expectations.invalid_sources).Count
    rfc3339_invalid_cases = [int]@($expectations.rfc3339_invalid).Count
    rfc3339_valid_cases = [int]@($expectations.rfc3339_valid).Count
    schema_version = 1
    valid_scalar_cases = 12
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Strict YAML conformance passed: {0} scalar, {1} mapping-key, {2} source, {3} byte, ' +
        '{4} budget, and {5} timestamp cases.' -f
        $summary.valid_scalar_cases,
        $summary.invalid_mapping_key_fixtures,
        $summary.invalid_source_cases,
        $summary.byte_cases,
        $summary.budget_cases,
        ($summary.rfc3339_valid_cases + $summary.rfc3339_invalid_cases)
    )
}
