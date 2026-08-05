param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

function Set-OccurrenceFixturePath {
    param([object]$Data, [string]$Path, [object]$Value)
    $parts = @($Path.Split('.'))
    $current = $Data
    for ($index = 0; $index -lt $parts.Count - 1; $index++) {
        $part = $parts[$index]
        if ($current -is [System.Collections.IList]) {
            $current = $current[[int]$part]
        }
        else {
            $current = $current[$part]
        }
    }
    $final = $parts[-1]
    if ($current -is [System.Collections.IList]) {
        $current[[int]$final] = $Value
    }
    else {
        $current[$final] = $Value
    }
}

function Get-OccurrenceIds {
    param([object[]]$Items)
    return @($Items | ForEach-Object { [string]$_.id })
}
function Assert-OccurrenceIds {
    param([object[]]$Actual, [object[]]$Expected, [string]$Context)
    if ((@($Actual) -join '|') -cne (@($Expected) -join '|')) {
        throw "$Context expected '$(@($Expected)-join ',')', got '$(@($Actual)-join ',')'."
    }
}
function New-SyntheticOccurrenceRule {
    param([string]$RuleId, [string]$RuleKind, [string]$EffectKind, [string]$TargetId, [string]$OccurrenceTemplate)
    return [ordered]@{
        id=$RuleId
        label="Synthetic $EffectKind extension"
        pattern_id='outer-loop-pattern'
        rule_kind=$RuleKind
        condition_logic='all'
        applicability=[ordered]@{application_level='pattern-default'
            recurrence_ids=@()
            phase_ids=@()
            branch_ids=@()
            min_iteration_ordinal=2
            max_iteration_ordinal=2
            chronology_window=$null
            effective_window=$null
        }
        priority=10
        resolution_group="synthetic-$EffectKind"
        selection_mode='accumulate'
        override_mode='inherit'
        conditions=@([ordered]@{id="$RuleId-condition"
                condition_kind='occurrence-reached'
                target_type='occurrence-template'
                target_id=$OccurrenceTemplate
                expected_value='occurred'
                subject_type=$null
                subject_id=$null
                state_kind=$null
                track_id=$null
                comparison_value=$null
            })
        effects=@([ordered]@{id="$RuleId-effect"
                effect_kind=$EffectKind
                target_type='recurrence-pattern'
                target_id=$TargetId
            })
    }
}

$repoRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$project = Get-KnowledgeProjectConfig $repoRoot
$packs = Get-KnowledgeSchemaPackRegistry $project
$resources = Get-KnowledgeResourceConfig $project
$sources = Get-KnowledgeSourceRegistry $project $resources $packs
$chronology = Get-KnowledgeChronologyRegistry $project $packs @($sources.works.Keys) @($sources.continuities.Keys)
$registry = Get-KnowledgeOccurrenceRegistry $project $packs $chronology

$fixtureRoot = Join-Path $repoRoot 'Framework\Data\Occurrence'
$chronologyFixturePath = Join-Path $repoRoot 'Framework\Data\Chronology\valid-registry.yaml'
$chronologyFixtureData = ConvertFrom-KnowledgeYamlFile $chronologyFixturePath 2 'chronology fixture'
$chronologyFixtureData['contexts'] = @(
    [ordered]@{id='recipient-context'
        label='Recipient Context'
        coordinate_system_id='civil-year'
        role='story'
        continuity_ids=@()
        work_ids=@('fixture-work')
        branch_id='main'
    },
    [ordered]@{id='agent-context'
        label='Agent Context'
        coordinate_system_id='civil-year'
        role='time-travel-origin'
        continuity_ids=@()
        work_ids=@('fixture-work')
        branch_id='main'
    }
)
$chronologyFixtureData['context_relations'] = @()
$chronologyFixture = ConvertTo-KnowledgeChronologyRegistry `
    $chronologyFixtureData `
    $chronologyFixturePath `
    $packs `
