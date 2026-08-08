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
        pack_presentations = @($Document.packs | Where-Object { $null -ne $_.presentation }).Count
        capabilities = $capabilities.Count
        available_capabilities = @($capabilities | Where-Object available).Count
        enabled_capabilities = @($capabilities | Where-Object enabled).Count
        planned_capabilities = @($capabilities | Where-Object planned).Count
        deprecated_capabilities = @($capabilities | Where-Object deprecated).Count
        capability_presentations = @($capabilities | Where-Object { $null -ne $_.presentation }).Count
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
$module = Get-Module KnowledgeFramework
$catalogModel = & $module { param($Value) Get-KnowledgeFrameworkCatalogModel $Value } $Root
$catalogPacks = & $module {
    param($Project, $Catalog)
    Get-KnowledgeSchemaPackRegistryFromCatalog $Project $Catalog
} $project $catalogModel
if ((ConvertTo-KnowledgeCanonicalJson $packs) -cne (ConvertTo-KnowledgeCanonicalJson $catalogPacks)) {
    throw 'Catalog-backed schema-pack composition differs from the direct shadow path.'
}
$taxonomy = Get-KnowledgeTaxonomyConfig $project
$resources = Get-KnowledgeResourceConfig $project
$schema = New-KnowledgeEffectiveProjectSchema $project $packs $taxonomy $resources
$catalogSchema = New-KnowledgeEffectiveProjectSchema $project $catalogPacks $taxonomy $resources
if ((ConvertTo-KnowledgeCanonicalJson $schema) -cne (ConvertTo-KnowledgeCanonicalJson $catalogSchema)) {
    throw 'Catalog-backed effective schema differs from the direct shadow composition.'
}
if (
    (ConvertTo-KnowledgeCanonicalJson (Get-KnowledgeEffectiveProjectSchema $Root)) -cne
    (ConvertTo-KnowledgeCanonicalJson $catalogSchema)
) {
    throw 'Effective-schema loading did not use the catalog-backed composition.'
}
$reportModel = New-KnowledgeEffectiveSchemaReportModel $schema
if ($reportModel.report_contract -cne 'effective-project-schema-report-model') {
    throw 'Effective-schema report model contract changed.'
}
if ($reportModel.source_contract -cne $schema.contract -or $reportModel.contract -cne $schema.contract) {
    throw 'Effective-schema report model lost source-contract identity.'
}
if ([int]$reportModel.summary.selected_packs -ne @($schema.packs).Count) {
    throw 'Effective-schema report summary does not describe the composed schema.'
}
$markdown = ConvertTo-KnowledgeEffectiveSchemaMarkdown $reportModel
$secondMarkdown = ConvertTo-KnowledgeEffectiveSchemaMarkdown (New-KnowledgeEffectiveSchemaReportModel $schema)
if ($markdown -cne $secondMarkdown) {
    throw 'Effective-schema Markdown rendering is not deterministic.'
}
$requiredMarkdown = @(
    'generated_type: effective-schema-qa-report'
    'canonical: false'
    '# Effective Project Schema'
    '## Selected Packs'
    '## Capabilities'
    '## Diagnostics'
)
foreach ($value in $requiredMarkdown) {
    if (-not $markdown.Contains($value)) {
        throw 'Effective-schema Markdown report is missing required sections or metadata.'
    }
}
if ($markdown.Contains([System.IO.Path]::GetFullPath($Root)) -or $markdown.Contains('generated_at')) {
    throw 'Effective-schema Markdown report contains machine-specific or temporal data.'
}
$wrongFramework = $project.PSObject.Copy()
$wrongFramework.framework = 'wrong-framework'
try {
    $null = & $module {
        param($Project, $Catalog)
        Get-KnowledgeSchemaPackRegistryFromCatalog $Project $Catalog
    } $wrongFramework $catalogModel
    throw 'Catalog-backed composition accepted a mismatched framework ID.'
}
catch {
    if ($_.Exception.Message -cnotmatch 'does not match installed framework') {
        throw
    }
}
$wrongLookup = $project.PSObject.Copy()
$wrongLookup.lookup_keys_registry = $project.manifest_path
try {
    $null = & $module {
        param($Project, $Catalog)
        Get-KnowledgeSchemaPackRegistryFromCatalog $Project $Catalog
    } $wrongLookup $catalogModel
    throw 'Catalog-backed composition accepted a mismatched lookup-key registry.'
}
catch {
    if ($_.Exception.Message -cnotmatch 'does not match the framework installation') {
        throw
    }
}

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
if (@($schema.packs | Where-Object { $null -eq $_.classification -or $null -eq $_.presentation }).Count -ne 0) {
    throw 'Effective schema lost selected-pack classification or presentation.'
}
if (@($schema.capabilities | Where-Object { $null -eq $_.presentation }).Count -ne 0) {
    throw 'Effective schema lost capability presentation.'
}
if (@($schema.packs | Where-Object { $null -ne $_.presentation.visual }).Count -ne 0) {
    throw 'Effective schema invented optional pack visual metadata.'
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

$lookupKeys = Get-KnowledgeLookupKeyConfig $project
$selection = New-KnowledgeEffectiveSchemaSelection `
    $schema `
    $lookupKeys `
    'Narrative-Media' `
    'Narrative-Time-Loops'
if (
    [int]$selection.source_contract_version -ne [int]$schema.contract_version -or
    (@($selection.packs | ForEach-Object id) -join '|') -cne 'narrative-media' -or
    (@($selection.capabilities | ForEach-Object id) -join '|') -cne 'narrative-time-loops'
) {
    throw 'Effective-schema normalized singular selection changed.'
}
$unknownRejected = $false
try {
    $null = New-KnowledgeEffectiveSchemaSelection $schema $lookupKeys 'missing-pack' $null
}
catch {
    $unknownRejected = $true
}
if (-not $unknownRejected) {
    throw 'Effective-schema selection accepted an unknown pack ID.'
}
$duplicatePack = [ordered]@{}
foreach ($key in $schema.packs[0].Keys) {
    $duplicatePack[$key] = $schema.packs[0][$key]
}
$duplicatePack.id = $schema.packs[0].id.ToUpperInvariant()
$originalPacks = @($schema.packs)
$schema.packs = @($originalPacks) + @($duplicatePack)
$ambiguousRejected = $false
try {
    $null = New-KnowledgeEffectiveSchemaSelection `
        $schema `
        $lookupKeys `
    ([System.Globalization.CultureInfo]::InvariantCulture.TextInfo.ToTitleCase($originalPacks[0].id)) `
        $null
}
catch {
    $ambiguousRejected = $true
}
finally {
    $schema.packs = $originalPacks
}
if (-not $ambiguousRejected) {
    throw 'Effective-schema selection accepted an ambiguous normalized pack ID.'
}

$consumerIds = @('qa', 'visualization')
$consumerProjections = @{}
foreach ($consumerId in $consumerIds) {
    $consumerProjections[$consumerId] = New-KnowledgeEffectiveConsumerSchemaProjection $schema $consumerId
}
$retiredConsumerApis = @(
    'Assert-KnowledgeConsumerSchemaShadow'
    'Compare-KnowledgeConsumerSchemaProjection'
    'New-KnowledgeLegacyConsumerSchemaProjection'
)
$exportedCommands = @(Get-Module KnowledgeFramework).ExportedCommands
if (@($retiredConsumerApis | Where-Object { $exportedCommands.ContainsKey($_) }).Count -gt 0) {
    throw 'Retired effective-schema shadow APIs remain publicly exported.'
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

$visualizationProjection = $consumerProjections['visualization']
if ((@($visualizationProjection.roots.Keys | Sort-Object) -join '|') -cne 'glossary') {
    throw 'Effective Visualization discovery roots changed.'
}
if ((@($visualizationProjection.content_types.Keys | Sort-Object) -join '|') -cne 'glossary-page') {
    throw 'Effective Visualization content types changed.'
}
$tarotCard = $visualizationProjection.records['tarot card']
if (
    $tarotCard.relative_folder -cne 'Tarot_Cards' -or
    $tarotCard.slug_prefix -cne 'tarot-card' -or
    $tarotCard.graph_class -cne 'tarot' -or
    'tarot-card-the-star' -cnotmatch $tarotCard.slug_pattern
) {
    throw 'Effective Visualization record discovery changed.'
}
$requiredVisualizationCapabilities = @(
    'graph-projection'
    'reader-disclosure'
    'spoiler-bounding'
    'visibility-policy'
)
$missingVisualizationCapabilities = @(
    $requiredVisualizationCapabilities | Where-Object {
        $state = $visualizationProjection.capability_state[$_]
        -not [bool]$state.available -or -not [bool]$state.enabled
    }
)
if ($missingVisualizationCapabilities.Count -gt 0) {
    throw 'Effective Visualization projection capabilities changed.'
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
    selection_cases = 3
    failure_cases = 1
    consumer_projection_modes = $consumerIds.Count
    retired_consumer_apis = $retiredConsumerApis.Count
    qa_discovery_content_types = $qaProjection.content_types.Count
    qa_discovery_categories = $qaProjection.categories.Count
    qa_discovery_placements = $qaProjection.placements.Count
    qa_discovery_records = $qaProjection.records.Count
    visualization_discovery_content_types = $visualizationProjection.content_types.Count
    visualization_discovery_categories = $visualizationProjection.categories.Count
    visualization_discovery_records = $visualizationProjection.records.Count
    report_model_cases = 3
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
