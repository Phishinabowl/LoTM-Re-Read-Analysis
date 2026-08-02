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

function New-TaxonomyFixtureProject {
    param([object]$Project, [string]$FixtureRoot)

    $fixture = $Project.PSObject.Copy()
    $fixture.root = $FixtureRoot
    $fixture.taxonomy_registry = Join-Path $FixtureRoot 'registry.json'
    $fixture.content_roots = @(
        [pscustomobject]@{
            id = 'articles'
            relative_path = 'content/articles'
            path = Join-Path $FixtureRoot 'content\articles'
            provenance_mode = 'fixed'
            provenance_label = 'article'
        }
        [pscustomobject]@{
            id = 'records'
            relative_path = 'content/records'
            path = Join-Path $FixtureRoot 'content\records'
            provenance_mode = 'fixed'
            provenance_label = 'record'
        }
    )
    return $fixture
}

function New-SourceFixtureProject {
    param([object]$Project, [string]$FixtureRoot)

    $fixture = $Project.PSObject.Copy()
    $fixture.root = $FixtureRoot
    $fixture.resources_registry = Join-Path $FixtureRoot 'resources.json'
    $fixture.sources_registry = Join-Path $FixtureRoot 'registry.json'
    $fixture.resource_roots = @(
        [pscustomobject]@{
            id = 'source-files'
            relative_path = 'source-files'
            path = Join-Path $FixtureRoot 'source-files'
            required = $true
        }
    )
    return $fixture
}

function Get-FixtureEntityRegistry {
    param(
        [object]$Project,
        [object]$Taxonomy,
        [object]$Sources,
        [object]$SchemaPacks,
        [string]$FixtureRoot
    )

    $fixture = $Project.PSObject.Copy()
    $fixture.entities_registry = Join-Path $FixtureRoot 'registry.json'
    return Get-KnowledgeEntityRegistry $fixture $Taxonomy $Sources $SchemaPacks
}

function Assert-EntityFixtureCounts {
    param([object]$Registry, [object]$Expected)

    $fields = @(
        'entities'
        'entity_relationship_types'
        'entity_relationships'
        'incarnations'
        'incarnation_bindings'
        'incarnation_relationship_types'
        'incarnation_relationships'
        'identity_phases'
        'identity_phase_bindings'
        'identity_phase_relationship_types'
        'identity_phase_relationships'
    )
    foreach ($field in $fields) {
        if ($Registry.$field.Count -ne [int]$Expected.$field) {
            throw "Entity fixture '$field' count changed."
        }
    }
    if ((Get-KnowledgeEntityReconciliationTargets $Registry).Count -ne [int]$Expected.reconciliation_target_types) {
        throw 'Entity reconciliation target-type count changed.'
    }
    if ((Get-KnowledgeEntityProvenanceSubjectTypes).Count -ne [int]$Expected.provenance_target_types) {
        throw 'Entity provenance target-type count changed.'
    }
}

