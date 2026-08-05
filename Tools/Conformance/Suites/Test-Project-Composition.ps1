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

$sourceCountFields = @(
    'media_modalities'
    'cultural_forms'
    'release_forms'
    'container_formats'
    'mediums'
    'work_groups'
    'continuities'
    'authority_profiles'
    'work_relationship_types'
    'works'
    'segments'
    'content_groups'
    'ordering_schemes'
    'numbering_schemes'
    'work_relationships'
    'adaptation_mappings'
    'territories'
    'applicability_scopes'
    'manifestations'
    'release_components'
    'release_packages'
    'release_runs'
    'release_events'
    'catalog_placements'
    'platform_offerings'
    'sources'
)
$chronologyCountFields = @(
    'coordinate_systems'
    'eras'
    'narrative_contexts'
    'positions'
    'spans'
    'relations'
    'mappings'
)
$entityCountFields = @(
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
$occurrenceCountFields = @(
    'branches'
    'templates'
    'recurrence_patterns'
    'recurrences'
    'recurrence_cardinalities'
    'iterations'
    'phases'
    'schedules'
    'occurrences'
    'occurrence_participations'
    'tracks'
    'track_entries'
    'transitions'
    'causal_relations'
    'outcomes'
    'rules'
    'state_transitions'
    'carryovers'
)

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

function ConvertTo-CompositionComparableValue {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value -or $Value -is [string] -or $Value.GetType().IsPrimitive) {
        return $Value
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $mapping = [ordered]@{}
        foreach ($key in $Value.Keys) {
            $mapping[[string]$key] = ConvertTo-CompositionComparableValue $Value[$key]
        }
        return $mapping
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $mapping = [ordered]@{}
        foreach ($property in $Value.PSObject.Properties) {
            $mapping[$property.Name] = ConvertTo-CompositionComparableValue $property.Value
        }
        return $mapping
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        return , @($Value | ForEach-Object { ConvertTo-CompositionComparableValue $_ })
    }
    return $Value
}

function Get-ProjectComposition {
    param([string]$ProjectRoot)

    $project = Get-KnowledgeProjectConfig $ProjectRoot
    $lookup = Get-KnowledgeLookupKeyConfig $project
    $packs = Get-KnowledgeSchemaPackRegistry $project
    $taxonomy = Get-KnowledgeTaxonomyConfig $project
    $resources = Get-KnowledgeResourceConfig $project
    $sources = Get-KnowledgeSourceRegistry $project $resources $packs
    $chronology = Get-KnowledgeChronologyRegistry `
        $project `
        $packs `
    @($sources.works.Keys) `
    @($sources.continuities.Keys)
    $entities = Get-KnowledgeEntityRegistry $project $taxonomy $sources $packs
    $occurrences = Get-KnowledgeOccurrenceRegistry $project $packs $chronology
    $providers = @(
        (Get-KnowledgeTaxonomyReconciliationProvider $taxonomy)
        (Get-KnowledgeResourceReconciliationProvider $resources)
        (Get-KnowledgeSourceReconciliationProvider $sources)
        (Get-KnowledgeEntityReconciliationProvider $entities)
    )
    $reconciliation = Get-KnowledgeReconciliationRegistry $project $providers $packs
    $provenance = Get-KnowledgeProvenanceRegistry `
        $project `
        $sources `
        $entities `
        $reconciliation `
        $packs `
        $occurrences
    return [pscustomobject]@{
        project = $project
        lookup = $lookup
        packs = $packs
        taxonomy = $taxonomy
        resources = $resources
        sources = $sources
        chronology = $chronology
        entities = $entities
        occurrences = $occurrences
        providers = @($providers)
        reconciliation = $reconciliation
        provenance = $provenance
    }
}

function Get-RegistryCounts {
    param([object]$Registry, [string[]]$Fields)

    $counts = [ordered]@{}
    foreach ($field in $Fields) {
        $value = $Registry.$field
        $counts[$field] = if ($value -is [System.Collections.IDictionary]) {
            $value.Count
        }
        else {
            @($value).Count
        }
    }
    return $counts
}

