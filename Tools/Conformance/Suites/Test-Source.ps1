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
    $fixtureProject.resources_registry = Join-Path $FixtureRoot 'resources.json'
    $fixtureProject.sources_registry = Join-Path $FixtureRoot 'registry.json'
    $fixtureProject.resource_roots = @(
        [pscustomobject]@{
            id = 'source-files'
            relative_path = 'source-files'
            path = Join-Path $FixtureRoot 'source-files'
            required = $true
        }
    )
    return $fixtureProject
}

function Get-FixtureSourceRegistry {
    param(
        [object]$Project,
        [object]$SchemaPacks,
        [string]$FixtureRoot
    )

    $fixtureProject = New-FixtureProject $Project $FixtureRoot
    $resources = Get-KnowledgeResourceConfig $fixtureProject
    return Get-KnowledgeSourceRegistry $fixtureProject $resources $SchemaPacks
}

function Assert-SourceFixtureCounts {
    param(
        [object]$Registry,
        [object]$Expected
    )

    $fields = @(
        'media_modalities'
        'mediums'
        'work_groups'
        'continuities'
        'authority_profiles'
        'works'
        'segments'
        'content_groups'
        'numbering_schemes'
        'ordering_schemes'
        'work_relationships'
        'adaptation_mappings'
        'territories'
        'applicability_scopes'
        'work_production_contexts'
        'manifestations'
        'release_components'
        'release_packages'
        'release_runs'
        'release_events'
        'catalog_placements'
        'platform_offerings'
        'sources'
        'external_identifiers'
    )
    foreach ($field in $fields) {
        if ($Registry.$field.Count -ne [int]$Expected.$field) {
            throw "Source fixture '$field' count changed."
        }
    }
    $coverageCount = @($Registry.sources.Values | ForEach-Object coverage).Count
    $observationCount = @($Registry.sources.Values | ForEach-Object observations).Count
    if ($coverageCount -ne [int]$Expected.coverage_entries) {
        throw 'Source fixture coverage count changed.'
    }
    if ($observationCount -ne [int]$Expected.observations) {
        throw 'Source fixture observation count changed.'
    }
    if ((Get-KnowledgeSourceReconciliationTargets $Registry).Count -ne [int]$Expected.reconciliation_target_types) {
        throw 'Source reconciliation target-type count changed.'
    }
    if ((Get-KnowledgeSourceProvenanceSubjectTypes).Count -ne [int]$Expected.provenance_target_types) {
        throw 'Source provenance target-type count changed.'
    }
}

