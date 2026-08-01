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
function New-SyntheticOccurrenceRule{
  param([string]$RuleId,[string]$RuleKind,[string]$EffectKind,[string]$TargetId,[string]$OccurrenceTemplate)
  return [ordered]@{
    id=$RuleId;label="Synthetic $EffectKind extension";pattern_id='outer-loop-pattern';rule_kind=$RuleKind;condition_logic='all'
    applicability=[ordered]@{application_level='pattern-default';recurrence_ids=@();phase_ids=@();branch_ids=@();min_iteration_ordinal=2;max_iteration_ordinal=2;chronology_window=$null;effective_window=$null}
    priority=10;resolution_group="synthetic-$EffectKind";selection_mode='accumulate';override_mode='inherit'
    conditions=@([ordered]@{id="$RuleId-condition";condition_kind='occurrence-reached';target_type='occurrence-template';target_id=$OccurrenceTemplate;expected_value='occurred';subject_type=$null;subject_id=$null;state_kind=$null;track_id=$null;comparison_value=$null})
    effects=@([ordered]@{id="$RuleId-effect";effect_kind=$EffectKind;target_type='recurrence-pattern';target_id=$TargetId})
  }
}

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
$fixtureData=ConvertFrom-KnowledgeYamlFile $fixturePath 4 'occurrence fixture'
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
foreach($property in $expectations.iteration_phases.PSObject.Properties){$phase=Get-KnowledgeRecurrencePhaseForIteration $fixture $property.Name;$actual=$(if($null -eq $phase){$null}else{$phase.id});if($actual -cne $property.Value){throw "Unexpected recurrence phase for '$($property.Name)'."}}
foreach($vector in @($expectations.schedule_values)){if((Get-KnowledgeRecurrenceScheduleValue $fixture ([string]$vector[0]) ([int]$vector[1])) -cne $vector[2]){throw "Unexpected schedule value for '$($vector[0])' ordinal $($vector[1])."}}
foreach($vector in @($expectations.schedule_errors)){$actualError=$null;try{$null=Get-KnowledgeRecurrenceScheduleValue $fixture ([string]$vector[0]) ([int]$vector[1])}catch{$actualError=$_.Exception.Message};if($actualError -cne [string]$vector[2]){throw "Unexpected schedule error for '$($vector[0])': $actualError"}}
foreach($vector in @($expectations.schedule_matches)){$effective=$vector[3];if((Get-KnowledgeRecurrenceScheduleMatch $fixture ([string]$vector[0]) ([string]$vector[1]) ([string]$vector[2]) $effective) -cne [string]$vector[4]){throw "Unexpected schedule match for '$($vector[0])' at '$($vector[2])'."}}
foreach($vector in @($expectations.rule_evaluations)){$evaluation=Get-KnowledgeRecurrenceRuleEvaluation $fixture ([string]$vector[0]) ([string]$vector[1]) $vector[2];Assert-OccurrenceIds @($evaluation.selected_rule_ids) @($vector[4]) "Selected rules at '$($vector[1])'";Assert-OccurrenceIds @($evaluation.effects|ForEach-Object {$_.effect_kind}) @($vector[5]) "Effects at '$($vector[1])'";Assert-OccurrenceIds @($evaluation.conflicts) @($vector[6]) "Conflicts at '$($vector[1])'";if($evaluation.status -cne [string]$vector[3]){throw "Unexpected rule evaluation status at '$($vector[1])'."}}
foreach($vector in @($expectations.trace_dispositions)){$evaluation=Get-KnowledgeRecurrenceRuleEvaluation $fixture ([string]$vector[0]) ([string]$vector[1]) $vector[2];$trace=@($evaluation.traces|Where-Object {$_.rule_id -ceq [string]$vector[3]})[0];if($trace.disposition -cne [string]$vector[4]){throw "Unexpected trace disposition for rule '$($vector[3])'."}}
foreach($property in $expectations.subject_state_transitions.PSObject.Properties){$parts=@($property.Name.Split('|',2));Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeStateTransitionsForSubject $fixture $parts[0] $parts[1])) @($property.Value) "States '$($property.Name)'"}
foreach($vector in @($expectations.state_at)){$state=Get-KnowledgeStateAt $fixture ([string]$vector[0]) ([string]$vector[1]) ([string]$vector[2]) ([string]$vector[3]) ([string]$vector[4]);$actual=$(if($null -eq $state){$null}else{$state.id});if($actual -cne $vector[5]){throw "Unexpected state at '$($vector[1])' on '$($vector[0])'."}}

