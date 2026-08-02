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
$fixtureData = ConvertFrom-KnowledgeYamlFile $fixturePath 1 'chronology fixture'
$fixture = ConvertTo-KnowledgeChronologyRegistry $fixtureData $fixturePath $packs @() @()
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
foreach ($vector in @($expectations.comparisons)) {
    $actual = Get-KnowledgeChronologyComparison $fixture ([string]$vector[0]) ([string]$vector[1])
    if ($actual -cne [string]$vector[2]) {
        throw "Chronology comparison $($vector[0])/$($vector[1]): expected $($vector[2]), got $actual"
    }
}

$invalidPaths = @(Get-ChildItem -LiteralPath $fixtureRoot -Filter 'invalid-*.yaml' | Sort-Object Name)
foreach ($path in $invalidPaths) {
    $rejected = $false
    try {
        $data = ConvertFrom-KnowledgeYamlFile $path.FullName 1 'invalid chronology fixture'
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
    coordinate_systems=[int]$registry.coordinate_systems.Count
    eras=[int]$registry.eras.Count
    fixture_comparisons=[int]@($expectations.comparisons).Count
    invalid_fixtures=[int]$invalidPaths.Count
    mappings=[int]@($registry.mappings).Count
    narrative_contexts=[int]@($registry.narrative_contexts).Count
    positions=[int]$registry.positions.Count
    relations=[int]@($registry.relations).Count
    schema_version=[int]$registry.schema_version
    spans=[int]@($registry.spans).Count
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        (
            'Chronology validation passed: schema {0}, {1} project coordinate system, {2} eras, ' +
            '{3} narrative context, {4} comparisons, and {5} malformed fixtures.'
        ) -f
        $summary.schema_version,
        $summary.coordinate_systems,
        $summary.eras,
        $summary.narrative_contexts,
        $summary.fixture_comparisons,
        $summary.invalid_fixtures
    )
}