function Get-ProjectCompositionSummary {
    param([object]$Composition)

    $project = $Composition.project
    $packs = $Composition.packs
    $versions = [ordered]@{}
    foreach ($packId in @($packs.selection_order)) {
        $versions[$packId] = [int]$packs.packs[$packId].pack_version
    }
    $controlledValueCount = 0
    foreach ($values in $packs.controlled_values.Values) {
        $controlledValueCount += @($values).Count
    }
    $disabledCapabilities = @(
        $packs.declared_capabilities |
            Where-Object { $packs.enabled_capabilities -cnotcontains $_ } |
            Sort-Object
    )
    $aliasCount = 0
    foreach ($aliases in $Composition.reconciliation.aliases.Values) {
        $aliasCount += $aliases.Count
    }
    $sourceProvenanceTypes = @(Get-KnowledgeSourceProvenanceSubjectTypes)
    $entityProvenanceTypes = @(Get-KnowledgeEntityProvenanceSubjectTypes)
    $reconciliationProvenanceTypes = @(Get-KnowledgeReconciliationProvenanceSubjectTypes)
    $occurrenceProvenanceTypes = @((Get-KnowledgeOccurrenceProvenanceTargets $Composition.occurrences).Keys)
    $allProvenanceTypes = @(
        $sourceProvenanceTypes +
        $entityProvenanceTypes +
        $reconciliationProvenanceTypes +
        $occurrenceProvenanceTypes +
        @('claim-supersession') |
            Sort-Object -Unique
    )
    $reconciliationTargetTypeCount = 0
    foreach ($provider in @($Composition.providers)) {
        $reconciliationTargetTypeCount += $provider.targets.Count
    }
    return [ordered]@{
        project = [ordered]@{
            project_id = $project.project_id
            framework = $project.framework
            domain = $project.domain
            content_root_ids = @($project.content_roots.id)
            resource_root_ids = @($project.resource_roots.id)
        }
        schemas = [ordered]@{
            project = [int]$project.schema_version
            lookup = [int]$Composition.lookup.schema_version
            packs = [int]$packs.schema_version
            taxonomy = [int]$Composition.taxonomy.schema_version
            resources = [int]$Composition.resources.schema_version
            sources = [int]$Composition.sources.schema_version
            chronology = [int]$Composition.chronology.schema_version
            entities = [int]$Composition.entities.schema_version
            occurrences = [int]$Composition.occurrences.schema_version
            reconciliation = [int]$Composition.reconciliation.schema_version
            provenance = [int]$Composition.provenance.schema_version
        }
        packs = [ordered]@{
            selection_order = @($packs.selection_order)
            versions = $versions
            declared_capabilities = @($packs.declared_capabilities).Count
            available_capabilities = @($packs.available_capabilities).Count
            enabled_capabilities = @($packs.enabled_capabilities).Count
            disabled_capability_ids = @($disabledCapabilities)
            controlled_value_namespaces = $packs.controlled_values.Count
            controlled_values = $controlledValueCount
            semantic_declarations = [ordered]@{
                transition_profiles = $packs.transition_profiles.Count
                outcome_incompatibilities = $packs.outcome_incompatibilities.Count
                effect_target_compatibilities = $packs.effect_target_compatibilities.Count
                rule_effect_compatibilities = $packs.rule_effect_compatibilities.Count
                effect_policies = $packs.effect_policies.Count
                effect_incompatibilities = $packs.effect_incompatibilities.Count
                state_change_profiles = $packs.state_change_profiles.Count
            }
        }
        counts = [ordered]@{
            taxonomy = [ordered]@{
                categories = $Composition.taxonomy.categories.Count
                content_types = $Composition.taxonomy.content_types.Count
            }
            resources = [ordered]@{
                kinds = $Composition.resources.kinds.Count
                types = $Composition.resources.types.Count
            }
            sources = Get-RegistryCounts $Composition.sources $sourceCountFields
            chronology = Get-RegistryCounts $Composition.chronology $chronologyCountFields
            entities = Get-RegistryCounts $Composition.entities $entityCountFields
            occurrences = Get-RegistryCounts $Composition.occurrences $occurrenceCountFields
            reconciliation = [ordered]@{
                target_types = $Composition.reconciliation.targets.Count
                records = @($Composition.reconciliation.records).Count
                aliases = $aliasCount
            }
            provenance = [ordered]@{
                assertions = @($Composition.provenance.assertions).Count
                claim_supersessions = @($Composition.provenance.claim_supersessions).Count
            }
        }
        providers = [ordered]@{
            reconciliation_target_types = $reconciliationTargetTypeCount
            source_provenance_types = $sourceProvenanceTypes.Count
            entity_provenance_types = $entityProvenanceTypes.Count
            reconciliation_provenance_types = $reconciliationProvenanceTypes.Count
            occurrence_provenance_types = $occurrenceProvenanceTypes.Count
            total_provenance_subject_types = $allProvenanceTypes.Count
        }
    }
}