$invalidCases=Get-Content -LiteralPath (Join-Path $fixtureRoot 'invalid-cases.json') -Raw|ConvertFrom-Json
foreach($case in @($invalidCases)){$invalid=ConvertFrom-KnowledgeYamlFile $fixturePath 4 'invalid occurrence fixture';foreach($change in @($case.changes)){Set-OccurrenceFixturePath $invalid ([string]$change.path) $change.value};$rejected=$false;try{$null=ConvertTo-KnowledgeOccurrenceRegistry $invalid $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets}catch{$rejected=$true};if(-not $rejected){throw "Malformed occurrence case unexpectedly loaded: $($case.name)"}}

$extensionValues=[ordered]@{
  'occurrence.rule-kind'=@('pause','signal')
  'occurrence.rule-effect-kind'=@('pause-recurrence','signal-recurrence')
  'occurrence.rule-effect-kind-target-type'=@('pause-recurrence-uses-recurrence-pattern','signal-recurrence-uses-recurrence-pattern')
  'occurrence.rule-kind-effect-kind'=@('pause-uses-pause-recurrence','signal-uses-signal-recurrence')
  'occurrence.rule-effect-pattern-scope'=@('pause-recurrence-uses-owning-pattern','signal-recurrence-allows-external-pattern')
  'occurrence.rule-effect-incompatibility-pair'=@('advance-iteration-with-pause-recurrence')
}
foreach($namespace in $extensionValues.Keys){$packs.controlled_values[$namespace]=@($packs.controlled_values[$namespace])+@($extensionValues[$namespace])}

$owningProbe=ConvertFrom-KnowledgeYamlFile $fixturePath 4 'occurrence fixture';$owningProbe['rules']=@($owningProbe['rules'])+@(New-SyntheticOccurrenceRule 'synthetic-pause-rule' 'pause' 'pause-recurrence' 'outer-loop-pattern' 'reset')
$owningRegistry=ConvertTo-KnowledgeOccurrenceRegistry $owningProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
$owningEvaluation=Get-KnowledgeRecurrenceRuleEvaluation $owningRegistry 'outer-loop' 'reset-two'
if($owningEvaluation.status -cne 'conflict'){throw 'Owning-pattern extension did not produce a conflict.'};Assert-OccurrenceIds @($owningEvaluation.selected_rule_ids) @('outer-reset-rule','synthetic-pause-rule') 'Owning-pattern extension selected rules';Assert-OccurrenceIds @($owningEvaluation.conflicts) @('advance-iteration conflicts with pause-recurrence') 'Owning-pattern extension conflicts'

$foreignOwningProbe=ConvertFrom-KnowledgeYamlFile $fixturePath 4 'occurrence fixture';$foreignOwningRule=New-SyntheticOccurrenceRule 'synthetic-pause-rule' 'pause' 'pause-recurrence' 'inner-loop-pattern' 'reset';$foreignOwningProbe['rules']=@($foreignOwningProbe['rules'])+@($foreignOwningRule);$foreignRejected=$false;try{$null=ConvertTo-KnowledgeOccurrenceRegistry $foreignOwningProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets}catch{$foreignRejected=$true};if(-not $foreignRejected){throw 'Owning-pattern extension unexpectedly accepted a foreign pattern target.'}

$externalProbe=ConvertFrom-KnowledgeYamlFile $fixturePath 4 'occurrence fixture';$externalProbe['rules']=@($externalProbe['rules'])+@(New-SyntheticOccurrenceRule 'synthetic-signal-rule' 'signal' 'signal-recurrence' 'inner-loop-pattern' 'bell')
$externalRegistry=ConvertTo-KnowledgeOccurrenceRegistry $externalProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
$externalEvaluation=Get-KnowledgeRecurrenceRuleEvaluation $externalRegistry 'outer-loop' 'bell-two'
if($externalEvaluation.status -cne 'selected'){throw 'External-pattern extension was not selected.'};Assert-OccurrenceIds @($externalEvaluation.selected_rule_ids) @('synthetic-signal-rule') 'External-pattern extension selected rules';Assert-OccurrenceIds @($externalEvaluation.effects|ForEach-Object {$_.target_id}) @('inner-loop-pattern') 'External-pattern extension targets'

$summary=[ordered]@{
  branches=[int]$registry.branches.Count
  carryovers=[int]@($registry.carryovers).Count
  causal_relations=[int]@($registry.causal_relations).Count
  fixture_queries=54
  invalid_cases=[int]@($invalidCases).Count
  iterations=[int]$registry.iterations.Count
  phases=[int]$registry.phases.Count
  schedules=[int]$registry.schedules.Count
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
