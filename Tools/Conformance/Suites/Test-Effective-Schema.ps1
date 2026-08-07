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

function ConvertTo-CompactJson {
    param([object]$Value)
    return $Value | ConvertTo-Json -Depth 100 -Compress
}

function Get-EffectiveSchemaSummary {
    param(
        [object]$Document,
        [int]$ScaleCapabilities
    )

    $capabilities = @($Document.capabilities)
    return [ordered]@{
        schema_version = 1
        contract = $Document.contract
        contract_version = [int]$Document.contract_version
        project_id = $Document.project.project_id
        packs = @($Document.packs).Count
        active_packs = @($Document.packs | Where-Object lifecycle -eq 'active').Count
        capabilities = $capabilities.Count
        available_capabilities = @($capabilities | Where-Object available).Count
        enabled_capabilities = @($capabilities | Where-Object enabled).Count
        planned_capabilities = @($capabilities | Where-Object planned).Count
        deprecated_capabilities = @($capabilities | Where-Object deprecated).Count
        controlled_value_namespaces = @($Document.controlled_value_namespaces).Count
        content_roots = @($Document.content.roots).Count
        content_types = @($Document.content.content_types).Count
        categories = @($Document.content.categories).Count
        resource_roots = @($Document.resources.roots).Count
        resource_kinds = @($Document.resources.kinds).Count
        resource_types = @($Document.resources.types).Count
        diagnostic_codes = @($Document.diagnostics | ForEach-Object code)
        scale_capabilities = $ScaleCapabilities
    }
}

$project = Get-KnowledgeProjectConfig $Root
$packs = Get-KnowledgeSchemaPackRegistry $project
$taxonomy = Get-KnowledgeTaxonomyConfig $project
$resources = Get-KnowledgeResourceConfig $project
$schema = New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources

$expectedKeys = @(
    'contract',
    'contract_version',
    'project',
    'registry_schema_versions',
    'packs',
    'capabilities',
    'controlled_value_namespaces',
    'content',
    'resources',
    'diagnostics'
)
if ((@($schema.Keys) -join '|') -cne ($expectedKeys -join '|')) {
    throw 'Effective schema top-level property order changed.'
}
if (@($schema.packs | Where-Object lifecycle -ne 'active').Count -ne 0) {
    throw 'Effective schema did not preserve selected pack lifecycle.'
}
$firstJson = ConvertTo-CompactJson $schema
$secondJson = ConvertTo-CompactJson (New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources)
if ($firstJson -cne $secondJson) {
    throw 'Repeated effective-schema composition was not byte deterministic.'
}
if ($firstJson.Contains([System.IO.Path]::GetFullPath($Root))) {
    throw 'Effective schema leaked an absolute project path.'
}
$originalDirectory = (Get-Location).Path
try {
    Set-Location ([System.IO.Path]::GetTempPath())
    $alternateDirectoryJson = ConvertTo-CompactJson (
        New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources
    )
}
finally {
    Set-Location $originalDirectory
}
if ($firstJson -cne $alternateDirectoryJson) {
    throw 'Effective-schema composition changed with the process working directory.'
}

$consumerShadowModes = @('qa', 'visualization')
$consumerProjections = @{}
foreach ($consumerId in $consumerShadowModes) {
    $legacyProjection = New-KnowledgeLegacyConsumerSchemaProjection $project $packs $taxonomy $consumerId
    $effectiveProjection = New-KnowledgeEffectiveConsumerSchemaProjection $schema $consumerId
    Assert-KnowledgeConsumerSchemaShadow $consumerId $legacyProjection $effectiveProjection
    $consumerProjections[$consumerId] = $effectiveProjection
}

$qaProjection = $consumerProjections['qa']
if ((@($qaProjection.roots.Keys | Sort-Object) -join '|') -cne 'glossary|volumes') {
    throw 'Effective QA discovery roots changed.'
}
$character = $qaProjection.categories.character
if ($character.label -cne 'Character' -or $character.plural_label -cne 'Characters') {
    throw 'Effective QA category labels changed.'
}
if ($qaProjection.placements['character|glossary-page'].relative_folder -cne 'Characters') {
    throw 'Effective QA category placement changed.'
}
$volume = $qaProjection.records['volume summary']
if (
    $volume.content_type_id -cne 'volume-summary' -or
    $volume.export_folder -cne 'Volumes' -or
    $volume.slug_prefix -cne 'volume' -or
    'volume-01-clown' -cnotmatch $volume.slug_pattern
) {
    throw 'Effective QA fixed-record slug configuration changed.'
}
if ('volume-1' -cmatch $volume.slug_pattern) {
    throw 'Effective QA fixed-record slug matching accepted a non-page volume identifier.'
}

$legacyProjection = New-KnowledgeLegacyConsumerSchemaProjection $project $packs $taxonomy 'qa'
$driftedProjection = New-KnowledgeEffectiveConsumerSchemaProjection $schema 'qa'
$driftedProjection.roots.glossary.relative_path = 'Changed_Glossary'
$expectedDifference = 'roots.glossary.relative_path: legacy="Glossary_Threads"; effective="Changed_Glossary"'
$differences = @(Compare-KnowledgeConsumerSchemaProjection $legacyProjection $driftedProjection)
if ($differences.Count -ne 1 -or $differences[0] -cne $expectedDifference) {
    throw "Consumer shadow mismatch detail changed: $($differences -join ' | ')"
}
try {
    Assert-KnowledgeConsumerSchemaShadow 'qa' $legacyProjection $driftedProjection
    throw 'Consumer shadow accepted a drifted effective projection.'
}
catch {
    if (-not $_.Exception.Message.Contains($expectedDifference)) {
        throw "Consumer shadow failure omitted its exact path: $($_.Exception.Message)"
    }
}

