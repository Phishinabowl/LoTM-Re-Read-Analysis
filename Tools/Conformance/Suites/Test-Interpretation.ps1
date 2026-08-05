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
    param([scriptblock]$Action, [string]$Message)

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
    param([object]$Document, [object[]]$Path)

    if ($Path.Count -eq 0) {
        throw 'Fixture mutation path cannot be empty.'
    }
    $current = $Document
    for ($index = 0; $index -lt $Path.Count - 1; $index += 1) {
        $current = $current[$Path[$index]]
    }
    return [pscustomobject]@{ parent = $current
        final = $Path[$Path.Count - 1]
    }
}

function Invoke-FixtureMutation {
    param([object]$Document, [object]$Operation)

    $location = Get-FixtureMutationParent $Document @($Operation.path)
    $value = if ($Operation.PSObject.Properties.Name -ccontains 'value') {
        ConvertTo-MutableFixtureValue $Operation.value
    }
    else {
        $null
    }
    switch ([string]$Operation.op) {
        'set' {
            $location.parent[$location.final] = $value
        }
        'append' {
            $target = $location.parent[$location.final]
            if ($target -isnot [System.Collections.ArrayList]) {
                throw 'Fixture append target must be a mutable list.'
            }
            [void]$target.Add($value)
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
    param([string]$Path, [object]$Value)

    $content = ($Value | ConvertTo-Json -Depth 100) + [Environment]::NewLine
    [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
}

function New-FixtureProvider {
    param([string]$ProviderId, [object]$Targets)

    $resolver = {
        param($Type, $Id)
        if (-not $Targets.Contains($Type) -or -not $Targets[$Type].Contains($Id)) {
            throw "Unknown fixture target '$Type`:$Id'."
        }
        return $Targets[$Type][$Id]
    }.GetNewClosure()
    return New-KnowledgeInterpretationTargetProvider $ProviderId @($Targets.Keys) $resolver
}

function New-FixtureTargetMap {
    param([string]$TargetType, [string[]]$Ids)

    $records = @{}
    foreach ($id in $Ids) {
        $records[$id] = [pscustomobject]@{ id = $id }
    }
    return @{ $TargetType = $records }
}

function Get-FixtureProviders {
    return @(
        (New-FixtureProvider `
            'occurrence' `
        (New-FixtureTargetMap 'occurrence' @('first-occurrence', 'second-occurrence')))
        (New-FixtureProvider 'entity' (New-FixtureTargetMap 'entity' @('observer-entity')))
        (New-FixtureProvider 'chronology' (New-FixtureTargetMap 'chronology-position' @('shared-position')))
    )
}

function Get-FixtureRegistry {
    param(
        [object]$Project,
        [object]$Packs,
        [object[]]$Providers,
        [string]$FixtureRoot
    )

    $fixture = $Project.PSObject.Copy()
    $fixture.interpretations_registry = Join-Path $FixtureRoot 'registry.json'
    return Get-KnowledgeInterpretationRegistry $fixture $Packs $Providers
}

function Assert-FixtureCounts {
    param([object]$Registry, [object]$Expected)

    foreach ($field in @('relation_types', 'interpretations', 'members', 'relations', 'comparison_sets')) {
        $value = $Registry.$field
        $count = if ($value -is [System.Collections.IDictionary]) {
            $value.Count
        }
        else {
            @($value).Count
        }
        if ($count -ne [int]$Expected.$field) {
            throw "Structural interpretation fixture '$field' count changed."
        }
    }
    $targetTypes = Get-KnowledgeInterpretationProvenanceTargets $Registry
    if ($targetTypes.Count -ne [int]$Expected.provenance_target_types) {
        throw 'Structural interpretation provenance target-type count changed.'
    }
}

function Assert-FixtureServices {
    param([object]$Registry, [string[]]$ClaimKeys)

    Assert-KnowledgeInterpretationClaimTargets $Registry $ClaimKeys
    $structure = Get-KnowledgeInterpretationStructure $Registry 'forward-reconstruction'
    if (@($structure.members.id) -join ',' -cne 'forward-first,forward-second,forward-claim') {
        throw 'Structural interpretation member query changed.'
    }
    if (@($structure.relations.id) -join ',' -cne 'forward-order,forward-claim-cause') {
        throw 'Structural interpretation relation query changed.'
    }
    $sets = Get-KnowledgeInterpretationComparisonSets $Registry 'forward-reconstruction'
    if (@($sets.id) -join ',' -cne 'order-alternatives,research-candidates') {
        throw 'Structural interpretation comparison-set query changed.'
    }
    $unresolved = Get-KnowledgeInterpretationSetDecision $Registry 'order-alternatives'
    if ($unresolved.disposition -cne 'unresolved' -or @($unresolved.selected_interpretation_ids).Count -ne 0) {
        throw 'Mutually exclusive interpretation set no longer remains unresolved.'
    }
    $compatible = Get-KnowledgeInterpretationSetDecision $Registry 'compatible-contexts'
    if ($compatible.disposition -cne 'compatible' -or @($compatible.selected_interpretation_ids).Count -ne 0) {
        throw 'Compatible interpretation decision changed.'
    }
    $target = Get-KnowledgeInterpretationProvenanceTarget `
        $Registry `
        'structural-interpretation-relation' `
        'forward-order'
    if ($target.relationship_type -cne 'precedes') {
        throw 'Structural interpretation provenance lookup changed.'
    }
}

function Assert-InvalidQueries {
    param([object]$Registry)

    $actions = @(
        { Get-KnowledgeInterpretationMembers $Registry 'unknown' }
        { Get-KnowledgeInterpretationRelations $Registry 'unknown' }
        { Get-KnowledgeInterpretationComparisonSets $Registry 'unknown' }
        { Get-KnowledgeInterpretationStructure $Registry 'unknown' }
        { Get-KnowledgeInterpretationSetDecision $Registry 'unknown' }
        { Get-KnowledgeInterpretationProvenanceTarget $Registry 'unknown' 'forward-reconstruction' }
        { Get-KnowledgeInterpretationProvenanceTarget $Registry 'structural-interpretation' 'unknown' }
        { Assert-KnowledgeInterpretationClaimTargets $Registry @() }
    )
    foreach ($action in $actions) {
        Assert-Rejected $action 'Structural interpretation invalid query unexpectedly succeeded.'
    }
    return $actions.Count
}

function Assert-Scale {
    param(
        [object]$Project,
        [object]$Packs,
        [object]$Base,
        [string]$FixtureRoot
    )

    $scale = ConvertTo-MutableFixtureValue $Base
    $scale['interpretations'] = [ordered]@{
        'scale-reconstruction' = [ordered]@{
            lifecycle = 'active'
            label = 'Scale Reconstruction'
            description = $null
        }
    }
    $scale['members'] = New-Object System.Collections.ArrayList
    $scale['relations'] = New-Object System.Collections.ArrayList
    $scale['comparison_sets'] = [ordered]@{}
    $ids = @()
    for ($index = 0; $index -lt 128; $index += 1) {
        $ids += 'scale-occurrence-{0:D3}' -f $index
        [void]$scale['members'].Add([ordered]@{
                id = 'scale-member-{0:D3}' -f $index
                interpretation_id = 'scale-reconstruction'
                target_type = 'occurrence'
                target_id = 'scale-occurrence-{0:D3}' -f $index
            })
        if ($index -gt 0) {
            [void]$scale['relations'].Add([ordered]@{
                    id = 'scale-relation-{0:D3}' -f $index
                    interpretation_id = 'scale-reconstruction'
                    source_member_id = 'scale-member-{0:D3}' -f ($index - 1)
                    relationship_type = 'precedes'
                    target_member_id = 'scale-member-{0:D3}' -f $index
                })
        }
    }
    Write-FixtureJson (Join-Path $FixtureRoot 'registry.json') $scale
    $provider = New-FixtureProvider 'scale' (New-FixtureTargetMap 'occurrence' $ids)
    $registry = Get-FixtureRegistry $Project $Packs @($provider) $FixtureRoot
    return [pscustomobject]@{
        members = @($registry.members).Count
        relations = @($registry.relations).Count
    }
}

$fixtureRoot = Join-Path $Root 'Framework\Data\Interpretations'
$base = Get-Content -LiteralPath (Join-Path $fixtureRoot 'base\registry.json') -Raw | ConvertFrom-Json
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
$project = Get-KnowledgeProjectConfig $Root
$packs = Get-KnowledgeSchemaPackRegistry $project
$providers = @(Get-FixtureProviders)
$temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('interpretation-conformance-' + [guid]::NewGuid())
[void](New-Item -ItemType Directory -Path $temporaryRoot)
try {
    Write-FixtureJson (Join-Path $temporaryRoot 'registry.json') $base
    $registry = Get-FixtureRegistry $project $packs $providers $temporaryRoot
    Assert-FixtureCounts $registry $expectations.counts
    Assert-FixtureServices $registry @($expectations.claim_keys)
    $invalidQueries = Assert-InvalidQueries $registry
    if ($invalidQueries -ne [int]$expectations.invalid_queries) {
        throw 'Structural interpretation invalid-query count changed.'
    }

    $invalidConfigurations = 0
    foreach ($case in @($expectations.invalid_cases)) {
        if ($case.post_load -ceq 'unknown-claim') {
            Assert-Rejected `
            { Assert-KnowledgeInterpretationClaimTargets $registry @() } `
                "Structural interpretation invalid case '$($case.id)' unexpectedly succeeded."
        }
        else {
            $candidate = ConvertTo-MutableFixtureValue $base
            foreach ($operation in @($case.operations)) {
                Invoke-FixtureMutation $candidate $operation
            }
            Write-FixtureJson (Join-Path $temporaryRoot 'registry.json') $candidate
            Assert-Rejected `
            { Get-FixtureRegistry $project $packs $providers $temporaryRoot } `
                "Structural interpretation invalid case '$($case.id)' unexpectedly succeeded."
        }
        $invalidConfigurations += 1
    }

    $disabledPacks = $packs.PSObject.Copy()
    $disabledPacks.enabled_capabilities = @(
        $packs.enabled_capabilities | Where-Object { $_ -cne 'structural-interpretation-modeling' }
    )
    Write-FixtureJson (Join-Path $temporaryRoot 'registry.json') $base
    Assert-Rejected `
    { Get-FixtureRegistry $project $disabledPacks $providers $temporaryRoot } `
        'Disabled structural interpretation capability unexpectedly loaded.'
    $invalidConfigurations += 1

    $duplicateProvider = New-FixtureProvider `
        'duplicate' `
    (New-FixtureTargetMap 'occurrence' @('other-occurrence'))
    Assert-Rejected `
    { Get-FixtureRegistry $project $packs @($providers + @($duplicateProvider)) $temporaryRoot } `
        'Duplicate structural interpretation target provider unexpectedly loaded.'
    $invalidConfigurations += 1

    $scale = Assert-Scale $project $packs $base $temporaryRoot
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    schema_version = [int]$registry.schema_version
    counts = [ordered]@{
        comparison_sets = [int]$expectations.counts.comparison_sets
        interpretations = [int]$expectations.counts.interpretations
        members = [int]$expectations.counts.members
        provenance_target_types = [int]$expectations.counts.provenance_target_types
        relation_types = [int]$expectations.counts.relation_types
        relations = [int]$expectations.counts.relations
    }
    invalid_configurations = $invalidConfigurations
    invalid_queries = $invalidQueries
    scale_members = [int]$scale.members
    scale_relations = [int]$scale.relations
}
if ($Json) {
    $summary | ConvertTo-Json -Compress -Depth 10
}
else {
    Write-Output 'Structural interpretation conformance passed.'
    $summary | ConvertTo-Json -Depth 10
}
