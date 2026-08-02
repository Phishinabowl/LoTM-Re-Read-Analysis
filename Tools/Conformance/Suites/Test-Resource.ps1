[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force
$Root = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

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

function ConvertTo-MutableFixtureValue {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value -or $Value -is [string] -or $Value.GetType().IsPrimitive) {
        return $Value
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $mapping = [ordered]@{}
        foreach ($key in $Value.Keys) {
            $mapping[[string]$key] = ConvertTo-MutableFixtureValue $Value[$key]
        }
        return $mapping
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $mapping = [ordered]@{}
        foreach ($property in $Value.PSObject.Properties) {
            $mapping[$property.Name] = ConvertTo-MutableFixtureValue $property.Value
        }
        return $mapping
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        $list = New-Object System.Collections.ArrayList
        foreach ($item in $Value) {
            [void]$list.Add((ConvertTo-MutableFixtureValue $item))
        }
        return , $list
    }
    return $Value
}

function Get-FixtureMutationParent {
    param(
        [object]$Document,
        [object[]]$Path
    )

    if ($Path.Count -eq 0) {
        throw 'Fixture mutation path cannot be empty.'
    }
    $current = $Document
    for ($index = 0; $index -lt $Path.Count - 1; $index += 1) {
        $current = $current[$Path[$index]]
    }
    return [pscustomobject]@{
        parent = $current
        final = $Path[$Path.Count - 1]
    }
}

function Invoke-FixtureMutation {
    param(
        [object]$Document,
        [object]$Operation,
        [string]$CaseRoot
    )

    $location = Get-FixtureMutationParent $Document @($Operation.path)
    $operationValue = if (
        $Operation.PSObject.Properties.Name -ccontains 'value_source' -and
        [string]$Operation.value_source -ceq 'absolute-path'
    ) {
        [System.IO.Path]::GetFullPath((Join-Path $CaseRoot '..\outside'))
    }
    elseif ($Operation.PSObject.Properties.Name -ccontains 'value') {
        ConvertTo-MutableFixtureValue $Operation.value
    }
    else {
        $null
    }
    switch ([string]$Operation.op) {
        'set' {
            $location.parent[$location.final] = $operationValue
        }
        'append' {
            $target = $location.parent[$location.final]
            if ($target -isnot [System.Collections.ArrayList]) {
                throw 'Fixture append target must be a mutable list.'
            }
            [void]$target.Add($operationValue)
        }
        'remove' {
            if ($location.parent -is [System.Collections.ArrayList]) {
                $location.parent.RemoveAt([int]$location.final)
            }
            else {
                [void]$location.parent.Remove([string]$location.final)
            }
        }
        default {
            throw "Unknown fixture mutation operation: $($Operation.op)"
        }
    }
}

function Write-FixtureJson {
    param(
        [string]$Path,
        [object]$Value
    )

    $content = ($Value | ConvertTo-Json -Depth 100) + [Environment]::NewLine
    [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
}

function New-FixtureProject {
    param(
        [object]$Project,
        [string]$FixtureRoot
    )

    $fixtureProject = $Project.PSObject.Copy()
    $fixtureProject.root = $FixtureRoot
    $fixtureProject.resources_registry = Join-Path $FixtureRoot 'registry.json'
    $fixtureProject.resource_roots = @(
        [pscustomobject]@{
            id = 'documents'
            relative_path = 'documents'
            path = Join-Path $FixtureRoot 'documents'
            required = $false
        }
        [pscustomobject]@{
            id = 'evidence-store'
            relative_path = 'evidence'
            path = Join-Path $FixtureRoot 'evidence'
            required = $false
        }
        [pscustomobject]@{
            id = 'generated'
            relative_path = 'generated'
            path = Join-Path $FixtureRoot 'generated'
            required = $false
        }
        [pscustomobject]@{
            id = 'workspace'
            relative_path = 'workspace'
            path = Join-Path $FixtureRoot 'workspace'
            required = $false
        }
    )
    return $fixtureProject
}

function Assert-ValidResourceFixture {
    param(
        [object]$Registry,
        [object]$Expected
    )

    if ($Registry.kinds.Count -ne [int]$Expected.resource_kinds) {
        throw 'Resource fixture kind count changed.'
    }
    if ($Registry.types.Count -ne [int]$Expected.resource_types) {
        throw 'Resource fixture type count changed.'
    }
    $activeTypes = @($Registry.types.Values | Where-Object lifecycle -eq 'active')
    if ($activeTypes.Count -ne [int]$Expected.active_resource_types) {
        throw 'Resource fixture active-type count changed.'
    }
    $authorities = @($Registry.types.Values | ForEach-Object authority | Sort-Object -Unique)
    if (($authorities -join '|') -cne (@($Expected.authority_values | Sort-Object) -join '|')) {
        throw 'Resource fixture authority coverage changed.'
    }
    $tracking = @(
        $Registry.types.Values |
            ForEach-Object placements |
            ForEach-Object tracking |
            Sort-Object -Unique
    )
    if (($tracking -join '|') -cne (@($Expected.tracking_values | Sort-Object) -join '|')) {
        throw 'Resource fixture tracking coverage changed.'
    }
    $generatedRoots = @($Registry.types['generated-preview'].placements | ForEach-Object root_id)
    if (($generatedRoots -join '|') -cne (@($Expected.generated_preview_roots) -join '|')) {
        throw 'Resource multi-placement order changed.'
    }
    if (@($Registry.types['future-export'].placements).Count -ne [int]$Expected.deferred_placement_count) {
        throw 'Deferred resource placement behavior changed.'
    }
    $requiredPath = $Registry.types['canonical-document'].placements[0].path
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw 'Required resource placement did not resolve to the fixture tree.'
    }
    $provider = Get-KnowledgeResourceReconciliationProvider $Registry
    if ([string]$provider.provider_id -cne 'resource') {
        throw 'Resource reconciliation provider ID changed.'
    }
    if (($provider.targets.Keys -join '|') -cne (@($Expected.reconciliation_target_types) -join '|')) {
        throw 'Resource reconciliation target order changed.'
    }
    $kindTarget = Get-KnowledgeResourceReconciliationTarget $Registry 'resource-kind' 'document'
    if (-not [object]::ReferenceEquals($kindTarget, $Registry.kinds['document'])) {
        throw 'Resource-kind reconciliation lookup changed.'
    }
    $typeTarget = Get-KnowledgeResourceReconciliationTarget $Registry 'resource-type' 'canonical-document'
    if (-not [object]::ReferenceEquals($typeTarget, $Registry.types['canonical-document'])) {
        throw 'Resource-type reconciliation lookup changed.'
    }
}