@('fixture-work') `
@()
$fixturePath = Join-Path $fixtureRoot 'valid-registry.yaml'
$subjectTargets = [ordered]@{character = @('protagonist', 'observer') }
$payloadTargets = [ordered]@{'state-record' = @('protagonist-health') }
$fixtureData = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$fixture = ConvertTo-KnowledgeOccurrenceRegistry $fixtureData $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
Assert-KnowledgeOccurrenceBranchContinuityTargets $fixture @('fixture-continuity')
$continuityRejected = $false
try {
    Assert-KnowledgeOccurrenceBranchContinuityTargets $fixture @()
}
catch {
    $continuityRejected = $true
}
if (-not $continuityRejected) {
    throw 'Unknown branch continuity membership unexpectedly validated.'
}
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json

foreach ($property in $expectations.branch_state_histories.PSObject.Properties) {
    Assert-OccurrenceIds `
    (Get-OccurrenceIds (Get-KnowledgeOccurrenceBranchStateHistory $fixture $property.Name)) `
    @($property.Value) `
        "Branch-state history '$($property.Name)'"
}
foreach ($vector in @($expectations.branch_state_at)) {
    $state = Get-KnowledgeOccurrenceBranchStateAt $fixture ([string]$vector[0]) $vector[1]
    $stateId = if ($null -eq $state) {
        $null
    }
    else {
        $state.id
    }
    if ($stateId -cne $vector[2]) {
        throw "Unexpected branch state for '$($vector[0])' at ordinal '$($vector[1])'."
    }
}
$queryRejected = $false
try {
    $null = Get-KnowledgeOccurrenceBranchStateHistory $fixture 'missing-branch'
}
catch {
    $queryRejected = $true
}
if (-not $queryRejected) {
    throw 'Unknown branch-state history query unexpectedly succeeded.'
}
$queryRejected = $false
try {
    $null = Get-KnowledgeOccurrenceBranchStateAt $fixture 'main' -1
}
catch {
    $queryRejected = $true
}
if (-not $queryRejected) {
    throw 'Negative branch-state boundary unexpectedly succeeded.'
}