function Assert-EntityFixtureServices {
    param([object]$Registry)

    if ((Resolve-KnowledgeEntityId $Registry 'FIRST-CONCEPT') -cne 'alpha-concept') {
        throw 'Entity alias resolution changed.'
    }
    if ((@(Resolve-KnowledgeEntityIds $Registry 'shared-subject') -join '|') -cne 'alpha-concept|beta-concept') {
        throw 'Ambiguous entity resolution changed.'
    }
    if ((@(Resolve-KnowledgeIncarnationIds $Registry 'shared-incarnation') -join '|') -cne 'alpha-primary|beta-primary') {
        throw 'Ambiguous incarnation resolution changed.'
    }
    if ((@(Resolve-KnowledgeIdentityPhaseIds $Registry 'shared-phase') -join '|') -cne 'alpha-primary-early|beta-concept-phase') {
        throw 'Ambiguous identity-phase resolution changed.'
    }
    if ($null -ne (Resolve-KnowledgeEntityId $Registry 'missing-entity')) {
        throw 'Unknown entity alias unexpectedly resolved.'
    }
    if ((@(Get-KnowledgeEntityIncarnations $Registry 'alpha-concept').id -join '|') -cne 'alpha-primary|alpha-adaptation') {
        throw 'Entity-to-incarnation query changed.'
    }
    if ((@(Get-KnowledgeEntityRelationships $Registry 'alpha-concept').id -join '|') -cne 'beta-succeeds-alpha|gamma-inspired-by-alpha') {
        throw 'Entity relationship query changed.'
    }
    if ((@(Get-KnowledgeIncarnationBindings $Registry 'alpha-primary').id -join '|') -cne 'alpha-primary-binding') {
        throw 'Incarnation binding query changed.'
    }
    if ((@(Get-KnowledgeIncarnationRelationships $Registry 'alpha-primary').id -join '|') -cne 'alpha-continuity-counterparts') {
        throw 'Incarnation relationship query changed.'
    }
    if ((@(Get-KnowledgeIdentityPhases $Registry 'entity-incarnation' 'alpha-primary').id -join '|') -cne 'alpha-primary-early|alpha-primary-late') {
        throw 'Incarnation identity-phase query changed.'
    }
    if ((@(Get-KnowledgeIdentityPhases $Registry 'entity' 'beta-concept').id -join '|') -cne 'beta-concept-phase') {
        throw 'Entity identity-phase query changed.'
    }
    if ((@(Get-KnowledgeIdentityPhaseBindings $Registry 'alpha-primary-early').id -join '|') -cne 'alpha-early-binding') {
        throw 'Identity-phase binding query changed.'
    }
    if ((@(Get-KnowledgeIdentityPhaseRelationships $Registry 'alpha-primary-early').id -join '|') -cne 'alpha-late-succeeds-early') {
        throw 'Identity-phase relationship query changed.'
    }
    $subject = Get-KnowledgeIdentitySubjectTarget $Registry 'entity' 'alpha-concept'
    if (-not [object]::ReferenceEquals($subject, $Registry.entities['alpha-concept'])) {
        throw 'Identity subject lookup changed.'
    }
    $phase = Get-KnowledgeIdentityTarget $Registry 'identity-phase' 'alpha-primary-early'
    if (-not [object]::ReferenceEquals($phase, $Registry.identity_phases['alpha-primary-early'])) {
        throw 'Identity target lookup changed.'
    }
    $provider = Get-KnowledgeEntityReconciliationProvider $Registry
    if ($provider.provider_id -cne 'entity' -or ($provider.targets.Keys -join '|') -cne 'entity|entity-incarnation|identity-phase') {
        throw 'Entity reconciliation provider changed.'
    }
    $relationship = Get-KnowledgeEntityProvenanceTarget $Registry 'entity-relationship' 'gamma-inspired-by-alpha'
    if (($relationship.basis_roles -join '|') -cne 'identity|appearance') {
        throw 'Entity provenance relationship lookup changed.'
    }
}

function Assert-InvalidEntityQueries {
    param([object]$Registry)

    $actions = @(
        { Resolve-KnowledgeEntityId $Registry 'shared-subject' }
        { Resolve-KnowledgeIncarnationId $Registry 'shared-incarnation' }
        { Resolve-KnowledgeIdentityPhaseId $Registry 'shared-phase' }
        { Get-KnowledgeEntityIncarnations $Registry 'unknown' }
        { Get-KnowledgeEntityRelationships $Registry 'unknown' }
        { Get-KnowledgeIncarnationBindings $Registry 'unknown' }
        { Get-KnowledgeIncarnationRelationships $Registry 'unknown' }
        { Get-KnowledgeIdentityPhases $Registry 'unknown' 'alpha-concept' }
        { Get-KnowledgeIdentityPhases $Registry 'entity' 'unknown' }
        { Get-KnowledgeIdentityPhaseBindings $Registry 'unknown' }
        { Get-KnowledgeIdentityPhaseRelationships $Registry 'unknown' }
        { Get-KnowledgeIdentitySubjectTarget $Registry 'unknown' 'alpha-concept' }
        { Get-KnowledgeIdentitySubjectTarget $Registry 'entity' 'unknown' }
        { Get-KnowledgeIdentityTarget $Registry 'unknown' 'alpha-concept' }
        { Get-KnowledgeEntityProvenanceTarget $Registry 'unknown' 'alpha-concept' }
    )
    for ($index = 0; $index -lt $actions.Count; $index += 1) {
        Assert-Rejected $actions[$index] "Invalid entity service query was accepted: $index"
    }
    return $actions.Count
}

function Add-ScaleEntities {
    param([object]$Document, [int]$Count)

    for ($index = 0; $index -lt $Count; $index += 1) {
        $entityId = 'scale-entity-{0:d3}' -f $index
        $Document.entities[$entityId] = [ordered]@{
            lifecycle = 'active'
            primary_category_id = 'subject-alpha'
            category_ids = @('subject-alpha')
            label = 'Scale Entity {0:d3}' -f $index
            aliases = @()
        }
    }
}