$planned = @($schema.capabilities | Where-Object planned | Select-Object -First 1)
if ($planned.Count -ne 1 -or $planned[0].available -or -not $planned[0].disabled) {
    throw 'Planned capability state is inconsistent.'
}

$selected = @($schema.capabilities | Where-Object enabled | Select-Object -First 1)[0]
$capabilityId = $selected.id
$providerId = @($packs.capability_providers[$capabilityId])[0]
$originalEnabled = @($packs.enabled_capabilities)
$packs.enabled_capabilities = @($originalEnabled | Where-Object { $_ -cne $capabilityId })
$disabledSchema = New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources
$disabled = @($disabledSchema.capabilities | Where-Object id -eq $capabilityId)[0]
if (-not $disabled.available -or $disabled.enabled -or -not $disabled.disabled) {
    throw 'Available-but-disabled capability state is inconsistent.'
}
$packs.enabled_capabilities = $originalEnabled

$definition = $packs.capability_definitions["$providerId|$capabilityId"]
$originalLifecycle = $definition.lifecycle
$definition.lifecycle = 'deprecated'
$deprecatedSchema = New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources
$deprecated = @($deprecatedSchema.capabilities | Where-Object id -eq $capabilityId)[0]
if (-not $deprecated.deprecated -or -not $deprecated.enabled) {
    throw 'Deprecated enabled capability did not retain activation state.'
}
if (@($deprecatedSchema.diagnostics | Where-Object code -eq 'deprecated-capability-enabled').Count -ne 1) {
    throw 'Deprecated enabled capability did not emit its diagnostic.'
}
$definition.lifecycle = $originalLifecycle

$secondProvider = @($packs.selection_order | Where-Object { $_ -cne $providerId } | Select-Object -First 1)[0]
$originalProviders = @($packs.capability_providers[$capabilityId])
$packs.capability_providers[$capabilityId] = @($providerId, $secondProvider)
$secondaryKey = "$secondProvider|$capabilityId"
$packs.capability_definitions[$secondaryKey] = [pscustomobject]@{
    id = $capabilityId
    lifecycle = 'planned'
    label = 'Synthetic secondary provider'
    description = $null
}
$ambiguousSchema = New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources
$ambiguous = @($ambiguousSchema.capabilities | Where-Object id -eq $capabilityId)[0]
if (@($ambiguous.providers).Count -ne 2 -or $ambiguous.effective_lifecycle -cne 'available') {
    throw 'Multiple-provider lifecycle resolution is inconsistent.'
}
if (@($ambiguousSchema.diagnostics | Where-Object code -eq 'multiple-capability-providers').Count -ne 1) {
    throw 'Multiple capability providers did not emit their diagnostic.'
}
$packs.capability_providers[$capabilityId] = $originalProviders
$packs.capability_definitions.Remove($secondaryKey)

$scaleCount = 400
$scaleIds = @()
for ($index = 0; $index -lt $scaleCount; $index += 1) {
    $scaleId = 'scale-capability-{0:d3}' -f $index
    $scaleIds += $scaleId
    $packs.capability_providers[$scaleId] = @($providerId)
    $packs.capability_definitions["$providerId|$scaleId"] = [pscustomobject]@{
        id = $scaleId
        lifecycle = 'available'
        label = $null
        description = $null
    }
}
$packs.declared_capabilities = @($packs.declared_capabilities) + $scaleIds
$packs.available_capabilities = @($packs.available_capabilities) + $scaleIds
$scaleSchema = New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources
if (@($scaleSchema.capabilities).Count -ne @($schema.capabilities).Count + $scaleCount) {
    throw 'Effective schema scale composition lost capabilities.'
}

$failure = New-KnowledgeEffectiveSchemaFailure (
    [System.ArgumentException]::new("Schema pack 'child' requires unselected pack 'base'.")
)
if ($null -ne $failure.schema -or $failure.diagnostics[0].code -cne 'missing-pack-dependency') {
    throw 'Effective schema failure classification changed.'
}

$expectedPath = Join-Path $Root 'Framework\Data\Effective-Schema\expected-summary.json'
$expected = Get-Content -LiteralPath $expectedPath -Raw | ConvertFrom-Json
$actual = Get-EffectiveSchemaSummary $schema $scaleCount
if ((ConvertTo-CompactJson $actual) -cne (ConvertTo-CompactJson $expected)) {
    throw "Effective schema summary changed.`nExpected: $(ConvertTo-CompactJson $expected)`nActual: $(ConvertTo-CompactJson $actual)"
}

$result = [ordered]@{
    schema_version = 1
    status = 'passed'
    summary = $actual
    deterministic_passes = 3
    synthetic_states = 4
    failure_cases = 1
    consumer_shadow_modes = $consumerShadowModes.Count
    consumer_shadow_failure_cases = 1
    qa_discovery_content_types = $qaProjection.content_types.Count
    qa_discovery_categories = $qaProjection.categories.Count
    qa_discovery_placements = $qaProjection.placements.Count
    qa_discovery_records = $qaProjection.records.Count
}
if ($Json) {
    $result | ConvertTo-Json -Depth 100 -Compress
}
else {
    Write-Output (
        'Effective-schema conformance passed: {0} packs, {1} capabilities, {2} namespaces, and {3} scale capabilities.' -f
        $actual.packs,
        $actual.capabilities,
        $actual.controlled_value_namespaces,
        $scaleCount
    )
}