function New-ScaleResourceFixture {
    param(
        [string]$FixtureRoot,
        [int]$TypeCount
    )

    $types = [ordered]@{}
    for ($index = 0; $index -lt $TypeCount; $index += 1) {
        $typeId = 'scale-resource-{0:d3}' -f $index
        $types[$typeId] = [ordered]@{
            lifecycle = 'active'
            label = 'Scale Resource {0:d3}' -f $index
            plural_label = 'Scale Resources {0:d3}' -f $index
            kind_id = 'scale-kind'
            authority = 'supporting'
            editor_enabled = $false
            placements = @(
                [ordered]@{
                    root_id = 'generated'
                    relative_path = 'scale/{0:d3}' -f $index
                    tracking = 'ignored'
                    required = $false
                }
            )
        }
    }
    $registry = [ordered]@{
        schema_version = 1
        resource_kinds = [ordered]@{
            'scale-kind' = [ordered]@{
                label = 'Scale Kind'
                plural_label = 'Scale Kinds'
            }
        }
        resource_types = $types
    }
    Write-FixtureJson (Join-Path $FixtureRoot 'registry.json') $registry
}

$project = Get-KnowledgeProjectConfig $Root
$canonical = Get-KnowledgeResourceConfig $project
$fixtureRoot = Join-Path $Root 'Framework\Data\Resources'
$baseRoot = Join-Path $fixtureRoot 'base'
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw |
    ConvertFrom-Json
if ([int]$expectations.schema_version -ne 1) {
    throw 'Unsupported resource conformance expectation schema.'
}
$baseDocument = ConvertTo-MutableFixtureValue (
    Get-Content -LiteralPath (Join-Path $baseRoot 'registry.json') -Raw | ConvertFrom-Json
)

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('knowledge-resource-' + [guid]::NewGuid().ToString('N'))
try {
    [void](New-Item -ItemType Directory -Path $tempRoot)
    $validRoot = Join-Path $tempRoot 'valid'
    Copy-Item -LiteralPath $baseRoot -Destination $validRoot -Recurse
    $fixtureRegistry = Get-KnowledgeResourceConfig (New-FixtureProject $project $validRoot)
    Assert-ValidResourceFixture $fixtureRegistry $expectations.valid
    Assert-Rejected {
        Get-KnowledgeResourceReconciliationTarget $fixtureRegistry 'unknown' 'document'
    } 'Unsupported resource reconciliation target type was accepted.'
    Assert-Rejected {
        Get-KnowledgeResourceReconciliationTarget $fixtureRegistry 'resource-kind' 'unknown'
    } 'Unknown resource reconciliation target was accepted.'

    foreach ($case in $expectations.invalid_cases) {
        $caseRoot = Join-Path $tempRoot ([string]$case.id)
        Copy-Item -LiteralPath $baseRoot -Destination $caseRoot -Recurse
        $document = ConvertTo-MutableFixtureValue $baseDocument
        foreach ($operation in $case.operations) {
            Invoke-FixtureMutation $document $operation $caseRoot
        }
        Write-FixtureJson (Join-Path $caseRoot 'registry.json') $document
        $caseProject = New-FixtureProject $project $caseRoot
        Assert-Rejected {
            Get-KnowledgeResourceConfig $caseProject
        } "Malformed resource configuration was accepted: $($case.id)"
    }

    $scaleRoot = Join-Path $tempRoot 'scale'
    [void](New-Item -ItemType Directory -Path $scaleRoot)
    $scaleCount = [int]$expectations.scale_resource_type_count
    New-ScaleResourceFixture $scaleRoot $scaleCount
    $scaleRegistry = Get-KnowledgeResourceConfig (New-FixtureProject $project $scaleRoot)
    if ($scaleRegistry.kinds.Count -ne 1 -or $scaleRegistry.types.Count -ne $scaleCount) {
        throw 'Resource scale composition counts changed.'
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    schema_version = 1
    canonical_resource_kinds = $canonical.kinds.Count
    canonical_resource_types = $canonical.types.Count
    fixture_resource_kinds = $fixtureRegistry.kinds.Count
    fixture_resource_types = $fixtureRegistry.types.Count
    fixture_active_resource_types = @($fixtureRegistry.types.Values | Where-Object lifecycle -eq 'active').Count
    invalid_configuration_cases = @($expectations.invalid_cases).Count
    invalid_query_cases = [int]$expectations.invalid_query_cases
    scale_resource_type_count = $scaleCount
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Host (
        'Resource conformance passed: {0} canonical kinds, {1} canonical types, ' +
        '{2} malformed configurations, and {3} scale resource types.' -f
        $summary.canonical_resource_kinds,
        $summary.canonical_resource_types,
        $summary.invalid_configuration_cases,
        $summary.scale_resource_type_count
    )
}