$project = Get-KnowledgeProjectConfig $Root
$schemaPacks = Get-KnowledgeSchemaPackRegistry $project
$canonicalTaxonomy = Get-KnowledgeTaxonomyConfig $project
$canonicalResources = Get-KnowledgeResourceConfig $project
$canonicalSources = Get-KnowledgeSourceRegistry $project $canonicalResources $schemaPacks
$canonical = Get-KnowledgeEntityRegistry $project $canonicalTaxonomy $canonicalSources $schemaPacks

$taxonomyRoot = Join-Path $Root 'Framework\Data\Taxonomy\base'
$taxonomy = Get-KnowledgeTaxonomyConfig (New-TaxonomyFixtureProject $project $taxonomyRoot)
$sourceRoot = Join-Path $Root 'Framework\Data\Sources\base'
$sourceProject = New-SourceFixtureProject $project $sourceRoot
$resources = Get-KnowledgeResourceConfig $sourceProject
$sources = Get-KnowledgeSourceRegistry $sourceProject $resources $schemaPacks

$fixtureRoot = Join-Path $Root 'Framework\Data\Entities'
$baseRoot = Join-Path $fixtureRoot 'base'
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
if ([int]$expectations.schema_version -ne 1) {
    throw 'Unsupported entity conformance expectation schema.'
}
$baseDocument = ConvertTo-MutableFixtureValue (
    Get-Content -LiteralPath (Join-Path $baseRoot 'registry.json') -Raw | ConvertFrom-Json
)

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('knowledge-entity-' + [guid]::NewGuid().ToString('N'))
try {
    [void](New-Item -ItemType Directory -Path $tempRoot)
    $validRoot = Join-Path $tempRoot 'valid'
    Copy-Item -LiteralPath $baseRoot -Destination $validRoot -Recurse
    $fixtureRegistry = Get-FixtureEntityRegistry $project $taxonomy $sources $schemaPacks $validRoot
    Assert-EntityFixtureCounts $fixtureRegistry $expectations.valid_counts
    Assert-EntityFixtureServices $fixtureRegistry
    $invalidQueryCount = Assert-InvalidEntityQueries $fixtureRegistry
    if ($invalidQueryCount -ne [int]$expectations.invalid_query_cases) {
        throw 'Entity invalid-query expectation count changed.'
    }

    foreach ($case in $expectations.invalid_cases) {
        $caseRoot = Join-Path $tempRoot ([string]$case.id)
        Copy-Item -LiteralPath $baseRoot -Destination $caseRoot -Recurse
        $document = ConvertTo-MutableFixtureValue $baseDocument
        foreach ($operation in $case.operations) {
            Invoke-FixtureMutation $document $operation
        }
        Write-FixtureJson (Join-Path $caseRoot 'registry.json') $document
        Assert-Rejected {
            Get-FixtureEntityRegistry $project $taxonomy $sources $schemaPacks $caseRoot
        } "Malformed entity configuration was accepted: $($case.id)"
    }

    $scaleRoot = Join-Path $tempRoot 'scale'
    Copy-Item -LiteralPath $baseRoot -Destination $scaleRoot -Recurse
    $scaleDocument = ConvertTo-MutableFixtureValue $baseDocument
    $scaleCount = [int]$expectations.scale_additional_entities
    Add-ScaleEntities $scaleDocument $scaleCount
    Write-FixtureJson (Join-Path $scaleRoot 'registry.json') $scaleDocument
    $scaleRegistry = Get-FixtureEntityRegistry $project $taxonomy $sources $schemaPacks $scaleRoot
    if ($scaleRegistry.entities.Count -ne $fixtureRegistry.entities.Count + $scaleCount) {
        throw 'Entity scale composition count changed.'
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    schema_version = 1
    canonical_entities = $canonical.entities.Count
    canonical_incarnations = $canonical.incarnations.Count
    canonical_identity_phases = $canonical.identity_phases.Count
    fixture_entities = $fixtureRegistry.entities.Count
    fixture_incarnations = $fixtureRegistry.incarnations.Count
    fixture_identity_phases = $fixtureRegistry.identity_phases.Count
    fixture_provenance_target_types = (Get-KnowledgeEntityProvenanceSubjectTypes).Count
    invalid_configuration_cases = @($expectations.invalid_cases).Count
    invalid_query_cases = $invalidQueryCount
    scale_additional_entities = $scaleCount
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Host (
        'Entity conformance passed: {0} fixture entities, {1} incarnations, ' +
        '{2} malformed configurations, and {3} additional scale entities.' -f
        $summary.fixture_entities,
        $summary.fixture_incarnations,
        $summary.invalid_configuration_cases,
        $summary.scale_additional_entities
    )
}
