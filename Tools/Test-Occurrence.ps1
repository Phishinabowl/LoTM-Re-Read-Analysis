param(
  [string]$Root,
  [switch]$Json
)

. (Join-Path $PSScriptRoot 'Project-Config.ps1')
. (Join-Path $PSScriptRoot 'Schema-Pack-Config.ps1')
. (Join-Path $PSScriptRoot 'Resource-Config.ps1')
. (Join-Path $PSScriptRoot 'Source-Config.ps1')
. (Join-Path $PSScriptRoot 'Chronology-Config.ps1')
. (Join-Path $PSScriptRoot 'Occurrence-Config.ps1')

function Set-OccurrenceFixturePath{
  param([object]$Data,[string]$Path,[object]$Value)
  $parts=@($Path.Split('.'));$current=$Data
  for($index=0;$index -lt $parts.Count-1;$index++){$part=$parts[$index];if($current -is [System.Collections.IList]){$current=$current[[int]$part]}else{$current=$current[$part]}}
  $final=$parts[-1];if($current -is [System.Collections.IList]){$current[[int]$final]=$Value}else{$current[$final]=$Value}
}

function Get-OccurrenceIds{param([object[]]$Items);return @($Items|ForEach-Object {[string]$_.id})}
function Assert-OccurrenceIds{param([object[]]$Actual,[object[]]$Expected,[string]$Context);if((@($Actual)-join '|') -cne (@($Expected)-join '|')){throw "$Context expected '$(@($Expected)-join ',')', got '$(@($Actual)-join ',')'."}}

$repoRoot=Resolve-KnowledgeProjectRoot $Root
$project=Get-KnowledgeProjectConfig $repoRoot
$packs=Get-KnowledgeSchemaPackRegistry $project
$resources=Get-KnowledgeResourceConfig $project
$sources=Get-KnowledgeSourceRegistry $project $resources $packs
$chronology=Get-KnowledgeChronologyRegistry $project $packs @($sources.works.Keys) @($sources.continuities.Keys)
$registry=Get-KnowledgeOccurrenceRegistry $project $packs $chronology

$fixtureRoot=Join-Path $repoRoot 'Framework\Data\Occurrence'
$chronologyFixturePath=Join-Path $repoRoot 'Framework\Data\Chronology\valid-registry.yaml'
$chronologyFixtureData=ConvertFrom-KnowledgeYamlFile $chronologyFixturePath 1 'chronology fixture'
$chronologyFixture=ConvertTo-KnowledgeChronologyRegistry $chronologyFixtureData $chronologyFixturePath $packs @() @()
$fixturePath=Join-Path $fixtureRoot 'valid-registry.yaml'
$subjectTargets=[ordered]@{character=@('protagonist','observer')}
$payloadTargets=[ordered]@{'state-record'=@('protagonist-health')}
$fixtureData=ConvertFrom-KnowledgeYamlFile $fixturePath 3 'occurrence fixture'
$fixture=ConvertTo-KnowledgeOccurrenceRegistry $fixtureData $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
$expectations=Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw|ConvertFrom-Json