foreach ($property in $expectations.iteration_occurrences.PSObject.Properties) {
    Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOccurrencesForIteration $fixture $property.Name)) @($property.Value) "Iteration '$($property.Name)'"
}
foreach ($property in $expectations.recurrence_cardinalities.PSObject.Properties) {
    Assert-OccurrenceIds `
    (Get-OccurrenceIds (Get-KnowledgeCardinalitiesForRecurrence $fixture $property.Name)) `
    @($property.Value) `
        "Cardinalities '$($property.Name)'"
}
foreach ($property in $expectations.position_occurrences.PSObject.Properties) {
    Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOccurrencesAtPosition $fixture $property.Name)) @($property.Value) "Position '$($property.Name)'"
}
foreach ($property in $expectations.occurrence_participations.PSObject.Properties) {
    Assert-OccurrenceIds `
    (Get-OccurrenceIds (Get-KnowledgeParticipationsForOccurrence $fixture $property.Name)) `
    @($property.Value) `
        "Participations '$($property.Name)'"
}
foreach ($property in $expectations.subject_participations.PSObject.Properties) {
    $parts = @($property.Name.Split('|', 2))
    Assert-OccurrenceIds `
    (Get-OccurrenceIds (Get-KnowledgeParticipationsForSubject $fixture $parts[0] $parts[1])) `
    @($property.Value) `
        "Subject participations '$($property.Name)'"
}
foreach ($property in $expectations.track_occurrence_entries.PSObject.Properties) {
    $parts = @($property.Name.Split('|', 2))
    Assert-OccurrenceIds `
    (Get-OccurrenceIds (Get-KnowledgeTrackEntriesForOccurrence $fixture $parts[0] $parts[1])) `
    @($property.Value) `
        "Track occurrence entries '$($property.Name)'"
}
foreach ($vector in @($expectations.track_entry_neighbors)) {
    $previous = Get-KnowledgePreviousTrackEntry $fixture ([string]$vector[0]) ([string]$vector[1])
    $following = Get-KnowledgeNextTrackEntry $fixture ([string]$vector[0]) ([string]$vector[1])
    if ($previous.id -cne $vector[2] -or $following.id -cne $vector[3]) {
        throw "Unexpected track-entry neighbors for '$($vector[1])'."
    }
}
foreach ($vector in @($expectations.ambiguous_occurrence_neighbors)) {
    $actualError = $null
    try {
        $null = Get-KnowledgePreviousTrackOccurrence $fixture ([string]$vector[0]) ([string]$vector[1])
    }
    catch {
        $actualError = $_.Exception.Message
    }
    if ($actualError -cne [string]$vector[2]) {
        throw "Unexpected ambiguous occurrence error for '$($vector[1])': $actualError"
    }
}
foreach ($property in $expectations.iteration_track_occurrences.PSObject.Properties) {
    $parts = @($property.Name.Split('|', 2))
    Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOccurrencesForIterationOnTrack $fixture $parts[0] $parts[1])) @($property.Value) "Iteration '$($parts[0])' on track '$($parts[1])'"
}
foreach ($vector in @($expectations.track_iteration_boundaries)) {
    $previous = Get-KnowledgePreviousBeforeIteration $fixture ([string]$vector[0]) ([string]$vector[1])
    $following = Get-KnowledgeNextAfterIteration $fixture ([string]$vector[0]) ([string]$vector[1])
    if ($previous.id -cne [string]$vector[2] -or $following.id -cne [string]$vector[3]) {
        throw "Unexpected track boundaries for '$($vector[1])' on '$($vector[0])'."
    }
}
foreach ($vector in @($expectations.track_neighbors)) {
    $previous = Get-KnowledgePreviousTrackOccurrence $fixture ([string]$vector[0]) ([string]$vector[1])
    $following = Get-KnowledgeNextTrackOccurrence $fixture ([string]$vector[0]) ([string]$vector[1])
    if ($previous.id -cne [string]$vector[2] -or $following.id -cne [string]$vector[3]) {
        throw "Unexpected track neighbors for '$($vector[1])'."
    }
}
foreach ($property in $expectations.carryovers_into.PSObject.Properties) {
    Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeCarryoversIntoIteration $fixture $property.Name)) @($property.Value) "Carryover '$($property.Name)'"
}
foreach ($property in $expectations.occurrence_recurrences.PSObject.Properties) {
    $recurrence = Get-KnowledgeOccurrenceRecurrence $fixture $property.Name
    $actual = $(if ($null -eq $recurrence) {
            $null
        }
        else {
            $recurrence.id
        })
    if ($actual -cne $property.Value) {
        throw "Unexpected recurrence for '$($property.Name)'."
    }
}
foreach ($property in $expectations.occurrence_outcomes.PSObject.Properties) {
    Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeOutcomesForOccurrence $fixture $property.Name)) @($property.Value) "Outcomes '$($property.Name)'"
}
foreach ($property in $expectations.pattern_rules.PSObject.Properties) {
    Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeRulesForRecurrencePattern $fixture $property.Name)) @($property.Value) "Rules '$($property.Name)'"
}
foreach ($property in $expectations.iteration_phases.PSObject.Properties) {
    $phase = Get-KnowledgeRecurrencePhaseForIteration $fixture $property.Name
    $actual = $(if ($null -eq $phase) {
            $null
        }
        else {
            $phase.id
        })
    if ($actual -cne $property.Value) {
        throw "Unexpected recurrence phase for '$($property.Name)'."
    }
}
foreach ($vector in @($expectations.schedule_values)) {
    if ((Get-KnowledgeRecurrenceScheduleValue $fixture ([string]$vector[0]) ([int]$vector[1])) -cne $vector[2]) {
        throw "Unexpected schedule value for '$($vector[0])' ordinal $($vector[1])."
    }
}
foreach ($vector in @($expectations.schedule_errors)) {
    $actualError = $null
    try {
        $null = Get-KnowledgeRecurrenceScheduleValue $fixture ([string]$vector[0]) ([int]$vector[1])
    }
    catch {
        $actualError = $_.Exception.Message
    }
    if ($actualError -cne [string]$vector[2]) {
        throw "Unexpected schedule error for '$($vector[0])': $actualError"
    }
}
foreach ($vector in @($expectations.schedule_matches)) {
    $effective = $vector[3]
    if ((Get-KnowledgeRecurrenceScheduleMatch $fixture ([string]$vector[0]) ([string]$vector[1]) ([string]$vector[2]) $effective) -cne [string]$vector[4]) {
        throw "Unexpected schedule match for '$($vector[0])' at '$($vector[2])'."
    }
}
foreach ($vector in @($expectations.rule_evaluations)) {
    $evaluation = Get-KnowledgeRecurrenceRuleEvaluation $fixture ([string]$vector[0]) ([string]$vector[1]) $vector[2]
    if ($evaluation.PSObject.Properties.Name -ccontains 'effects') {
        throw 'Unsafe legacy rule-evaluation effects alias remains available.'
    }
    Assert-OccurrenceIds @($evaluation.selected_rule_ids) @($vector[4]) "Selected rules at '$($vector[1])'"
    Assert-OccurrenceIds @($evaluation.proposed_effects | ForEach-Object { $_.effect_kind }) @($vector[5]) "Effects at '$($vector[1])'"
    $authorizedKinds = if ([string]$vector[3] -ceq 'selected') {
        @($vector[5])
    }
    else {
        @()
    }
    Assert-OccurrenceIds @($evaluation.authorized_effects | ForEach-Object { $_.effect_kind }) $authorizedKinds "Authorized effects at '$($vector[1])'"
    $expectedDisposition = @{
        selected='authorized'
        conflict='blocked-conflict'
        indeterminate='blocked-indeterminate'
        'no-match'='not-applicable'
    }[[string]$vector[3]]
    if ($evaluation.execution_disposition -cne $expectedDisposition) {
        throw "Unexpected execution disposition at '$($vector[1])'."
    }
    Assert-OccurrenceIds @($evaluation.conflicts) @($vector[6]) "Conflicts at '$($vector[1])'"
    if ($evaluation.status -cne [string]$vector[3]) {
        throw "Unexpected rule evaluation status at '$($vector[1])'."
    }
}
foreach ($vector in @($expectations.resolved_effects)) {
    $evaluation = Get-KnowledgeRecurrenceRuleEvaluation $fixture ([string]$vector[0]) ([string]$vector[1]) $vector[2]
    $expectedEffects = @($vector[3])
    if (@($evaluation.proposed_effects).Count -ne $expectedEffects.Count) {
        throw "Unexpected resolved effect count at '$($vector[1])'."
    }
    for ($index = 0; $index -lt $expectedEffects.Count; $index++) {
        $actual = $evaluation.proposed_effects[$index]
        $expected = $expectedEffects[$index]
        if (
            $actual.effect_kind -cne [string]$expected[0] -or
            $actual.target_type -cne [string]$expected[1] -or
            $actual.target_id -cne [string]$expected[2] -or
            $actual.repetition_policy -cne [string]$expected[3] -or
            [int]$actual.contribution_count -ne [int]$expected[4] -or
            [int]$actual.proposed_execution_count -ne [int]$expected[5]
        ) {
            throw "Unexpected resolved effect at '$($vector[1])' index $index."
        }
        Assert-OccurrenceIds @($actual.contributing_rule_ids) @($expected[6]) "Resolved effect rule contributors at '$($vector[1])'"
        Assert-OccurrenceIds @($actual.contributing_effect_ids) @($expected[7]) "Resolved effect row contributors at '$($vector[1])'"
    }
}
foreach ($vector in @($expectations.trace_dispositions)) {
    $evaluation = Get-KnowledgeRecurrenceRuleEvaluation $fixture ([string]$vector[0]) ([string]$vector[1]) $vector[2]
    $trace = @($evaluation.traces | Where-Object { $_.rule_id -ceq [string]$vector[3] })[0]
    if ($trace.disposition -cne [string]$vector[4]) {
        throw "Unexpected trace disposition for rule '$($vector[3])'."
    }
}
foreach ($property in $expectations.subject_state_transitions.PSObject.Properties) {
    $parts = @($property.Name.Split('|', 2))
    Assert-OccurrenceIds (Get-OccurrenceIds (Get-KnowledgeStateTransitionsForSubject $fixture $parts[0] $parts[1])) @($property.Value) "States '$($property.Name)'"
}
foreach ($vector in @($expectations.state_at)) {
    $state = Get-KnowledgeStateAt $fixture ([string]$vector[0]) ([string]$vector[1]) ([string]$vector[2]) ([string]$vector[3]) ([string]$vector[4])
    $actual = $(if ($null -eq $state) {
            $null
        }
        else {
            $state.id
        })
    if ($actual -cne $vector[5]) {
        throw "Unexpected state at '$($vector[1])' on '$($vector[0])'."
    }
}