function Assert-SourceFixtureServices {
    param([object]$Registry)

    if ((Resolve-KnowledgeWorkId $Registry 'ORIGINAL-WORK') -cne 'primary-work') {
        throw 'Source work-alias resolution changed.'
    }
    if ((Resolve-KnowledgeSourceId $Registry 'SCREEN-SOURCE') -cne 'adaptation-source') {
        throw 'Evidence source-alias resolution changed.'
    }
    if ($null -ne (Resolve-KnowledgeWorkId $Registry 'missing-work')) {
        throw 'Unknown work alias unexpectedly resolved.'
    }
    $workTarget = Get-KnowledgeSourceReconciliationTarget $Registry 'work' 'primary-work'
    if (-not [object]::ReferenceEquals($workTarget, $Registry.works['primary-work'])) {
        throw 'Source reconciliation lookup changed.'
    }
    $rangeTarget = Get-KnowledgeSourceProvenanceTarget $Registry 'coverage-position-range' 'primary-chapters-one-two'
    if ([string]$rangeTarget.id -cne 'primary-chapters-one-two') {
        throw 'Nested source provenance lookup changed.'
    }
    $highest = @(Get-KnowledgeHighestPrecedenceScopes $Registry @('adaptation-work-scope', 'chapter-one-region-scope'))
    if (($highest.id -join '|') -cne 'chapter-one-region-scope') {
        throw 'Applicability precedence selection changed.'
    }

    $adaptation = Get-KnowledgeApplicabilityDecision $Registry 'segment' 'adaptation-episode-one'
    if (($adaptation.winning_scope_ids -join '|') -cne 'adaptation-work-scope' -or $adaptation.matches[0].target_match -cne 'contained') {
        throw 'Contained work-scope applicability changed.'
    }
    $chapter = Get-KnowledgeApplicabilityDecision `
        $Registry 'segment' 'primary-chapter-one' 'sample-region' '2025-02-01T00:00:00Z'
    if (($chapter.winning_scope_ids -join '|') -cne 'chapter-one-region-scope' -or $chapter.matches[0].target_match -cne 'exact') {
        throw 'Territorial segment applicability changed.'
    }
    $before = Get-KnowledgeApplicabilityDecision `
        $Registry 'segment' 'primary-chapter-one' 'sample-region' '2024-12-31T00:00:00Z'
    if ($before.winning_scope_ids.Count -ne 0) {
        throw 'Applicability accepted a scope before its effective window.'
    }

    $primary = Get-KnowledgeSourceAuthorityDecision `
        $Registry 'comparison-profile' 'dialogue' 'primary-source' 'canonical-text'
    if ($primary.rank -ne 1 -or $primary.winning_rule_id -cne 'primary-dialogue-rule' -or $primary.inherited) {
        throw 'Exact source authority rule selection changed.'
    }
    $adaptationAuthority = Get-KnowledgeSourceAuthorityDecision `
        $Registry 'comparison-profile' 'dialogue' 'adaptation-source' 'animation-visual'
    if (
        $adaptationAuthority.rank -ne 2 -or
        $adaptationAuthority.winning_rule_id -cne 'adaptation-content-rule' -or
        -not $adaptationAuthority.claim_namespace_inherited
    ) {
        throw 'Claim-namespace authority inheritance changed.'
    }
    $modeAuthority = Get-KnowledgeSourceAuthorityDecision `
        $Registry 'comparison-profile' 'canonical-content' 'primary-source' 'canonical-text'
    if ($modeAuthority.winning_rule_id -cne 'primary-text-mode-rule' -or -not $modeAuthority.evidence_mode_inherited) {
        throw 'Evidence-mode authority inheritance changed.'
    }
    $fallback = Get-KnowledgeSourceAuthorityDecision `
        $Registry 'comparison-profile' 'publication-metadata' 'primary-source'
    if ($fallback.rank -ne 1 -or -not $fallback.priority_fallback) {
        throw 'Source-priority authority fallback changed.'
    }
    $candidates = @(
        [pscustomobject]@{ candidate_id = 'primary-claim'
            source_id = 'primary-source'
            evidence_mode = 'canonical-text'
        }
        [pscustomobject]@{ candidate_id = 'adaptation-claim'
            source_id = 'adaptation-source'
            evidence_mode = 'animation-visual'
        }
    )
    $comparison = Compare-KnowledgeSourceAuthority $Registry 'comparison-profile' 'dialogue' $candidates
    if ($comparison.outcome -cne 'winner' -or ($comparison.winning_candidate_ids -join '|') -cne 'primary-claim') {
        throw 'Multi-source authority comparison changed.'
    }

    $novelStart = [ordered]@{ work = 'primary-work'
        volume = 1
        chapter = 1
    }
    $novelEnd = [ordered]@{ work = 'primary-work'
        volume = 1
        chapter = 2
    }
    Assert-SourceEvidencePosition `
        $novelStart `
        $Registry.mediums['novel'] `
        $Registry.sources['primary-source'].work_ids `
        $Registry.works `
        $Registry.segments `
        $Registry.ordering_schemes `
        'fixture novel position'
    if ((Compare-SourcePositions $novelStart $novelEnd $Registry.mediums['novel']) -ne -1) {
        throw 'Novel position ordering changed.'
    }
    $animeStart = [ordered]@{
        work = 'adaptation-work'
        segment = 'adaptation-episode-one'
        ordering_scheme = 'adaptation-release-order'
        episode = 1
    }
    $animeEnd = [ordered]@{
        work = 'adaptation-work'
        segment = 'adaptation-episode-two'
        ordering_scheme = 'adaptation-release-order'
        episode = 2
    }
    Assert-SourceEvidencePosition `
        $animeStart `
        $Registry.mediums['anime'] `
        $Registry.sources['adaptation-source'].work_ids `
        $Registry.works `
        $Registry.segments `
        $Registry.ordering_schemes `
        'fixture anime position'
    if ((Compare-SourcePositions $animeStart $animeEnd $Registry.mediums['anime'] $Registry.ordering_schemes) -ne -1) {
        throw 'Ordering-backed position comparison changed.'
    }
}

function Assert-InvalidSourceQueries {
    param([object]$Registry)

    $actions = @(
        { Get-KnowledgeSourceReconciliationTarget $Registry 'unknown' 'primary-work' }
        { Get-KnowledgeSourceReconciliationTarget $Registry 'work' 'unknown' }
        { Get-KnowledgeSourceProvenanceTarget $Registry 'unknown' 'primary-work' }
        { Get-KnowledgeSourceProvenanceTarget $Registry 'work' 'unknown' }
        { Get-KnowledgeHighestPrecedenceScopes $Registry @() }
        { Get-KnowledgeHighestPrecedenceScopes $Registry @('unknown') }
        { Get-KnowledgeApplicabilityDecision $Registry 'unknown' 'primary-work' }
        { Get-KnowledgeApplicabilityDecision $Registry 'work' 'unknown' }
        { Get-KnowledgeApplicabilityDecision $Registry 'work' 'primary-work' 'unknown' }
        { Get-KnowledgeSourceAuthorityDecision $Registry 'unknown' 'dialogue' 'primary-source' }
        { Get-KnowledgeSourceAuthorityDecision $Registry 'comparison-profile' 'dialogue' 'unknown' }
        { Get-KnowledgeSourceAuthorityDecision $Registry 'comparison-profile' 'unknown' 'primary-source' }
        { Get-KnowledgeSourceAuthorityDecision $Registry 'comparison-profile' 'dialogue' 'primary-source' 'animation-visual' }
        { Compare-KnowledgeSourceAuthority $Registry 'comparison-profile' 'dialogue' @() }
        {
            Compare-KnowledgeSourceAuthority $Registry 'comparison-profile' 'dialogue' @(
                [pscustomobject]@{ candidate_id = 'duplicate'
                    source_id = 'primary-source'
                    evidence_mode = $null
                }
                [pscustomobject]@{ candidate_id = 'duplicate'
                    source_id = 'adaptation-source'
                    evidence_mode = $null
                }
            )
        }
    )
    for ($index = 0; $index -lt $actions.Count; $index += 1) {
        Assert-Rejected $actions[$index] "Invalid source service query was accepted: $index"
    }
    return $actions.Count
}

