param(
  [string]$Root,
  [switch]$Json
)

$projectHelper=Join-Path $PSScriptRoot 'Project-Config.ps1';. $projectHelper
$packHelper=Join-Path $PSScriptRoot 'Schema-Pack-Config.ps1';. $packHelper
$resourceHelper=Join-Path $PSScriptRoot 'Resource-Config.ps1';. $resourceHelper
$sourceHelper=Join-Path $PSScriptRoot 'Source-Config.ps1';. $sourceHelper
$chronologyHelper=Join-Path $PSScriptRoot 'Chronology-Config.ps1';. $chronologyHelper

$repoRoot=Resolve-KnowledgeProjectRoot $Root
$project=Get-KnowledgeProjectConfig $repoRoot
$packs=Get-KnowledgeSchemaPackRegistry $project
$resources=Get-KnowledgeResourceConfig $project
$sources=Get-KnowledgeSourceRegistry $project $resources $packs
$registry=Get-KnowledgeChronologyRegistry $project $packs @($sources.works.Keys) @($sources.continuities.Keys)

$fixtureRoot=Join-Path $repoRoot 'Framework\Data\Chronology'
$fixturePath=Join-Path $fixtureRoot 'valid-registry.yaml'
$fixtureData=ConvertFrom-KnowledgeYamlFile $fixturePath 1 'chronology fixture'
$fixture=ConvertTo-KnowledgeChronologyRegistry $fixtureData $fixturePath $packs @() @()
$expectations=Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
foreach($vector in @($expectations.comparisons)){
  $actual=Get-KnowledgeChronologyComparison $fixture ([string]$vector[0]) ([string]$vector[1])
  if($actual -cne [string]$vector[2]){throw "Chronology comparison $($vector[0])/$($vector[1]): expected $($vector[2]), got $actual"}
}

$invalidPaths=@(Get-ChildItem -LiteralPath $fixtureRoot -Filter 'invalid-*.yaml' | Sort-Object Name)
foreach($path in $invalidPaths){
  $rejected=$false
  try{$data=ConvertFrom-KnowledgeYamlFile $path.FullName 1 'invalid chronology fixture';$null=ConvertTo-KnowledgeChronologyRegistry $data $path.FullName $packs @() @()}
  catch{$rejected=$true}
  if(-not $rejected){throw "Malformed chronology fixture unexpectedly loaded: $($path.Name)"}
}

$summary=[ordered]@{
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
if($Json){$summary|ConvertTo-Json -Compress}else{Write-Output "Chronology validation passed: schema $($summary.schema_version), $($summary.coordinate_systems) project coordinate system, $($summary.eras) eras, $($summary.narrative_contexts) narrative context, $($summary.fixture_comparisons) comparisons, and $($summary.invalid_fixtures) malformed fixtures."}