foreach($property in $expectations.iteration_occurrences.PSObject.Properties){Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOccurrencesForIteration $fixture $property.Name)) @($property.Value) "Iteration '$($property.Name)'"}
foreach($property in $expectations.position_occurrences.PSObject.Properties){Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOccurrencesAtPosition $fixture $property.Name)) @($property.Value) "Position '$($property.Name)'"}
foreach($property in $expectations.iteration_track_occurrences.PSObject.Properties){$parts=@($property.Name.Split('|',2));Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOccurrencesForIterationOnTrack $fixture $parts[0] $parts[1])) @($property.Value) "Iteration '$($parts[0])' on track '$($parts[1])'"}
foreach($vector in @($expectations.track_iteration_boundaries)){$previous=Get-KnowledgePreviousBeforeIteration $fixture ([string]$vector[0]) ([string]$vector[1]);$following=Get-KnowledgeNextAfterIteration $fixture ([string]$vector[0]) ([string]$vector[1]);if($previous.id -cne [string]$vector[2] -or $following.id -cne [string]$vector[3]){throw "Unexpected track boundaries for '$($vector[1])' on '$($vector[0])'."}}
foreach($vector in @($expectations.track_neighbors)){$previous=Get-KnowledgePreviousTrackOccurrence $fixture ([string]$vector[0]) ([string]$vector[1]);$following=Get-KnowledgeNextTrackOccurrence $fixture ([string]$vector[0]) ([string]$vector[1]);if($previous.id -cne [string]$vector[2] -or $following.id -cne [string]$vector[3]){throw "Unexpected track neighbors for '$($vector[1])'."}}
foreach($property in $expectations.carryovers_into.PSObject.Properties){Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeCarryoversIntoIteration $fixture $property.Name)) @($property.Value) "Carryover '$($property.Name)'"}
foreach($property in $expectations.occurrence_recurrences.PSObject.Properties){$recurrence=Get-KnowledgeOccurrenceRecurrence $fixture $property.Name;$actual=$(if($null -eq $recurrence){$null}else{$recurrence.id});if($actual -cne $property.Value){throw "Unexpected recurrence for '$($property.Name)'."}}
foreach($property in $expectations.occurrence_outcomes.PSObject.Properties){Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOutcomesForOccurrence $fixture $property.Name)) @($property.Value) "Outcomes '$($property.Name)'"}
foreach($property in $expectations.pattern_rules.PSObject.Properties){Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeRulesForRecurrencePattern $fixture $property.Name)) @($property.Value) "Rules '$($property.Name)'"}
foreach($property in $expectations.subject_state_transitions.PSObject.Properties){$parts=@($property.Name.Split('|',2));Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeStateTransitionsForSubject $fixture $parts[0] $parts[1])) @($property.Value) "States '$($property.Name)'"}
foreach($vector in @($expectations.state_at)){$state=Get-KnowledgeStateAt $fixture ([string]$vector[0]) ([string]$vector[1]) ([string]$vector[2]) ([string]$vector[3]) ([string]$vector[4]);$actual=$(if($null -eq $state){$null}else{$state.id});if($actual -cne $vector[5]){throw "Unexpected state at '$($vector[1])' on '$($vector[0])'."}}

$invalidCases=Get-Content -LiteralPath (Join-Path $fixtureRoot 'invalid-cases.json') -Raw|ConvertFrom-Json
foreach($case in @($invalidCases)){$invalid=ConvertFrom-KnowledgeYamlFile $fixturePath 3 'invalid occurrence fixture';foreach($change in @($case.changes)){Set-OccurrenceFixturePath $invalid ([string]$change.path) $change.value};$rejected=$false;try{$null=ConvertTo-KnowledgeOccurrenceRegistry $invalid $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets}catch{$rejected=$true};if(-not $rejected){throw "Malformed occurrence case unexpectedly loaded: $($case.name)"}}

$summary=[ordered]@{
  branches=[int]$registry.branches.Count
  carryovers=[int]@($registry.carryovers).Count
  causal_relations=[int]@($registry.causal_relations).Count
  fixture_queries=26
  invalid_cases=[int]@($invalidCases).Count
  iterations=[int]$registry.iterations.Count
  occurrences=[int]$registry.occurrences.Count
  outcomes=[int]@($registry.outcomes).Count
  recurrence_patterns=[int]$registry.recurrence_patterns.Count
  recurrences=[int]$registry.recurrences.Count
  rules=[int]@($registry.rules).Count
  schema_version=[int]$registry.schema_version
  templates=[int]$registry.templates.Count
  state_transitions=[int]@($registry.state_transitions).Count
  tracks=[int]$registry.tracks.Count
  transitions=[int]@($registry.transitions).Count
}
if($Json){$summary|ConvertTo-Json -Compress}else{Write-Output "Occurrence validation passed: schema $($summary.schema_version), $($summary.branches) project branch, $($summary.fixture_queries) fixture queries, and $($summary.invalid_cases) malformed cases."}