function Add-ScaleSources {
    param(
        [object]$Document,
        [int]$Count
    )

    for ($index = 0; $index -lt $Count; $index += 1) {
        $sourceId = 'scale-source-{0:d3}' -f $index
        $Document.sources[$sourceId] = [ordered]@{
            lifecycle = 'active'
            label = 'Scale Source {0:d3}' -f $index
            work_ids = @('primary-work')
            manifestation_id = 'primary-edition'
            release_component_ids = @()
            medium_id = 'novel'
            locator_medium_ids = @('novel')
            container_format_ids = @('epub')
            role = 'primary-edition'
            comparison_group = 'scale-group'
            priority = $index + 1
            aliases = @()
            evidence_modes = @('canonical-text')
            observations = @()
            coverage = @()
            resource_bindings = @()
        }
    }
}

$project = Get-KnowledgeProjectConfig $Root
$schemaPacks = Get-KnowledgeSchemaPackRegistry $project
$canonicalResources = Get-KnowledgeResourceConfig $project
$canonical = Get-KnowledgeSourceRegistry $project $canonicalResources $schemaPacks
$fixtureRoot = Join-Path $Root 'Framework\Data\Sources'
$baseRoot = Join-Path $fixtureRoot 'base'
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
if ([int]$expectations.schema_version -ne 1) {
    throw 'Unsupported source conformance expectation schema.'
}
$baseDocument = ConvertTo-MutableFixtureValue (
    Get-Content -LiteralPath (Join-Path $baseRoot 'registry.json') -Raw | ConvertFrom-Json
)

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('knowledge-source-' + [guid]::NewGuid().ToString('N'))
try {
    [void](New-Item -ItemType Directory -Path $tempRoot)
    $validRoot = Join-Path $tempRoot 'valid'
    Copy-Item -LiteralPath $baseRoot -Destination $validRoot -Recurse
    $fixtureRegistry = Get-FixtureSourceRegistry $project $schemaPacks $validRoot
    Assert-SourceFixtureCounts $fixtureRegistry $expectations.valid_counts
    Assert-SourceFixtureServices $fixtureRegistry
    $invalidQueryCount = Assert-InvalidSourceQueries $fixtureRegistry
    if ($invalidQueryCount -ne [int]$expectations.invalid_query_cases) {
        throw 'Source invalid-query expectation count changed.'
    }

    foreach ($case in $expectations.invalid_cases) {
        $caseRoot = Join-Path $tempRoot ([string]$case.id)
        Copy-Item -LiteralPath $baseRoot -Destination $caseRoot -Recurse
        $document = ConvertTo-MutableFixtureValue $baseDocument
        foreach ($operation in $case.operations) {
            Invoke-FixtureMutation $document $operation $caseRoot
        }
        Write-FixtureJson (Join-Path $caseRoot 'registry.json') $document
        Assert-Rejected {
            Get-FixtureSourceRegistry $project $schemaPacks $caseRoot
        } "Malformed source configuration was accepted: $($case.id)"
    }

    $scaleRoot = Join-Path $tempRoot 'scale'
    Copy-Item -LiteralPath $baseRoot -Destination $scaleRoot -Recurse
    $scaleDocument = ConvertTo-MutableFixtureValue $baseDocument
    $scaleCount = [int]$expectations.scale_additional_sources
    Add-ScaleSources $scaleDocument $scaleCount
    Write-FixtureJson (Join-Path $scaleRoot 'registry.json') $scaleDocument
    $scaleRegistry = Get-FixtureSourceRegistry $project $schemaPacks $scaleRoot
    if ($scaleRegistry.sources.Count -ne $fixtureRegistry.sources.Count + $scaleCount) {
        throw 'Source scale composition count changed.'
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    schema_version = 1
    canonical_works = $canonical.works.Count
    canonical_sources = $canonical.sources.Count
    fixture_works = $fixtureRegistry.works.Count
    fixture_sources = $fixtureRegistry.sources.Count
    fixture_provenance_target_types = (Get-KnowledgeSourceProvenanceSubjectTypes).Count
    invalid_configuration_cases = @($expectations.invalid_cases).Count
    invalid_query_cases = $invalidQueryCount
    scale_additional_sources = $scaleCount
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Host (
        'Source conformance passed: {0} canonical works, {1} canonical sources, ' +
        '{2} malformed configurations, and {3} additional scale sources.' -f
        $summary.canonical_works,
        $summary.canonical_sources,
        $summary.invalid_configuration_cases,
        $summary.scale_additional_sources
    )
}