function Assert-ProjectCompositionWiring {
    param([object]$Composition)

    $project = $Composition.project
    $pathPairs = @(
        [pscustomobject]@{actual = $Composition.lookup.path
            expected = $project.lookup_keys_registry
        }
        [pscustomobject]@{actual = $Composition.packs.path
            expected = $project.schema_packs_registry
        }
        [pscustomobject]@{actual = $Composition.taxonomy.path
            expected = $project.taxonomy_registry
        }
        [pscustomobject]@{actual = $Composition.resources.path
            expected = $project.resources_registry
        }
        [pscustomobject]@{actual = $Composition.sources.path
            expected = $project.sources_registry
        }
        [pscustomobject]@{actual = $Composition.chronology.path
            expected = $project.chronology_registry
        }
        [pscustomobject]@{actual = $Composition.entities.path
            expected = $project.entities_registry
        }
        [pscustomobject]@{actual = $Composition.occurrences.path
            expected = $project.occurrences_registry
        }
        [pscustomobject]@{actual = $Composition.reconciliation.path
            expected = $project.reconciliation_registry
        }
        [pscustomobject]@{actual = $Composition.provenance.path
            expected = $project.provenance_registry
        }
    )
    foreach ($pair in $pathPairs) {
        $actual = [System.IO.Path]::GetFullPath([string]$pair.actual)
        $expected = [System.IO.Path]::GetFullPath([string]$pair.expected)
        if ($actual -cne $expected) {
            throw 'A composed registry did not retain its manifest-owned path.'
        }
    }
    if (-not [object]::ReferenceEquals($Composition.occurrences.chronology, $Composition.chronology)) {
        throw 'Occurrence composition did not retain the loaded chronology instance.'
    }
    if (-not [object]::ReferenceEquals($Composition.provenance.sources, $Composition.sources)) {
        throw 'Provenance composition did not retain the loaded source instance.'
    }
    if (-not [object]::ReferenceEquals($Composition.provenance.entities, $Composition.entities)) {
        throw 'Provenance composition did not retain the loaded entity instance.'
    }
    if (-not [object]::ReferenceEquals($Composition.provenance.reconciliations, $Composition.reconciliation)) {
        throw 'Provenance composition did not retain the loaded reconciliation instance.'
    }
    if (-not [object]::ReferenceEquals($Composition.provenance.occurrences, $Composition.occurrences)) {
        throw 'Provenance composition did not retain the loaded occurrence instance.'
    }
}

function Assert-ProjectProviderClosure {
    param([object]$Composition)

    $reconciliationTypes = @(
        $Composition.providers |
            ForEach-Object { @($_.targets.Keys) } |
            Sort-Object -Unique
    )
    $allowedReconciliation = @(Get-SchemaPackAllowedValues $Composition.packs 'reconciliation.target-type')
    if (($reconciliationTypes -join '|') -cne (@($allowedReconciliation | Sort-Object) -join '|') -or
        ($reconciliationTypes -join '|') -cne (@($Composition.reconciliation.targets.Keys | Sort-Object) -join '|')) {
        throw 'Reconciliation provider closure changed.'
    }
    $provenanceTypes = @(
        (Get-KnowledgeSourceProvenanceSubjectTypes) +
        (Get-KnowledgeEntityProvenanceSubjectTypes) +
        (Get-KnowledgeReconciliationProvenanceSubjectTypes) +
        @((Get-KnowledgeOccurrenceProvenanceTargets $Composition.occurrences).Keys) +
        @('claim-supersession') |
            Sort-Object -Unique
    )
    $allowedProvenance = @(Get-SchemaPackAllowedValues $Composition.packs 'provenance.subject-type')
    if (($provenanceTypes -join '|') -cne (@($allowedProvenance | Sort-Object) -join '|')) {
        throw 'Provenance provider closure changed.'
    }
}

function Copy-PacksWithoutCapability {
    param([object]$Packs, [string]$Capability)

    $copy = $Packs.PSObject.Copy()
    $copy.enabled_capabilities = @($Packs.enabled_capabilities | Where-Object { $_ -cne $Capability })
    return $copy
}

function Copy-PacksWithProvenanceTypes {
    param([object]$Packs, [string[]]$Values)

    $copy = $Packs.PSObject.Copy()
    $controlledValues = [ordered]@{}
    foreach ($key in $Packs.controlled_values.Keys) {
        $controlledValues[$key] = @($Packs.controlled_values[$key])
    }
    $controlledValues['provenance.subject-type'] = @($Values)
    $copy.controlled_values = $controlledValues
    return $copy
}