$invalidCases = Get-Content -LiteralPath (Join-Path $fixtureRoot 'invalid-cases.json') -Raw | ConvertFrom-Json
foreach ($case in @($invalidCases)) {
    $invalid = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'invalid occurrence fixture'
    foreach ($change in @($case.changes)) {
        Set-OccurrenceFixturePath $invalid ([string]$change.path) $change.value
    }
    $rejected = $false
    try {
        $null = ConvertTo-KnowledgeOccurrenceRegistry $invalid $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw "Malformed occurrence case unexpectedly loaded: $($case.name)"
    }
}

$scaleCount = 128
$scaleProbe = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$scaleProbe['tracks']['scale-observer-experience'] = [ordered]@{
    label = 'Scale Observer Experience'
    kind = 'observation'
    subject_type = 'character'
    subject_id = 'observer'
}
for ($index = 0; $index -lt $scaleCount; $index++) {
    $cardinalityId = 'scale-cardinality-{0:d3}' -f $index
    $scaleProbe['recurrence_cardinalities'][$cardinalityId] = [ordered]@{
        label = 'Scale cardinality {0:d3}' -f $index
        recurrence_id = 'inner-loop'
        cardinality_kind = 'minimum'
        minimum_count = 1000 + $index
        maximum_count = $null
        coverage_mode = 'unmaterialized'
        representative_iteration_ids = @()
        certainty = 'uncertain'
    }
    $occurrenceId = 'scale-occurrence-{0:d3}' -f $index
    $participationId = 'scale-participation-{0:d3}' -f $index
    $entryId = 'scale-entry-{0:d3}' -f $index
    $scaleProbe['occurrences'][$occurrenceId] = [ordered]@{
        template_id = 'intervention'
        label = 'Scale occurrence {0:d3}' -f $index
        iteration_id = $null
        branch_id = 'main'
        bindings = @()
    }
    $scaleProbe['occurrence_participations'][$participationId] = [ordered]@{
        occurrence_id = $occurrenceId
        subject_type = 'character'
        subject_id = 'observer'
        role = 'reviewer'
        perspective = 'reconstructed'
        status = 'completed'
        chronology_context_id = $null
    }
    $scaleProbe['track_entries'][$entryId] = [ordered]@{
        track_id = 'scale-observer-experience'
        participation_id = $participationId
        ordinal = $index + 1
    }
    $scaleProbe['branch_state_transitions'] = @($scaleProbe['branch_state_transitions']) + @(
        [ordered]@{
            id = 'scale-branch-state-{0:d3}' -f $index
            label = 'Scale branch state {0:d3}' -f $index
            branch_id = 'main'
            ordinal = $index + 3
            change_kind = 'preserve'
            prior_state = 'preserved'
            resulting_state = 'preserved'
            activation_occurrence_id = 'restored-main'
            trigger_transition_id = $null
            certainty = 'exact'
        }
    )
}
$scaleRegistry = ConvertTo-KnowledgeOccurrenceRegistry `
    $scaleProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
if (@(Get-KnowledgeCardinalitiesForRecurrence $scaleRegistry 'inner-loop').Count -ne (5 + $scaleCount)) {
    throw 'Generated recurrence-cardinality scale probe did not retain every record.'
}
if (
    @(Get-KnowledgeParticipationsForSubject $scaleRegistry 'character' 'observer').Count -ne (7 + $scaleCount) -or
    @($scaleRegistry.tracks['scale-observer-experience'].entry_ids).Count -ne $scaleCount
) {
    throw 'Generated occurrence-participation scale probe did not retain every record.'
}
if (@(Get-KnowledgeOccurrenceBranchStateHistory $scaleRegistry 'main').Count -ne (2 + $scaleCount)) {
    throw 'Generated branch-state scale probe did not retain every record.'
}

$mixedIndeterminateProbe = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$mixedRuleSource = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$mixedRule = $mixedRuleSource['rules'][0]
$mixedRule['id'] = 'indeterminate-reset-rule'
$mixedRule['label'] = 'Indeterminate reset policy'
$mixedRule['resolution_group'] = 'indeterminate-control'
$mixedRule['applicability']['effective_window'] = $mixedIndeterminateProbe['rules'][3]['applicability']['effective_window']
$mixedRule['conditions'][0]['id'] = 'indeterminate-reset-reached'
$mixedRule['conditions'][1]['id'] = 'indeterminate-reset-ordinal'
$mixedRule['effects'][0]['id'] = 'indeterminate-reset-advances'
$mixedIndeterminateProbe['rules'] = @($mixedIndeterminateProbe['rules']) + @($mixedRule)
$mixedIndeterminateRegistry = ConvertTo-KnowledgeOccurrenceRegistry `
    $mixedIndeterminateProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
