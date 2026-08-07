param(
    [string]$Root,
    [switch]$Json
)

$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

$repoRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$project = Get-KnowledgeProjectConfig $repoRoot
$packs = Get-KnowledgeSchemaPackRegistry $project
$resources = Get-KnowledgeResourceConfig $project
$sources = Get-KnowledgeSourceRegistry $project $resources $packs
$registry = Get-KnowledgeChronologyRegistry $project $packs @($sources.works.Keys) @($sources.continuities.Keys)

$fixtureRoot = Join-Path $repoRoot 'Framework\Data\Chronology'
$fixturePath = Join-Path $fixtureRoot 'valid-registry.yaml'
$fixtureData = ConvertFrom-KnowledgeYamlFile $fixturePath 2 'chronology fixture'
$fixture = ConvertTo-KnowledgeChronologyRegistry $fixtureData $fixturePath $packs @() @()
$contextOnlyFixture = ConvertTo-KnowledgeChronologyRegistry $fixtureData $fixturePath $packs
if (@($contextOnlyFixture.contexts).Count -ne @($fixture.contexts).Count) {
    throw 'Context-only chronology loading changed when optional project targets were omitted.'
}
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
foreach ($vector in @($expectations.comparisons)) {
    $actual = Get-KnowledgeChronologyComparison $fixture ([string]$vector[0]) ([string]$vector[1])
    if ($actual -cne [string]$vector[2]) {
        throw "Chronology comparison $($vector[0])/$($vector[1]): expected $($vector[2]), got $actual"
    }
}

foreach ($vector in @($expectations.context_queries.from)) {
    $actualIds = @(
        Get-KnowledgeChronologyContextRelationsFrom $fixture ([string]$vector[0]) $vector[1] |
            ForEach-Object { $_.id }
    )
    if (($actualIds -join '|') -cne (@($vector[2]) -join '|')) {
        throw "Outgoing context relations for $($vector[0])/$($vector[1]) did not match."
    }
}
foreach ($vector in @($expectations.context_queries.to)) {
    $actualIds = @(
        Get-KnowledgeChronologyContextRelationsTo $fixture ([string]$vector[0]) $vector[1] |
            ForEach-Object { $_.id }
    )
    if (($actualIds -join '|') -cne (@($vector[2]) -join '|')) {
        throw "Incoming context relations for $($vector[0])/$($vector[1]) did not match."
    }
}
$contextTargets = [ordered]@{}
foreach ($property in @($expectations.context_targets.PSObject.Properties)) {
    $contextTargets[$property.Name] = @($property.Value)
}
Assert-KnowledgeChronologyContextRelationTargets $fixture $contextTargets
$emptyTargets = [ordered]@{}
foreach ($key in @($contextTargets.Keys)) {
    $emptyTargets[$key] = @()
}
$targetRejected = $false
try {
    Assert-KnowledgeChronologyContextRelationTargets $fixture $emptyTargets
}
catch {
    $targetRejected = $true
}
if (-not $targetRejected) {
    throw 'Unknown chronology context relation binding target unexpectedly validated.'
}
$disabledTopologyPacks = $packs.PSObject.Copy()
$disabledTopologyPacks.enabled_capabilities = @(
    $packs.enabled_capabilities | Where-Object { $_ -cne 'chronology-context-topology' }
)
$capabilityRejected = $false
try {
    $null = ConvertTo-KnowledgeChronologyRegistry $fixtureData $fixturePath $disabledTopologyPacks @() @()
}
catch {
    $capabilityRejected = $true
}
if (-not $capabilityRejected) {
    throw 'Chronology context topology loaded without its capability.'
}
$provenanceTargets = Get-KnowledgeChronologyProvenanceTargets $fixture
if (
    $provenanceTargets['chronology-position'].Count -ne $fixture.positions.Count -or
    $provenanceTargets['chronology-context'].Count -ne 4 -or
    $provenanceTargets['chronology-context-relation'].Count -ne 7 -or
    $provenanceTargets['chronology-context-relation-binding'].Count -ne 3
) {
    throw 'Chronology provenance target counts did not match the V50 fixture.'
}
$positionTarget = Get-KnowledgeChronologyProvenanceTarget $fixture 'chronology-position' 'civil-anchor'
if (-not [object]::ReferenceEquals($positionTarget, $fixture.positions['civil-anchor'])) {
    throw 'Chronology-position provenance lookup returned the wrong canonical record.'
}
if ((Get-KnowledgeChronologyProvenanceTargets $registry)['chronology-position'].Count -ne 0) {
    throw 'An empty chronology registry did not expose an empty chronology-position provider.'
}
$detachedTargets = Get-KnowledgeChronologyProvenanceTargets $fixture
[void]$detachedTargets['chronology-position'].Remove('civil-anchor')
if (-not $fixture.positions.Contains('civil-anchor') -or
    -not (Get-KnowledgeChronologyProvenanceTargets $fixture)['chronology-position'].Contains('civil-anchor')) {
    throw 'Mutating the chronology provider inventory changed canonical registry state.'
}
foreach ($invalidLookup in @(
        @('chronology-position', 'missing-position'),
        @('unknown', 'civil-anchor')
    )) {
    $rejected = $false
    try {
        $null = Get-KnowledgeChronologyProvenanceTarget $fixture $invalidLookup[0] $invalidLookup[1]
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw "Invalid chronology provenance lookup succeeded: $($invalidLookup[0]):$($invalidLookup[1])"
    }
}