function Assert-InvalidProjectCompositions {
    param([object]$Composition)

    $project = $Composition.project
    $providers = @($Composition.providers)
    $packs = $Composition.packs
    $provenanceTypes = @(Get-SchemaPackAllowedValues $packs 'provenance.subject-type')
    $missingProviderPacks = Copy-PacksWithProvenanceTypes `
        $packs `
    @($provenanceTypes + @('unprovided-subject'))
    $unregisteredProviderPacks = Copy-PacksWithProvenanceTypes `
        $packs `
    @($provenanceTypes | Where-Object { $_ -cne 'entity' })
    $entityPacks = Copy-PacksWithoutCapability $packs 'entity-incarnations'
    $occurrencePacks = Copy-PacksWithoutCapability $packs 'occurrence-recurrence-modeling'
    $participationPacks = Copy-PacksWithoutCapability $packs 'occurrence-participation-identity'
    $reconciliationPacks = Copy-PacksWithoutCapability $packs 'stable-identity-reconciliation'
    $actions = @(
        { Get-KnowledgeReconciliationRegistry $project @($providers[0..2]) $packs }
        { Get-KnowledgeReconciliationRegistry $project @($providers + @($providers[0])) $packs }
        {
            Get-KnowledgeProvenanceRegistry `
                $project `
                $Composition.sources `
                $Composition.entities `
                $Composition.reconciliation `
                $missingProviderPacks `
                $Composition.occurrences
        }
        {
            Get-KnowledgeProvenanceRegistry `
                $project `
                $Composition.sources `
                $Composition.entities `
                $Composition.reconciliation `
                $unregisteredProviderPacks `
                $Composition.occurrences
        }
        {
            Get-KnowledgeEntityRegistry `
                $project `
                $Composition.taxonomy `
                $Composition.sources `
                $entityPacks
        }
        {
            Get-KnowledgeOccurrenceRegistry `
                $project `
                $occurrencePacks `
                $Composition.chronology
        }
        {
            Get-KnowledgeOccurrenceRegistry `
                $project `
                $participationPacks `
                $Composition.chronology
        }
        { Get-KnowledgeReconciliationRegistry $project $providers $reconciliationPacks }
    )
    for ($index = 0; $index -lt $actions.Count; $index += 1) {
        Assert-Rejected $actions[$index] "Invalid project composition was accepted: $index"
    }
    return $actions.Count
}

$baselinePath = Join-Path $Root 'Project_Config\composition-baseline.json'
$baseline = Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
if ([int]$baseline.schema_version -ne 1) {
    throw 'Unsupported project-composition baseline schema.'
}
$expectedSummary = ConvertTo-CompositionComparableValue ([ordered]@{
        project = $baseline.project
        schemas = $baseline.schemas
        packs = $baseline.packs
        counts = $baseline.counts
        providers = $baseline.providers
    })
$expectedJson = ConvertTo-SourceCanonicalJson $expectedSummary
$passCount = [int]$baseline.composition_passes
$summaryJson = @()
for ($index = 0; $index -lt $passCount; $index += 1) {
    $composition = Get-ProjectComposition $Root
    Assert-ProjectCompositionWiring $composition
    Assert-ProjectProviderClosure $composition
    $actualSummary = Get-ProjectCompositionSummary $composition
    $actualJson = ConvertTo-SourceCanonicalJson $actualSummary
    if ($actualJson -cne $expectedJson) {
        throw 'Canonical project composition differs from its reviewed baseline.'
    }
    $summaryJson += $actualJson
}
if (@($summaryJson | Sort-Object -Unique).Count -ne 1) {
    throw 'Repeated project composition produced process-state drift.'
}

$invalidCount = Assert-InvalidProjectCompositions $composition
if ($invalidCount -ne [int]$baseline.invalid_composition_cases) {
    throw 'Project-composition invalid-case count changed.'
}

$output = [ordered]@{
    schema_version = 1
    project_id = $composition.project.project_id
    composition_passes = $passCount
    selected_packs = $composition.packs.packs.Count
    enabled_capabilities = @($composition.packs.enabled_capabilities).Count
    disabled_capabilities = @($baseline.packs.disabled_capability_ids).Count
    reconciliation_target_types = $composition.reconciliation.targets.Count
    provenance_subject_types = [int]$baseline.providers.total_provenance_subject_types
    invalid_composition_cases = $invalidCount
}
if ($Json) {
    $output | ConvertTo-Json -Compress
}
else {
    Write-Host (
        'Project composition conformance passed: {0} complete loads, {1} packs, ' +
        '{2} reconciliation target types, and {3} rejected invalid compositions.' -f
        $output.composition_passes,
        $output.selected_packs,
        $output.reconciliation_target_types,
        $output.invalid_composition_cases
    )
}