$mixedIndeterminateEvaluation = Get-KnowledgeRecurrenceRuleEvaluation `
    $mixedIndeterminateRegistry 'outer-loop' 'reset-one'
if (
    $mixedIndeterminateEvaluation.status -cne 'indeterminate' -or
    $mixedIndeterminateEvaluation.execution_disposition -cne 'blocked-indeterminate' -or
    @($mixedIndeterminateEvaluation.authorized_effects).Count -ne 0
) {
    throw 'Mixed selected/indeterminate evaluation did not fail closed.'
}
Assert-OccurrenceIds @($mixedIndeterminateEvaluation.selected_rule_ids) @('outer-reset-rule') 'Mixed indeterminate selected rules'
Assert-OccurrenceIds @($mixedIndeterminateEvaluation.proposed_effects | ForEach-Object { $_.effect_kind }) @('advance-iteration') 'Mixed indeterminate proposed effects'

$extensionValues = [ordered]@{
    'occurrence.rule-kind'=@('pause', 'signal')
    'occurrence.rule-effect-kind'=@('pause-recurrence', 'signal-recurrence')
}
foreach ($namespace in $extensionValues.Keys) {
    $packs.controlled_values[$namespace] = @($packs.controlled_values[$namespace]) + @($extensionValues[$namespace])
}
$packs.effect_target_compatibilities['pause-recurrence|recurrence-pattern'] = $true
$packs.effect_target_compatibilities['signal-recurrence|recurrence-pattern'] = $true
$packs.rule_effect_compatibilities['pause|pause-recurrence'] = $true
$packs.rule_effect_compatibilities['signal|signal-recurrence'] = $true
$packs.effect_policies['pause-recurrence'] = [pscustomobject]@{
    effect_kind='pause-recurrence'
    repetition_policy='idempotent'
    recurrence_pattern_scope='owning-pattern'
}
$packs.effect_policies['signal-recurrence'] = [pscustomobject]@{
    effect_kind='signal-recurrence'
    repetition_policy='idempotent'
    recurrence_pattern_scope='external-pattern'
}
$packs.effect_incompatibilities['advance-iteration|pause-recurrence'] = 'same-target'

$owningProbe = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$owningProbe['rules'] = @($owningProbe['rules']) + @(New-SyntheticOccurrenceRule 'synthetic-pause-rule' 'pause' 'pause-recurrence' 'outer-loop-pattern' 'reset')
$owningRegistry = ConvertTo-KnowledgeOccurrenceRegistry $owningProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
$owningEvaluation = Get-KnowledgeRecurrenceRuleEvaluation $owningRegistry 'outer-loop' 'reset-two'
if ($owningEvaluation.status -cne 'conflict') {
    throw 'Owning-pattern extension did not produce a conflict.'
}
Assert-OccurrenceIds @($owningEvaluation.selected_rule_ids) @('outer-reset-rule', 'synthetic-pause-rule') 'Owning-pattern extension selected rules'
Assert-OccurrenceIds @($owningEvaluation.conflicts) @('advance-iteration conflicts with pause-recurrence on recurrence-pattern:outer-loop-pattern') 'Owning-pattern extension conflicts'

$foreignOwningProbe = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$foreignOwningRule = New-SyntheticOccurrenceRule 'synthetic-pause-rule' 'pause' 'pause-recurrence' 'inner-loop-pattern' 'reset'
$foreignOwningProbe['rules'] = @($foreignOwningProbe['rules']) + @($foreignOwningRule)
$foreignRejected = $false
try {
    $null = ConvertTo-KnowledgeOccurrenceRegistry $foreignOwningProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
}
catch {
    $foreignRejected = $true
}
if (-not $foreignRejected) {
    throw 'Owning-pattern extension unexpectedly accepted a foreign pattern target.'
}

$externalProbe = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$externalProbe['rules'] = @($externalProbe['rules']) + @(New-SyntheticOccurrenceRule 'synthetic-signal-rule' 'signal' 'signal-recurrence' 'inner-loop-pattern' 'bell')
$externalRegistry = ConvertTo-KnowledgeOccurrenceRegistry $externalProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
$externalEvaluation = Get-KnowledgeRecurrenceRuleEvaluation $externalRegistry 'outer-loop' 'bell-two'
if ($externalEvaluation.status -cne 'selected') {
    throw 'External-pattern extension was not selected.'
}
Assert-OccurrenceIds @($externalEvaluation.selected_rule_ids) @('synthetic-signal-rule') 'External-pattern extension selected rules'
Assert-OccurrenceIds @($externalEvaluation.authorized_effects | ForEach-Object { $_.target_id }) @('inner-loop-pattern') 'External-pattern extension targets'

$duplicateProbe = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$firstSignal = New-SyntheticOccurrenceRule 'first-signal-rule' 'signal' 'signal-recurrence' 'inner-loop-pattern' 'bell'
$secondSignal = New-SyntheticOccurrenceRule 'second-signal-rule' 'signal' 'signal-recurrence' 'inner-loop-pattern' 'bell'
$firstSignal['resolution_group'] = 'first-signal-group'
$secondSignal['resolution_group'] = 'second-signal-group'
$duplicateProbe['rules'] = @($duplicateProbe['rules']) + @($firstSignal, $secondSignal)
$duplicateRegistry = ConvertTo-KnowledgeOccurrenceRegistry `
    $duplicateProbe $fixturePath $packs $chronologyFixture $subjectTargets $payloadTargets