$scaleCount = 128
$scaleData = ConvertFrom-KnowledgeYamlFile $fixturePath 2 'chronology scale fixture'
$scaleContexts = @($scaleData['contexts'])
$scaleRelations = @($scaleData['context_relations'])
for ($index = 0; $index -lt $scaleCount; $index++) {
    $scaleData['positions']['scale-position-{0:d3}' -f $index] = [ordered]@{
        coordinate_system_id = 'control-step'
        value = 1000 + $index
        era_id = $null
        label = 'Scale Position {0:d3}' -f $index
        certainty = 'exact'
    }
    $scaleContexts += [ordered]@{
        id = "scale-context-$index"
        label = "Scale Context $index"
        coordinate_system_id = 'control-step'
        role = 'operational'
        continuity_ids = @()
        work_ids = @()
        branch_id = $null
    }
    $scaleRelations += [ordered]@{
        id = "scale-relation-$index"
        source_context_id = "scale-context-$index"
        relation_type = 'observes'
        target_context_id = "scale-context-$(($index + 1) % $scaleCount)"
        certainty = 'exact'
        bindings = @()
    }
}
$scaleData['contexts'] = @($scaleContexts)
$scaleData['context_relations'] = @($scaleRelations)
$scaleFixture = ConvertTo-KnowledgeChronologyRegistry `
    $scaleData `
(Join-Path $fixtureRoot 'generated-scale-registry.yaml') `
    $packs `
@() `
@()
if (@($scaleFixture.context_relations).Count -ne @($fixture.context_relations).Count + $scaleCount) {
    throw 'Chronology context topology scale extension did not retain every generated relation.'
}
$scaleProvenanceTargets = Get-KnowledgeChronologyProvenanceTargets $scaleFixture
if ($scaleProvenanceTargets['chronology-position'].Count -ne $fixture.positions.Count + $scaleCount) {
    throw 'Chronology-position provider did not retain every generated scale position.'
}

$invalidPaths = @(Get-ChildItem -LiteralPath $fixtureRoot -Filter 'invalid-*.yaml' | Sort-Object Name)
foreach ($path in $invalidPaths) {
    $rejected = $false
    try {
        $data = ConvertFrom-KnowledgeYamlFile $path.FullName 2 'invalid chronology fixture'
        $null = ConvertTo-KnowledgeChronologyRegistry $data $path.FullName $packs @() @()
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw "Malformed chronology fixture unexpectedly loaded: $($path.Name)"
    }
}

$summary = [ordered]@{
    contexts=[int]@($registry.contexts).Count
    context_relations=[int]@($registry.context_relations).Count
    coordinate_systems=[int]$registry.coordinate_systems.Count
    eras=[int]$registry.eras.Count
    fixture_comparisons=[int]@($expectations.comparisons).Count
    invalid_fixtures=[int]$invalidPaths.Count
    mappings=[int]@($registry.mappings).Count
    fixture_context_queries=[int]@($expectations.context_queries.from).Count + [int]@($expectations.context_queries.to).Count
    positions=[int]$registry.positions.Count
    empty_provider_checks=1
    provider_isolation_checks=1
    relations=[int]@($registry.relations).Count
    schema_version=[int]$registry.schema_version
    scale_context_relations=[int]$scaleCount
    scale_positions=[int]$scaleCount
    spans=[int]@($registry.spans).Count
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        (
            'Chronology validation passed: schema {0}, {1} project coordinate system, {2} eras, ' +
            '{3} context, {4} context relations, {5} comparisons, {6} topology queries, and {7} malformed fixtures.'
        ) -f
        $summary.schema_version,
        $summary.coordinate_systems,
        $summary.eras,
        $summary.contexts,
        $summary.context_relations,
        $summary.fixture_comparisons,
        $summary.fixture_context_queries,
        $summary.invalid_fixtures
    )
}