$duplicateEvaluation = Get-KnowledgeRecurrenceRuleEvaluation `
    $duplicateRegistry 'outer-loop' 'bell-two'
if (
    @($duplicateEvaluation.authorized_effects).Count -ne 1 -or
    $duplicateEvaluation.authorized_effects[0].contribution_count -ne 2 -or
    $duplicateEvaluation.authorized_effects[0].proposed_execution_count -ne 1
) {
    throw 'Unexpected idempotent effect resolution.'
}
Assert-OccurrenceIds @($duplicateEvaluation.authorized_effects[0].contributing_rule_ids) @('first-signal-rule', 'second-signal-rule') 'Idempotent effect contributors'
foreach ($policyCase in @([pscustomobject]@{policy='accumulating'
            status='selected'
            execution_count=2
            conflicts=@()
        }, [pscustomobject]@{policy='invalid'
            status='conflict'
            execution_count=0
            conflicts=@('duplicate signal-recurrence effect on recurrence-pattern:inner-loop-pattern is invalid')
        })) {
    $policyPacks = $packs.PSObject.Copy()
    $policyPacks.effect_policies = @{} + $packs.effect_policies
    $policyPacks.effect_policies['signal-recurrence'] = [pscustomobject]@{
        effect_kind='signal-recurrence'
        repetition_policy=$policyCase.policy
        recurrence_pattern_scope='external-pattern'
    }
    $policyRegistry = ConvertTo-KnowledgeOccurrenceRegistry `
        $duplicateProbe $fixturePath $policyPacks $chronologyFixture $subjectTargets $payloadTargets
    $policyEvaluation = Get-KnowledgeRecurrenceRuleEvaluation `
        $policyRegistry 'outer-loop' 'bell-two'
    if (
        $policyEvaluation.status -cne $policyCase.status -or
        $policyEvaluation.proposed_effects[0].proposed_execution_count -ne $policyCase.execution_count -or
        (@($policyEvaluation.authorized_effects).Count -gt 0) -ne ($policyCase.status -ceq 'selected')
    ) {
        throw "Unexpected '$($policyCase.policy)' effect resolution."
    }
    Assert-OccurrenceIds @($policyEvaluation.conflicts) @($policyCase.conflicts) "$($policyCase.policy) effect conflicts"
}

$scopedPacks = $packs.PSObject.Copy()
$scopedPacks.effect_policies = @{} + $packs.effect_policies
$scopedPacks.effect_policies['pause-recurrence'] = [pscustomobject]@{
    effect_kind='pause-recurrence'
    repetition_policy='idempotent'
    recurrence_pattern_scope='external-pattern'
}
$scopedProbe = ConvertFrom-KnowledgeYamlFile $fixturePath 7 'occurrence fixture'
$scopedProbe['rules'] = @($scopedProbe['rules']) + @(New-SyntheticOccurrenceRule 'cross-target-pause-rule' 'pause' 'pause-recurrence' 'inner-loop-pattern' 'reset')
$scopedRegistry = ConvertTo-KnowledgeOccurrenceRegistry `
    $scopedProbe $fixturePath $scopedPacks $chronologyFixture $subjectTargets $payloadTargets
$scopedEvaluation = Get-KnowledgeRecurrenceRuleEvaluation `
    $scopedRegistry 'outer-loop' 'reset-two'
if ($scopedEvaluation.status -cne 'selected' -or @($scopedEvaluation.conflicts).Count -ne 0) {
    throw 'Cross-target same-target pair unexpectedly conflicted.'
}

$globalPacks = $packs.PSObject.Copy()
$globalPacks.effect_policies = $scopedPacks.effect_policies
$globalPacks.effect_incompatibilities = @{} + $scopedPacks.effect_incompatibilities
$globalPacks.effect_incompatibilities['advance-iteration|pause-recurrence'] = 'global'
$globalRegistry = ConvertTo-KnowledgeOccurrenceRegistry `
    $scopedProbe $fixturePath $globalPacks $chronologyFixture $subjectTargets $payloadTargets
$globalEvaluation = Get-KnowledgeRecurrenceRuleEvaluation `
    $globalRegistry 'outer-loop' 'reset-two'
Assert-OccurrenceIds @($globalEvaluation.conflicts) @('advance-iteration conflicts with pause-recurrence globally') 'Global effect incompatibility'
if (
    $globalEvaluation.execution_disposition -cne 'blocked-conflict' -or
    @($globalEvaluation.authorized_effects).Count -ne 0 -or
    @($globalEvaluation.proposed_effects).Count -ne 2
) {
    throw 'Global conflict did not block the complete execution plan.'
}

$summary = [ordered]@{
    branch_state_transitions=[int]@($registry.branch_state_transitions).Count
    branches=[int]$registry.branches.Count
    carryovers=[int]@($registry.carryovers).Count
    causal_relations=[int]@($registry.causal_relations).Count
    fixture_queries=97
    invalid_cases=[int]@($invalidCases).Count
    iterations=[int]$registry.iterations.Count
    recurrence_cardinalities=[int]$registry.recurrence_cardinalities.Count
    scale_cardinalities=$scaleCount
    scale_participations=$scaleCount
    scale_branch_state_transitions=$scaleCount
    phases=[int]$registry.phases.Count
    schedules=[int]$registry.schedules.Count
    occurrences=[int]$registry.occurrences.Count
    occurrence_participations=[int]$registry.occurrence_participations.Count
    outcomes=[int]@($registry.outcomes).Count
    recurrence_patterns=[int]$registry.recurrence_patterns.Count
    recurrences=[int]$registry.recurrences.Count
    rules=[int]@($registry.rules).Count
    schema_version=[int]$registry.schema_version
    templates=[int]$registry.templates.Count
    state_transitions=[int]@($registry.state_transitions).Count
    tracks=[int]$registry.tracks.Count
    track_entries=[int]$registry.track_entries.Count
    transitions=[int]@($registry.transitions).Count
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        (
            'Occurrence validation passed: schema {0}, {1} project branch, ' +
            '{2} fixture queries, and {3} malformed cases.'
        ) -f
        $summary.schema_version,
        $summary.branches,
        $summary.fixture_queries,
        $summary.invalid_cases
    )
}
