$script:SupportedOccurrenceSchemaVersion = 6
$script:OccurrenceStableIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'

function Get-RequiredOccurrenceString {
    param([object]$Map, [string]$Key, [string]$Context)
    $value = Get-ProjectMapValue $Map $Key
    if ($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)) {
        throw "$Context.$Key must be a non-empty string."
    }
    return $value.Trim()
}
function Get-OptionalOccurrenceString {
    param([object]$Map, [string]$Key, [string]$Context)
    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        return $null
    }
    if ($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)) {
        throw "$Context.$Key must be a non-empty string or null."
    }
    return $value.Trim()
}
function Get-OccurrenceStringList {
    param([object]$Map, [string]$Key, [string]$Context)
    $value = $Map[$Key]
    if ($null -eq $value) {
        throw "$Context.$Key must be a list."
    }
    if ($value -is [string] -or $value -isnot [System.Collections.IList]) {
        throw "$Context.$Key must be a list."
    }
    $result = @()
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($entry in @($value)) {
        if ($entry -isnot [string] -or [string]::IsNullOrWhiteSpace($entry) -or -not $seen.Add($entry.Trim())) {
            throw "$Context.$Key must contain unique non-empty strings."
        }
        $result += $entry.Trim()
    }
    return @($result)
}
function Assert-OccurrenceStableId {
    param([string]$Value, [string]$Context)
    if ($Value -cnotmatch $script:OccurrenceStableIdPattern) {
        throw "$Context must be a lowercase kebab-case stable ID: $Value"
    }
    return $Value
}
function Assert-OccurrencePackValue {
    param([object]$Packs, [string]$Namespace, [string]$Value, [string]$Context)
    if (@(Get-SchemaPackAllowedValues $Packs $Namespace) -cnotcontains $Value) {
        throw "$Context uses '$Value', which is not provided in '$Namespace'."
    }
}
function Assert-OccurrenceMap {
    param([object]$Value, [string]$Context)
    if ($Value -isnot [System.Collections.IDictionary]) {
        throw "$Context must be a mapping."
    }
}
function Assert-OccurrenceList {
    param([object]$Value, [string]$Context)
    if ($Value -is [string] -or $Value -isnot [System.Collections.IList]) {
        throw "$Context must be a list."
    }
}
function Get-OptionalOccurrenceNonnegativeInteger {
    param([object]$Map, [string]$Key, [string]$Context)
    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        return $null
    }
    if ($value -isnot [int] -or $value -lt 0) {
        throw "$Context.$Key must be a nonnegative integer or null."
    }
    return [int]$value
}
function Get-RequiredOccurrencePositiveInteger {
    param([object]$Map, [string]$Key, [string]$Context)
    $value = Get-ProjectMapValue $Map $Key
    if ($value -isnot [int] -or $value -lt 1) {
        throw "$Context.$Key must be a positive integer."
    }
    return [int]$value
}

function Assert-OccurrenceParentAcyclic {
    param([System.Collections.IDictionary]$Items, [string]$ParentProperty, [string]$Kind)
    foreach ($itemId in @($Items.Keys)) {
        $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $current = [string]$itemId
        while ($null -ne $current) {
            if (-not $seen.Add($current)) {
                throw "$Kind parent cycle includes '$current'."
            }
            $current = $Items[$current].$ParentProperty
        }
    }
}

function Get-KnowledgeOccurrencesForIteration {
    param([object]$Registry, [string]$IterationId)
    if (-not $Registry.iterations.Contains($IterationId)) {
        throw "Unknown iteration '$IterationId'."
    }
    return @($Registry.occurrences.Values | Where-Object { $_.iteration_id -ceq $IterationId })
}
function Get-OptionalOccurrenceNonnegativeCount {
    param([object]$Map, [string]$Key, [string]$Context)
    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        return $null
    }
    if (($value -isnot [int] -and $value -isnot [long]) -or $value -lt 0) {
        throw "$Context.$Key must be a nonnegative signed 64-bit integer or null."
    }
    return [long]$value
}
function Get-KnowledgeCardinalitiesForRecurrence {
    param([object]$Registry, [string]$RecurrenceId)
    if (-not $Registry.recurrences.Contains($RecurrenceId)) {
        throw "Unknown recurrence '$RecurrenceId'."
    }
    return @(
        $Registry.recurrence_cardinalities.Values |
            Where-Object { $_.recurrence_id -ceq $RecurrenceId } |
            Sort-Object id
    )
}
function Get-KnowledgeOccurrencesAtPosition {
    param([object]$Registry, [string]$PositionId)
    return @($Registry.occurrences.Values | Where-Object { @($_.bindings | Where-Object { $_.position_id -ceq $PositionId }).Count -gt 0 })
}
function Get-KnowledgeParticipationsForOccurrence {
    param([object]$Registry, [string]$OccurrenceId)
    if (-not $Registry.occurrences.Contains($OccurrenceId)) {
        throw "Unknown occurrence '$OccurrenceId'."
    }
    return @($Registry.occurrence_participations.Values | Where-Object { $_.occurrence_id -ceq $OccurrenceId })
}
function Get-KnowledgeParticipationsForSubject {
    param([object]$Registry, [string]$SubjectType, [string]$SubjectId)
    return @(
        $Registry.occurrence_participations.Values |
            Where-Object { $_.subject_type -ceq $SubjectType -and $_.subject_id -ceq $SubjectId }
    )
}
function Get-KnowledgeTrackEntriesForOccurrence {
    param([object]$Registry, [string]$TrackId, [string]$OccurrenceId)
    if (-not $Registry.tracks.Contains($TrackId)) {
        throw "Unknown track '$TrackId'."
    }
    if (-not $Registry.occurrences.Contains($OccurrenceId)) {
        throw "Unknown occurrence '$OccurrenceId'."
    }
    return @(
        $Registry.tracks[$TrackId].entry_ids |
            ForEach-Object { $Registry.track_entries[$_] } |
            Where-Object {
                $Registry.occurrence_participations[$_.participation_id].occurrence_id -ceq $OccurrenceId
            }
    )
}
function Get-KnowledgeAdjacentTrackEntry {
    param([object]$Registry, [string]$TrackId, [string]$EntryId, [int]$Offset)
    if (-not $Registry.tracks.Contains($TrackId)) {
        throw "Unknown track '$TrackId'."
    }
    if (-not $Registry.track_entries.Contains($EntryId)) {
        throw "Unknown track entry '$EntryId'."
    }
    if ($Registry.track_entries[$EntryId].track_id -cne $TrackId) {
        throw "Track entry '$EntryId' does not belong to track '$TrackId'."
    }
    $ids = @($Registry.tracks[$TrackId].entry_ids)
    $target = [Array]::IndexOf($ids, $EntryId) + $Offset
    if ($target -lt 0 -or $target -ge $ids.Count) {
        return $null
    }
    return $Registry.track_entries[$ids[$target]]
}
function Get-KnowledgePreviousTrackEntry {
    param([object]$Registry, [string]$TrackId, [string]$EntryId)
    return Get-KnowledgeAdjacentTrackEntry $Registry $TrackId $EntryId -1
}
function Get-KnowledgeNextTrackEntry {
    param([object]$Registry, [string]$TrackId, [string]$EntryId)
    return Get-KnowledgeAdjacentTrackEntry $Registry $TrackId $EntryId 1
}
function Get-KnowledgeOccurrencesForIterationOnTrack {
    param([object]$Registry, [string]$IterationId, [string]$TrackId)
    if (-not $Registry.iterations.Contains($IterationId)) {
        throw "Unknown iteration '$IterationId'."
    }
    if (-not $Registry.tracks.Contains($TrackId)) {
        throw "Unknown track '$TrackId'."
    }
    return @($Registry.tracks[$TrackId].occurrence_ids | ForEach-Object { $Registry.occurrences[$_] } | Where-Object { $_.iteration_id -ceq $IterationId })
}
function Get-KnowledgeAdjacentTrackOccurrence {
    param([object]$Registry, [string]$TrackId, [string]$OccurrenceId, [int]$Offset)
    if (-not $Registry.tracks.Contains($TrackId)) {
        throw "Unknown track '$TrackId'."
    }
    $ids = @($Registry.tracks[$TrackId].occurrence_ids)
    $matches = @($ids | Where-Object { $_ -ceq $OccurrenceId })
    if ($matches.Count -eq 0) {
        throw "Occurrence '$OccurrenceId' is not on track '$TrackId'."
    }
    if ($matches.Count -gt 1) {
        throw "Occurrence ``$OccurrenceId`` appears more than once on track ``$TrackId``; use track-entry navigation."
    }
    $index = [Array]::IndexOf($ids, $OccurrenceId)
    $target = $index + $Offset
    if ($target -lt 0 -or $target -ge $ids.Count) {
        return $null
    }
    return $Registry.occurrences[$ids[$target]]
}
function Get-KnowledgePreviousTrackOccurrence {
    param([object]$Registry, [string]$TrackId, [string]$OccurrenceId)
    return Get-KnowledgeAdjacentTrackOccurrence $Registry $TrackId $OccurrenceId -1
}
function Get-KnowledgeNextTrackOccurrence {
    param([object]$Registry, [string]$TrackId, [string]$OccurrenceId)
    return Get-KnowledgeAdjacentTrackOccurrence $Registry $TrackId $OccurrenceId 1
}
function Get-KnowledgePreviousBeforeIteration {
    param([object]$Registry, [string]$TrackId, [string]$IterationId)
    $items = @(Get-KnowledgeOccurrencesForIterationOnTrack $Registry $IterationId $TrackId)
    if ($items.Count -eq 0) {
        return $null
    }
    return Get-KnowledgePreviousTrackOccurrence $Registry $TrackId $items[0].id
}
function Get-KnowledgeNextAfterIteration {
    param([object]$Registry, [string]$TrackId, [string]$IterationId)
    $items = @(Get-KnowledgeOccurrencesForIterationOnTrack $Registry $IterationId $TrackId)
    if ($items.Count -eq 0) {
        return $null
    }
    return Get-KnowledgeNextTrackOccurrence $Registry $TrackId $items[-1].id
}
function Get-KnowledgeCarryoversIntoIteration {
    param([object]$Registry, [string]$IterationId)
    if (-not $Registry.iterations.Contains($IterationId)) {
        throw "Unknown iteration '$IterationId'."
    }
    return @($Registry.carryovers | Where-Object { $_.target_iteration_id -ceq $IterationId })
}
function Get-KnowledgeOutcomesForOccurrence {
    param([object]$Registry, [string]$OccurrenceId)
    if (-not $Registry.occurrences.Contains($OccurrenceId)) {
        throw "Unknown occurrence '$OccurrenceId'."
    }
    return @($Registry.outcomes | Where-Object { $_.occurrence_id -ceq $OccurrenceId })
}
function Get-KnowledgeRulesForRecurrencePattern {
    param([object]$Registry, [string]$PatternId)
    if (-not $Registry.recurrence_patterns.Contains($PatternId)) {
        throw "Unknown recurrence pattern '$PatternId'."
    }
    return @($Registry.rules | Where-Object { $_.pattern_id -ceq $PatternId })
}
function Get-KnowledgeStateTransitionsForSubject {
    param([object]$Registry, [string]$SubjectType, [string]$SubjectId)
    return @($Registry.state_transitions | Where-Object { $_.subject_type -ceq $SubjectType -and $_.subject_id -ceq $SubjectId })
}
function Get-KnowledgeStateAt {
    param([object]$Registry, [string]$TrackId, [string]$OccurrenceId, [string]$PayloadTargetType, [string]$PayloadTargetId, [string]$StateKind)
    if (-not $Registry.tracks.Contains($TrackId)) {
        throw "Unknown track '$TrackId'."
    }
    $ids = @($Registry.tracks[$TrackId].occurrence_ids)
    $boundary = [Array]::IndexOf($ids, $OccurrenceId)
    if ($boundary -lt 0) {
        throw "Occurrence '$OccurrenceId' is not on track '$TrackId'."
    }
    if (@($ids | Where-Object { $_ -ceq $OccurrenceId }).Count -gt 1) {
        throw "Occurrence ``$OccurrenceId`` appears more than once on track ``$TrackId``; a participation-relative state query is required."
    }
    $candidates = @(
        $Registry.state_transitions |
            Where-Object {
                $_.track_ids -ccontains $TrackId -and
                $_.payload_target_type -ceq $PayloadTargetType -and
                $_.payload_target_id -ceq $PayloadTargetId -and
                $_.state_kind -ceq $StateKind -and
                [Array]::IndexOf($ids, $_.activation_occurrence_id) -le $boundary
            } |
            Sort-Object { [Array]::IndexOf($ids, $_.activation_occurrence_id) }
    )
    if ($candidates.Count -eq 0) {
        return $null
    }
    return $candidates[-1]
}
function Get-KnowledgeOccurrenceRecurrence {
    param([object]$Registry, [string]$OccurrenceId)
    if (-not $Registry.occurrences.Contains($OccurrenceId)) {
        throw "Unknown occurrence '$OccurrenceId'."
    }
    $iterationId = $Registry.occurrences[$OccurrenceId].iteration_id
    if ($null -eq $iterationId) {
        return $null
    }
    return $Registry.recurrences[$Registry.iterations[$iterationId].recurrence_id]
}
function Get-KnowledgeRecurrencePhaseForIteration {
    param([object]$Registry, [string]$IterationId)
    if (-not $Registry.iterations.Contains($IterationId)) {
        throw "Unknown iteration '$IterationId'."
    }
    $iteration = $Registry.iterations[$IterationId]
    $matches = @(
        $Registry.phases.Values | Where-Object {
            $_.recurrence_id -ceq $iteration.recurrence_id -and
            $_.start_ordinal -le $iteration.ordinal -and
            ($null -eq $_.end_ordinal -or $iteration.ordinal -le $_.end_ordinal)
        }
    )
    if ($matches.Count -eq 0) {
        return $null
    }
    return $matches[0]
}
function Get-KnowledgeRecurrenceScheduleValue {
    param([object]$Registry, [string]$ScheduleId, [int]$IterationOrdinal)
    if (-not $Registry.schedules.Contains($ScheduleId)) {
        throw "Unknown recurrence schedule '$ScheduleId'."
    }
    if ($IterationOrdinal -lt 1) {
        throw 'Schedule iteration ordinal must be positive.'
    }
    $schedule = $Registry.schedules[$ScheduleId]
    $offset = ($IterationOrdinal - 1) * $schedule.interval
    if ($schedule.schedule_kind -ceq 'chronology-step') {
        $anchor = $Registry.chronology.positions[$schedule.anchor_position_id]
        $system = $Registry.chronology.coordinate_systems[$anchor.coordinate_system_id]
        return [int]$(if ($system.direction -ceq 'ascending') {
                $anchor.value + $offset
            }
            else {
                $anchor.value - $offset
            })
    }
    $boundaryError = 'Schedule projection exceeds supported civil range 0001-9999.'
    if ($schedule.unit -ceq 'year') {
        $targetYear = [int]$schedule.anchor_value + $offset
        if ($targetYear -lt 1 -or $targetYear -gt 9999) {
            throw $boundaryError
        }
        return $targetYear.ToString('0000', [Globalization.CultureInfo]::InvariantCulture)
    }
    if ($schedule.unit -ceq 'month') {
        $parts = @($schedule.anchor_value.Split('-'))
        $absolute = ([int]$parts[0] * 12) + [int]$parts[1] - 1 + $offset
        $targetYear = [math]::Floor($absolute / 12)
        if ($targetYear -lt 1 -or $targetYear -gt 9999) {
            throw $boundaryError
        }
        $targetMonth = ($absolute % 12) + 1
        return "$($targetYear.ToString('0000',[Globalization.CultureInfo]::InvariantCulture))-$($targetMonth.ToString('00',[Globalization.CultureInfo]::InvariantCulture))"
    }
    try {
        $days = $offset * $(if ($schedule.unit -ceq 'week') {
                7
            }
            else {
                1
            })
        return ([datetime]::ParseExact($schedule.anchor_value, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture).AddDays($days)).ToString('yyyy-MM-dd')
    }
    catch [System.ArgumentOutOfRangeException] {
        throw $boundaryError
    }
}
function Get-KnowledgeRecurrenceScheduleMatch {
    param([object]$Registry, [string]$ScheduleId, [string]$IterationId, [string]$OccurrenceId, [object]$EffectiveAt = $null)
    if (-not $Registry.schedules.Contains($ScheduleId)) {
        throw "Unknown recurrence schedule '$ScheduleId'."
    }
    if (-not $Registry.iterations.Contains($IterationId)) {
        throw "Unknown iteration '$IterationId'."
    }
    if (-not $Registry.occurrences.Contains($OccurrenceId)) {
        throw "Unknown occurrence '$OccurrenceId'."
    }
    $schedule = $Registry.schedules[$ScheduleId]
    $iteration = $Registry.iterations[$IterationId]
    if ($Registry.recurrences[$iteration.recurrence_id].pattern_id -cne $schedule.pattern_id) {
        throw "Schedule '$ScheduleId' does not apply to iteration '$IterationId'."
    }
    $expected = Get-KnowledgeRecurrenceScheduleValue $Registry $ScheduleId $iteration.ordinal
    if ($schedule.schedule_kind -ceq 'civil-calendar') {
        if ($null -eq $EffectiveAt) {
            return 'indeterminate'
        }
        $query = ConvertTo-KnowledgeTemporalInstant $EffectiveAt
        return $(if ($query.label -ceq $expected) {
                'due'
            }
            else {
                'off-schedule'
            })
    }
    $anchor = $Registry.chronology.positions[$schedule.anchor_position_id]
    $candidates = @(
        $Registry.occurrences[$OccurrenceId].bindings |
            Where-Object { $_.role -ceq 'primary' } |
            ForEach-Object { $Registry.chronology.positions[$_.position_id] } |
            Where-Object { $_.coordinate_system_id -ceq $anchor.coordinate_system_id }
    )
    if ($candidates.Count -eq 0) {
        return 'indeterminate'
    }
    return $(if (@($candidates | Where-Object { $_.value -eq $expected -and $_.era_id -ceq $anchor.era_id }).Count -gt 0) {
            'due'
        }
        else {
            'off-schedule'
        })
}

function Get-KnowledgeRuleApplicabilityStatus {
    param([object]$Registry, [object]$Rule, [object]$Recurrence, [object]$Iteration, [object]$Occurrence, [object]$EffectiveAt)
    $app = $Rule.applicability
    if (@($app.recurrence_ids).Count -gt 0 -and @($app.recurrence_ids) -cnotcontains $Recurrence.id) {
        return [pscustomobject]@{status='not-applicable'
            detail='recurrence excluded'
        }
    }
    $phase = Get-KnowledgeRecurrencePhaseForIteration $Registry $Iteration.id
    if (@($app.phase_ids).Count -gt 0 -and ($null -eq $phase -or @($app.phase_ids) -cnotcontains $phase.id)) {
        return [pscustomobject]@{status='not-applicable'
            detail='phase excluded'
        }
    }
    if (@($app.branch_ids).Count -gt 0 -and @($app.branch_ids) -cnotcontains $Occurrence.branch_id) {
        return [pscustomobject]@{status='not-applicable'
            detail='branch excluded'
        }
    }
    if ($null -ne $app.min_iteration_ordinal -and $Iteration.ordinal -lt $app.min_iteration_ordinal) {
        return [pscustomobject]@{status='not-applicable'
            detail='iteration below minimum'
        }
    }
    if ($null -ne $app.max_iteration_ordinal -and $Iteration.ordinal -gt $app.max_iteration_ordinal) {
        return [pscustomobject]@{status='not-applicable'
            detail='iteration above maximum'
        }
    }
    if ($null -ne $app.chronology_window) {
        $primary = @($Occurrence.bindings | Where-Object { $_.role -ceq 'primary' } | ForEach-Object { $_.position_id })
        if ($primary.Count -eq 0) {
            return [pscustomobject]@{status='indeterminate'
                detail='occurrence has no primary chronology binding'
            }
        }
        $comparable = $false
        $inside = $false
        foreach ($positionId in $primary) {
            $startRelation = if ($null -eq $app.chronology_window.start_position_id) {
                'before'
            }
            else {
                Get-KnowledgeChronologyComparison $Registry.chronology $app.chronology_window.start_position_id $positionId
            }
            $endRelation = if ($null -eq $app.chronology_window.end_position_id) {
                'before'
            }
            else {
                Get-KnowledgeChronologyComparison $Registry.chronology $positionId $app.chronology_window.end_position_id
            }
            if ($startRelation -cne 'incomparable' -and $endRelation -cne 'incomparable') {
                $comparable = $true
                if ($startRelation -in @('before', 'concurrent') -and $endRelation -in @('before', 'concurrent')) {
                    $inside = $true
                    break
                }
            }
        }
        if (-not $comparable) {
            return [pscustomobject]@{status='indeterminate'
                detail='chronology window is incomparable with occurrence'
            }
        }
        if (-not $inside) {
            return [pscustomobject]@{status='not-applicable'
                detail='occurrence is outside chronology window'
            }
        }
    }
    $query = ConvertTo-KnowledgeTemporalInstant $EffectiveAt
    if ($null -ne $app.effective_window -and $null -eq $query) {
        return [pscustomobject]@{status='indeterminate'
            detail='effective time was not supplied'
        }
    }
    $temporal = Get-KnowledgeTemporalMatch $app.effective_window $query
    if ($null -eq $temporal) {
        return [pscustomobject]@{status='not-applicable'
            detail='effective time is outside window'
        }
    }
    if ($temporal -ceq 'unknown' -or ([string]$temporal).StartsWith('indeterminate-', [StringComparison]::Ordinal)) {
        return [pscustomobject]@{status='indeterminate'
            detail="effective window is $temporal"
        }
    }
    return [pscustomobject]@{status='applicable'
        detail='all applicability selectors matched'
    }
}
function Get-KnowledgeRuleConditionEvaluation {
    param([object]$Registry, [object]$Condition, [object]$Iteration, [object]$Occurrence, [object]$EffectiveAt)
    $matched = $false
    $detail = ''
    switch ($Condition.condition_kind) {
        'occurrence-reached' {
            $matched = $Occurrence.template_id -ceq $Condition.target_id
            $detail = "current template is '$($Occurrence.template_id)'"
        }
        'occurrence-outcome' {
            $matchingOutcomes = @(
                $Registry.outcomes | Where-Object {
                    $_.occurrence_id -ceq $Occurrence.id -and
                    $_.subject_type -ceq $Condition.subject_type -and
                    $_.subject_id -ceq $Condition.subject_id -and
                    $_.outcome_kind -ceq $Condition.expected_value
                }
            )
            $matched = (
                $Occurrence.template_id -ceq $Condition.target_id -and
                $matchingOutcomes.Count -gt 0
            )
            $detail = if ($matched) {
                'matching subject-qualified outcome found'
            }
            else {
                'matching outcome not found'
            }
        }
        'state-availability' {
            $track = $Registry.tracks[$Condition.track_id]
            if (@($track.occurrence_ids) -cnotcontains $Occurrence.id) {
                return [pscustomobject]@{condition_id=$Condition.id
                    status='indeterminate'
                    detail='occurrence is not on selected state track'
                }
            }
            $state = Get-KnowledgeStateAt $Registry $Condition.track_id $Occurrence.id $Condition.target_type $Condition.target_id $Condition.state_kind
            $matched = $null -ne $state -and $state.resulting_availability -ceq $Condition.expected_value
            $detail = if ($null -eq $state) {
                'no state established'
            }
            else {
                "availability is '$($state.resulting_availability)'"
            }
        }
        'iteration-ordinal' {
            $value = [int]$Condition.comparison_value
            $matched = switch ($Condition.expected_value) {
                'equals' {
                    $Iteration.ordinal -eq $value
                }
                'at-least' {
                    $Iteration.ordinal -ge $value
                }
                'at-most' {
                    $Iteration.ordinal -le $value
                }
                'less-than' {
                    $Iteration.ordinal -lt $value
                }
                'greater-than' {
                    $Iteration.ordinal -gt $value
                }
            }
            $detail = "iteration ordinal is $($Iteration.ordinal)"
        }
        'schedule-due' {
            $scheduleStatus = Get-KnowledgeRecurrenceScheduleMatch $Registry $Condition.target_id $Iteration.id $Occurrence.id $EffectiveAt
            if ($scheduleStatus -ceq 'indeterminate') {
                return [pscustomobject]@{condition_id=$Condition.id
                    status='indeterminate'
                    detail='schedule could not be evaluated'
                }
            }
            $matched = $scheduleStatus -ceq 'due'
            $detail = "schedule is '$scheduleStatus'"
        }
    }
    return [pscustomobject]@{condition_id=$Condition.id
        status=if ($matched) {
            'matched'
        }
        else {
            'not-matched'
        }
        detail=$detail
    }
}
function Resolve-KnowledgeRecurrenceRuleEffects {
    param([object]$Registry, [object[]]$SelectedRules)
    $contributions = @()
    foreach ($rule in @($SelectedRules | Sort-Object id)) {
        foreach ($effect in @($rule.effects)) {
            $contributions += [pscustomobject]@{rule_id=$rule.id
                effect=$effect
                signature="$($effect.effect_kind)|$($effect.target_type)|$($effect.target_id)"
            }
        }
    }
    $resolved = @()
    $conflicts = @()
    foreach ($group in @($contributions | Group-Object signature | Sort-Object Name)) {
        $members = @($group.Group)
        $effect = $members[0].effect
        $policy = [string]$Registry.effect_repetition_policies[$effect.effect_kind]
        $count = $members.Count
        $executionCount = if ($policy -ceq 'accumulating') {
            $count
        }
        else {
            1
        }
        if ($policy -ceq 'invalid' -and $count -gt 1) {
            $executionCount = 0
            $conflicts += "duplicate $($effect.effect_kind) effect on $($effect.target_type):$($effect.target_id) is invalid"
        }
        $resolved += [pscustomobject]@{effect_kind=$effect.effect_kind
            target_type=$effect.target_type
            target_id=$effect.target_id
            repetition_policy=$policy
            contribution_count=$count
            proposed_execution_count=$executionCount
            contributing_rule_ids=@($members | ForEach-Object { $_.rule_id })
            contributing_effect_ids=@($members | ForEach-Object { $_.effect.id })
        }
    }
    return [pscustomobject]@{proposed_effects=@($resolved)
        conflicts=@($conflicts | Sort-Object -Unique)
    }
}
function Get-KnowledgeResolvedEffectConflicts {
    param([object]$Registry, [object[]]$Effects)
    $conflicts = @()
    $kinds = @($Effects | ForEach-Object { $_.effect_kind } | Sort-Object -Unique)
    for ($leftIndex = 0; $leftIndex -lt $kinds.Count; $leftIndex++) {
        for ($rightIndex = $leftIndex + 1; $rightIndex -lt $kinds.Count; $rightIndex++) {
            $left = [string]$kinds[$leftIndex]
            $right = [string]$kinds[$rightIndex]
            $pair = "$left|$right"
            if ($Registry.effect_global_incompatibility_pairs.ContainsKey($pair)) {
                $conflicts += "$left conflicts with $right globally"
            }
            if ($Registry.effect_same_target_incompatibility_pairs.ContainsKey($pair)) {
                foreach ($leftEffect in @($Effects | Where-Object { $_.effect_kind -ceq $left })) {
                    foreach ($rightEffect in @($Effects | Where-Object { $_.effect_kind -ceq $right })) {
                        if ($leftEffect.target_type -ceq $rightEffect.target_type -and $leftEffect.target_id -ceq $rightEffect.target_id) {
                            $conflicts += "$left conflicts with $right on $($leftEffect.target_type):$($leftEffect.target_id)"
                        }
                    }
                }
            }
        }
    }
    $resetTargets = @($Effects | Where-Object { $_.effect_kind -ceq 'change-reset-point' } | ForEach-Object { $_.target_id } | Sort-Object -Unique)
    if ($resetTargets.Count -gt 1) {
        $conflicts += 'multiple change-reset-point effects select different targets'
    }
    return @($conflicts | Sort-Object -Unique)
}
function Get-KnowledgeRecurrenceRuleEvaluation {
    param([object]$Registry, [string]$RecurrenceId, [string]$OccurrenceId, [object]$EffectiveAt = $null)
    if (-not $Registry.recurrences.Contains($RecurrenceId)) {
        throw "Unknown recurrence '$RecurrenceId'."
    }
    if (-not $Registry.occurrences.Contains($OccurrenceId)) {
        throw "Unknown occurrence '$OccurrenceId'."
    }
    $recurrence = $Registry.recurrences[$RecurrenceId]
    $occurrence = $Registry.occurrences[$OccurrenceId]
    if ($null -eq $occurrence.iteration_id) {
        throw "Occurrence '$OccurrenceId' is not part of a recurrence iteration."
    }
    $iteration = $Registry.iterations[$occurrence.iteration_id]
    if ($iteration.recurrence_id -cne $RecurrenceId) {
        throw "Occurrence '$OccurrenceId' does not belong to recurrence '$RecurrenceId'."
    }
    $working = [ordered]@{}
    $indeterminate = $false
    $patternRules = @(Get-KnowledgeRulesForRecurrencePattern $Registry $recurrence.pattern_id)
    foreach ($rule in $patternRules) {
        $app = Get-KnowledgeRuleApplicabilityStatus $Registry $rule $recurrence $iteration $occurrence $EffectiveAt
        $evaluations = @()
        $matched = $false
        $disposition = $app.detail
        if ($app.status -cin @('applicable', 'indeterminate')) {
            $evaluations = @($rule.conditions | ForEach-Object { Get-KnowledgeRuleConditionEvaluation $Registry $_ $iteration $occurrence $EffectiveAt })
            $statuses = @($evaluations | ForEach-Object { $_.status })
            if ($rule.condition_logic -ceq 'all') {
                $conditionsMatched = @($statuses | Where-Object { $_ -cne 'matched' }).Count -eq 0
                $conditionsRejected = $statuses -ccontains 'not-matched'
                $conditionIndeterminate = ($statuses -ccontains 'indeterminate') -and ($statuses -cnotcontains 'not-matched')
            }
            else {
                $conditionsMatched = $statuses -ccontains 'matched'
                $conditionsRejected = -not $conditionsMatched -and ($statuses -cnotcontains 'indeterminate')
                $conditionIndeterminate = -not $conditionsMatched -and ($statuses -ccontains 'indeterminate')
            }
            if ($app.status -ceq 'indeterminate') {
                if ($conditionsRejected) {
                    $disposition = 'conditions did not match'
                }
                else {
                    $indeterminate = $true
                }
            }
            else {
                $matched = $conditionsMatched
                if ($conditionIndeterminate) {
                    $indeterminate = $true
                    $disposition = 'conditions indeterminate'
                }
                else {
                    $disposition = if ($matched) {
                        'conditions matched'
                    }
                    else {
                        'conditions did not match'
                    }
                }
            }
        }
        $working[$rule.id] = [ordered]@{rule=$rule
            applicability=$app.status
            matched=$matched
            selected=$false
            disposition=$disposition
            conditions=@($evaluations)
        }
    }
    $matchedRules = @($working.Values | Where-Object { $_.matched } | ForEach-Object { $_.rule })
    $replacedGroups = @(
        $matchedRules |
            Where-Object {
                $_.applicability.application_level -ceq 'execution-override' -and
                $_.override_mode -ceq 'replace-group'
            } |
            ForEach-Object { $_.resolution_group } |
            Sort-Object -Unique
    )
    $candidates = @()
    foreach ($rule in $matchedRules) {
        if ($rule.applicability.application_level -ceq 'pattern-default' -and $replacedGroups -ccontains $rule.resolution_group) {
            $working[$rule.id].disposition = 'suppressed by execution override'
        }
        else {
            $candidates += $rule
        }
    }
    $selected = @()
    $conflicts = @()
    foreach ($group in @($candidates | Group-Object resolution_group | Sort-Object Name)) {
        $accumulating = @($group.Group | Where-Object { $_.selection_mode -ceq 'accumulate' })
        $selected += $accumulating
        $exclusive = @($group.Group | Where-Object { $_.selection_mode -ceq 'exclusive' })
        if ($exclusive.Count -gt 0) {
            $maximum = ($exclusive.priority | Measure-Object -Maximum).Maximum
            $leaders = @($exclusive | Where-Object { $_.priority -eq $maximum } | Sort-Object id)
            $signatures = @($leaders | ForEach-Object { @($_.effects | ForEach-Object { "$($_.effect_kind)|$($_.target_type)|$($_.target_id)" } | Sort-Object) -join ',' } | Sort-Object -Unique)
            if ($signatures.Count -gt 1) {
                $conflicts += "resolution group '$($group.Name)' has conflicting exclusive rules at priority $maximum"
                foreach ($rule in $leaders) {
                    $working[$rule.id].disposition = 'conflicting top-priority exclusive rule'
                }
            }
            else {
                $selected += $leaders[0]
                foreach ($rule in @($leaders | Select-Object -Skip 1)) {
                    $working[$rule.id].disposition = "equivalent to selected rule '$($leaders[0].id)'"
                }
            }
            foreach ($rule in @($exclusive | Where-Object { $_.priority -lt $maximum })) {
                $working[$rule.id].disposition = 'lower-priority exclusive rule'
            }
        }
    }
    $resolution = Resolve-KnowledgeRecurrenceRuleEffects $Registry $selected
    $effects = @($resolution.proposed_effects)
    $conflicts += @($resolution.conflicts)
    $conflicts += @(Get-KnowledgeResolvedEffectConflicts $Registry $effects)
    foreach ($rule in $selected) {
        $working[$rule.id].selected = $true
        $working[$rule.id].disposition = 'selected'
    }
    $traces = @($patternRules | Sort-Object id | ForEach-Object { $entry = $working[$_.id]
            [pscustomobject]@{rule_id=$_.id
                applicability=$entry.applicability
                matched=[bool]$entry.matched
                selected=[bool]$entry.selected
                disposition=$entry.disposition
                conditions=@($entry.conditions)
            } })
    $selectedIds = @($selected | ForEach-Object { $_.id } | Sort-Object -Unique)
    $conflicts = @($conflicts | Sort-Object -Unique)
    $status = if ($conflicts.Count -gt 0) {
        'conflict'
    }
    elseif ($indeterminate) {
        'indeterminate'
    }
    elseif ($selectedIds.Count -gt 0) {
        'selected'
    }
    else {
        'no-match'
    }
    $executionDisposition = @{
        conflict='blocked-conflict'
        selected='authorized'
        indeterminate='blocked-indeterminate'
        'no-match'='not-applicable'
    }[$status]
    $authorizedEffects = if ($executionDisposition -ceq 'authorized') {
        @($effects)
    }
    else {
        @()
    }
    return [pscustomobject]@{status=$status
        recurrence_id=$RecurrenceId
        occurrence_id=$OccurrenceId
        selected_rule_ids=$selectedIds
        proposed_effects=@($effects)
        authorized_effects=@($authorizedEffects)
        execution_disposition=$executionDisposition
        conflicts=$conflicts
        traces=$traces
    }
}
function Get-KnowledgeOccurrenceProvenanceTargets {
    param([object]$Registry)
    $bindings = [ordered]@{}
    foreach ($occurrence in @($Registry.occurrences.Values)) {
        foreach ($binding in @($occurrence.bindings)) {
            $bindings[$binding.id] = $binding
        }
    }
    $transitions = [ordered]@{}
    foreach ($item in @($Registry.transitions)) {
        $transitions[$item.id] = $item
    }
    $causal = [ordered]@{}
    foreach ($item in @($Registry.causal_relations)) {
        $causal[$item.id] = $item
    }
    $outcomes = [ordered]@{}
    foreach ($item in @($Registry.outcomes)) {
        $outcomes[$item.id] = $item
    }
    $rules = [ordered]@{}
    foreach ($item in @($Registry.rules)) {
        $rules[$item.id] = $item
    }
    $states = [ordered]@{}
    foreach ($item in @($Registry.state_transitions)) {
        $states[$item.id] = $item
    }
    $carryovers = [ordered]@{}
    foreach ($item in @($Registry.carryovers)) {
        $carryovers[$item.id] = $item
    }
    return [ordered]@{'occurrence-branch'=$Registry.branches
        'occurrence-template'=$Registry.templates
        'recurrence-pattern'=$Registry.recurrence_patterns
        recurrence=$Registry.recurrences
        'recurrence-iteration'=$Registry.iterations
        'recurrence-cardinality'=$Registry.recurrence_cardinalities
        'recurrence-phase'=$Registry.phases
        'recurrence-schedule'=$Registry.schedules
        occurrence=$Registry.occurrences
        'occurrence-binding'=$bindings
        'occurrence-participation'=$Registry.occurrence_participations
        'occurrence-track'=$Registry.tracks
        'occurrence-track-entry'=$Registry.track_entries
        'occurrence-transition'=$transitions
        'causal-relation'=$causal
        'occurrence-outcome'=$outcomes
        'recurrence-rule'=$rules
        'state-transition'=$states
        'iteration-carryover'=$carryovers
    }
}

function Test-OccurrenceTarget {
    param(
        [string]$TargetType,
        [string]$TargetId,
        [object]$Branches,
        [object]$Templates,
        [object]$Patterns,
        [object]$Recurrences,
        [object]$Iterations,
        [object]$Occurrences,
        [object]$Tracks,
        [object]$Outcomes,
        [object]$Rules,
        [object]$States,
        [System.Collections.IDictionary]$ExternalTargets,
        [object]$Schedules = $null,
        [object]$Phases = $null
    )
    $internal = [ordered]@{'occurrence-branch'=$Branches
        'occurrence-template'=$Templates
        'recurrence-pattern'=$Patterns
        recurrence=$Recurrences
        'recurrence-iteration'=$Iterations
        occurrence=$Occurrences
        'occurrence-track'=$Tracks
        'occurrence-outcome'=$Outcomes
        'recurrence-rule'=$Rules
        'state-transition'=$States
        'recurrence-schedule'=$Schedules
        'recurrence-phase'=$Phases
    }
    if ($internal.Contains($TargetType)) {
        return $internal[$TargetType].Contains($TargetId)
    }
    if ($null -ne $ExternalTargets -and $ExternalTargets.Contains($TargetType)) {
        return @($ExternalTargets[$TargetType]) -ccontains $TargetId
    }
    return $false
}

function Test-OccurrenceRecurrenceWithin {
    param([string]$RecurrenceId, [string]$AncestorId, [object]$Recurrences)
    $current = $RecurrenceId
    while ($null -ne $current) {
        if ($current -ceq $AncestorId) {
            return $true
        }
        $current = $Recurrences[$current].parent_recurrence_id
    }
    return $false
}
function Assert-OccurrenceTransitionProfile {
    param([object]$Transition, [object]$Occurrences, [object]$Iterations, [object]$Recurrences, [object]$Branches, [object]$Chronology, [string]$Context)
    $sourceOccurrence = $Occurrences[$Transition.source_occurrence_id]
    $targetOccurrence = $Occurrences[$Transition.target_occurrence_id]
    $sourceIteration = if ($null -ne $sourceOccurrence.iteration_id) {
        $Iterations[$sourceOccurrence.iteration_id]
    }
    else {
        $null
    }
    $targetIteration = if ($null -ne $targetOccurrence.iteration_id) {
        $Iterations[$targetOccurrence.iteration_id]
    }
    else {
        $null
    }
    $recurrenceId = $Transition.recurrence_id
    $profile = $Transition.transition_profile
    if ($profile -in @('ordered', 'jump')) {
        $hasMismatchedRecurrence = (
            $null -eq $sourceIteration -or
            $null -eq $targetIteration -or
            $sourceIteration.recurrence_id -cne $recurrenceId -or
            $targetIteration.recurrence_id -cne $recurrenceId
        )
        if ($null -ne $recurrenceId -and $hasMismatchedRecurrence) {
            throw "$Context scoped '$profile' endpoints must belong to recurrence '$recurrenceId'."
        }
        if ($profile -ceq 'ordered') {
            $evidence = @($Transition.track_ids).Count -gt 0
            if ($null -ne $sourceIteration -and $null -ne $targetIteration -and $sourceIteration.recurrence_id -ceq $targetIteration.recurrence_id) {
                if ($sourceIteration.ordinal -gt $targetIteration.ordinal) {
                    throw "$Context ordered transition moves backward across recurrence iterations."
                }
                $evidence = $evidence -or $sourceIteration.ordinal -lt $targetIteration.ordinal
            }
            foreach ($sourceBinding in @($sourceOccurrence.bindings | Where-Object { $_.role -ceq 'primary' })) {
                foreach ($targetBinding in @($targetOccurrence.bindings | Where-Object { $_.role -ceq 'primary' })) {
                    $comparison = Get-KnowledgeChronologyComparison $Chronology $sourceBinding.position_id $targetBinding.position_id
                    if ($comparison -ceq 'after') {
                        throw "$Context ordered transition contradicts exact chronology position order."
                    }
                    $evidence = $evidence -or $comparison -ceq 'before'
                }
            }
            if (-not $evidence) {
                throw "$Context ordered transition requires a forward track, iteration, or chronology order."
            }
        }
        return
    }
    if ($profile -ceq 'recurrence-advance') {
        if ($null -eq $sourceIteration -or $null -eq $targetIteration -or $null -eq $recurrenceId) {
            throw "$Context recurrence-advance transitions require recurrence-bound source and target iterations."
        }
        if ($sourceIteration.recurrence_id -cne $recurrenceId -or $targetIteration.recurrence_id -cne $recurrenceId -or $sourceIteration.ordinal -ge $targetIteration.ordinal) {
            throw "$Context recurrence-advance transition must advance iterations in recurrence '$recurrenceId'."
        }
        return
    }
    if ($profile -ceq 'recurrence-exit') {
        if ($null -eq $sourceIteration -or $null -eq $recurrenceId -or -not (Test-OccurrenceRecurrenceWithin $sourceIteration.recurrence_id $recurrenceId $Recurrences)) {
            throw "$Context recurrence-exit source must belong to recurrence '$recurrenceId'."
        }
        if ($null -ne $targetIteration -and (Test-OccurrenceRecurrenceWithin $targetIteration.recurrence_id $recurrenceId $Recurrences)) {
            throw "$Context recurrence-exit target must leave recurrence '$recurrenceId'."
        }
        return
    }
    if ($profile -ceq 'branch-fork') {
        $hasMismatchedRecurrence = (
            $null -eq $sourceIteration -or
            $null -eq $targetIteration -or
            $sourceIteration.recurrence_id -cne $recurrenceId -or
            $targetIteration.recurrence_id -cne $recurrenceId
        )
        if ($null -ne $recurrenceId -and $hasMismatchedRecurrence) {
            throw "$Context scoped '$profile' endpoints must belong to recurrence '$recurrenceId'."
        }
        $targetBranch = $Branches[$targetOccurrence.branch_id]
        if ($null -eq $targetBranch.parent_branch_id -or $targetBranch.parent_branch_id -cne $sourceOccurrence.branch_id -or $targetBranch.fork_occurrence_id -cne $sourceOccurrence.id) {
            throw "$Context branch-fork endpoints do not match the target branch lineage."
        }
        return
    }
    if ($profile -ceq 'branch-merge') {
        $hasMismatchedRecurrence = (
            $null -eq $sourceIteration -or
            $null -eq $targetIteration -or
            $sourceIteration.recurrence_id -cne $recurrenceId -or
            $targetIteration.recurrence_id -cne $recurrenceId
        )
        if ($null -ne $recurrenceId -and $hasMismatchedRecurrence) {
            throw "$Context scoped '$profile' endpoints must belong to recurrence '$recurrenceId'."
        }
        if ($sourceOccurrence.branch_id -ceq $targetOccurrence.branch_id) {
            throw "$Context branch-merge endpoints must belong to different branches."
        }
        return
    }
    throw "$Context uses unsupported transition profile '$profile'."
}

function ConvertTo-KnowledgeOccurrenceRegistry {
    param([object]$Data, [string]$Path, [object]$SchemaPacks, [object]$Chronology, [System.Collections.IDictionary]$SubjectTargets = $null, [System.Collections.IDictionary]$PayloadTargets = $null)
    $requiredCapabilities = @(
        'occurrence-recurrence-modeling'
        'recurrence-rule-modeling'
        'state-availability-acquisition'
        'deterministic-recurrence-rule-evaluation'
        'recurrence-schedule-modeling'
        'recurrence-policy-integrity'
        'extensible-recurrence-policy-semantics'
        'civil-schedule-boundary-integrity'
        'semantic-declaration-integrity'
        'deterministic-effect-resolution'
        'aggregate-recurrence-cardinality'
        'occurrence-participation-identity'
    )
    foreach ($capability in $requiredCapabilities) {
        if (-not (Test-SchemaPackCapabilityEnabled $SchemaPacks $capability)) {
            throw "Occurrence registry requires enabled capability '$capability'."
        }
    }
    Assert-OccurrenceMap $Data 'Occurrence registry root'
    $rootKeys = @(
        'schema_version'
        'branches'
        'templates'
        'recurrence_patterns'
        'recurrences'
        'iterations'
        'recurrence_cardinalities'
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
    Assert-KnowledgeMapKeys $Data $rootKeys 'Occurrence registry root'
    $schemaVersion = Get-ProjectMapValue $Data 'schema_version'
    if ($schemaVersion -isnot [int] -or $schemaVersion -ne 6) {
        throw "Unsupported occurrence schema_version '$schemaVersion'; expected 6."
    }

    $rawBranches = Get-ProjectMapValue $Data 'branches'
    Assert-OccurrenceMap $rawBranches 'occurrences.branches'
    if ($rawBranches.Count -eq 0) {
        throw 'occurrences.branches cannot be empty.'
    }
    $branches = [ordered]@{}
    foreach ($id in @($rawBranches.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'occurrence branch ID'
        $context = "branches.$id"
        $item = $rawBranches[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('label', 'parent_branch_id', 'fork_occurrence_id') $context
        $parent = Get-OptionalOccurrenceString $item 'parent_branch_id' $context
        $fork = Get-OptionalOccurrenceString $item 'fork_occurrence_id' $context
        if (($null -eq $parent) -ne ($null -eq $fork)) {
            throw "$context must set both parent_branch_id and fork_occurrence_id, or neither."
        }
        $branches[$id] = [pscustomobject]@{id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            parent_branch_id=$parent
            fork_occurrence_id=$fork
        }
    }
    foreach ($branch in @($branches.Values)) {
        if ($null -ne $branch.parent_branch_id -and -not $branches.Contains($branch.parent_branch_id)) {
            throw "branches.$($branch.id).parent_branch_id references unknown branch '$($branch.parent_branch_id)'."
        }
    }
    Assert-OccurrenceParentAcyclic $branches 'parent_branch_id' 'Branch'

    $rawTemplates = Get-ProjectMapValue $Data 'templates'
    Assert-OccurrenceMap $rawTemplates 'occurrences.templates'
    $templates = [ordered]@{}
    foreach ($id in @($rawTemplates.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'occurrence template ID'
        $context = "templates.$id"
        $item = $rawTemplates[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('label', 'kind', 'aliases') $context
        $kind = Get-RequiredOccurrenceString $item 'kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.template-kind' $kind "$context.kind"
        $templates[$id] = [pscustomobject]@{id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            kind=$kind
            aliases=@(Get-OccurrenceStringList $item 'aliases' $context)
        }
    }

    $rawPatterns = Get-ProjectMapValue $Data 'recurrence_patterns'
    Assert-OccurrenceMap $rawPatterns 'occurrences.recurrence_patterns'
    $patterns = [ordered]@{}
    foreach ($id in @($rawPatterns.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'recurrence pattern ID'
        $context = "recurrence_patterns.$id"
        $item = $rawPatterns[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('label', 'kind', 'aliases') $context
        $kind = Get-RequiredOccurrenceString $item 'kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.recurrence-kind' $kind "$context.kind"
        $patterns[$id] = [pscustomobject]@{id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            kind=$kind
            aliases=@(Get-OccurrenceStringList $item 'aliases' $context)
        }
    }

    $rawRecurrences = Get-ProjectMapValue $Data 'recurrences'
    Assert-OccurrenceMap $rawRecurrences 'occurrences.recurrences'
    $recurrences = [ordered]@{}
    foreach ($id in @($rawRecurrences.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'recurrence ID'
        $context = "recurrences.$id"
        $item = $rawRecurrences[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('label', 'pattern_id', 'parent_recurrence_id', 'status') $context
        $patternId = Get-RequiredOccurrenceString $item 'pattern_id' $context
        if (-not $patterns.Contains($patternId)) {
            throw "$context.pattern_id references unknown recurrence pattern '$patternId'."
        }
        $status = Get-RequiredOccurrenceString $item 'status' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.recurrence-status' $status "$context.status"
        $recurrences[$id] = [pscustomobject]@{id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            pattern_id=$patternId
            parent_recurrence_id=Get-OptionalOccurrenceString $item 'parent_recurrence_id' $context
            status=$status
        }
    }
    foreach ($item in @($recurrences.Values)) {
        if ($null -ne $item.parent_recurrence_id -and -not $recurrences.Contains($item.parent_recurrence_id)) {
            throw "recurrences.$($item.id).parent_recurrence_id references unknown recurrence '$($item.parent_recurrence_id)'."
        }
    }
    Assert-OccurrenceParentAcyclic $recurrences 'parent_recurrence_id' 'Recurrence'

    $rawIterations = Get-ProjectMapValue $Data 'iterations'
    Assert-OccurrenceMap $rawIterations 'occurrences.iterations'
    $iterations = [ordered]@{}
    $ordinals = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($id in @($rawIterations.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'recurrence iteration ID'
        $context = "iterations.$id"
        $item = $rawIterations[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('recurrence_id', 'ordinal', 'parent_iteration_id', 'status') $context
        $recurrenceId = Get-RequiredOccurrenceString $item 'recurrence_id' $context
        if (-not $recurrences.Contains($recurrenceId)) {
            throw "$context.recurrence_id references unknown recurrence '$recurrenceId'."
        }
        $ordinal = Get-ProjectMapValue $item 'ordinal'
        if ($ordinal -isnot [int] -or $ordinal -lt 1) {
            throw "$context.ordinal must be a positive integer."
        }
        if (-not $ordinals.Add("$recurrenceId|$ordinal")) {
            throw "$context.ordinal duplicates ordinal $ordinal in '$recurrenceId'."
        }
        $status = Get-RequiredOccurrenceString $item 'status' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.iteration-status' $status "$context.status"
        $iterations[$id] = [pscustomobject]@{id=[string]$id
            recurrence_id=$recurrenceId
            ordinal=[int]$ordinal
            parent_iteration_id=Get-OptionalOccurrenceString $item 'parent_iteration_id' $context
            status=$status
        }
    }
    foreach ($iteration in @($iterations.Values)) {
        $parentRecurrence = $recurrences[$iteration.recurrence_id].parent_recurrence_id
        if ($null -eq $parentRecurrence) {
            if ($null -ne $iteration.parent_iteration_id) {
                throw "iterations.$($iteration.id).parent_iteration_id is only valid for a nested recurrence."
            }
        }
        elseif (
            $null -eq $iteration.parent_iteration_id -or
            -not $iterations.Contains($iteration.parent_iteration_id) -or
            $iterations[$iteration.parent_iteration_id].recurrence_id -cne $parentRecurrence
        ) {
            throw "iterations.$($iteration.id).parent_iteration_id must reference an iteration of parent recurrence '$parentRecurrence'."
        }
    }
    foreach ($recurrence in @($recurrences.Values)) {
        $members = @($iterations.Values | Where-Object { $_.recurrence_id -ceq $recurrence.id } | Sort-Object ordinal)
        $active = @($members | Where-Object { $_.status -ceq 'active' })
        $terminated = @($members | Where-Object { $_.status -ceq 'terminated' })
        if ($active.Count -gt 1 -or $terminated.Count -gt 1) {
            throw "Recurrence '$($recurrence.id)' has multiple terminal lifecycle states."
        }
        if ($active.Count -eq 1 -and $active[0].id -cne $members[-1].id) {
            throw "Recurrence '$($recurrence.id)' active iteration must have the highest ordinal."
        }
        if ($terminated.Count -eq 1 -and $terminated[0].id -cne $members[-1].id) {
            throw "Recurrence '$($recurrence.id)' terminated iteration must have the highest ordinal."
        }
        if ($terminated.Count -eq 1 -and $recurrence.status -cne 'terminated') {
            throw "Recurrence '$($recurrence.id)' with a terminated iteration must itself be terminated."
        }
        if ($recurrence.status -ceq 'terminated' -and $members.Count -gt 0 -and $members[-1].status -cne 'terminated') {
            throw "Terminated recurrence '$($recurrence.id)' must end with a terminated iteration."
        }
        if ($recurrence.status -ceq 'completed' -and ($active.Count -gt 0 -or $terminated.Count -gt 0)) {
            throw "Completed recurrence '$($recurrence.id)' cannot contain active or terminated iterations."
        }
    }

    $rawCardinalities = Get-ProjectMapValue $Data 'recurrence_cardinalities'
    Assert-OccurrenceMap $rawCardinalities 'occurrences.recurrence_cardinalities'
    $cardinalities = [ordered]@{}
    $cardinalitySemantics = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($id in @($rawCardinalities.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'recurrence cardinality ID'
        $context = "recurrence_cardinalities.$id"
        $item = $rawCardinalities[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @(
            'label'
            'recurrence_id'
            'cardinality_kind'
            'minimum_count'
            'maximum_count'
            'coverage_mode'
            'representative_iteration_ids'
            'certainty'
        ) $context
        $recurrenceId = Get-RequiredOccurrenceString $item 'recurrence_id' $context
        if (-not $recurrences.Contains($recurrenceId)) {
            throw "$context.recurrence_id references unknown recurrence '$recurrenceId'."
        }
        $kind = Get-RequiredOccurrenceString $item 'cardinality_kind' $context
        $coverage = Get-RequiredOccurrenceString $item 'coverage_mode' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.cardinality-kind' $kind "$context.cardinality_kind"
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.cardinality-coverage' $coverage "$context.coverage_mode"
        $minimum = Get-OptionalOccurrenceNonnegativeCount $item 'minimum_count' $context
        $maximum = Get-OptionalOccurrenceNonnegativeCount $item 'maximum_count' $context
        $boundsValid = switch ($kind) {
            'exact' {
                $null -ne $minimum -and $minimum -eq $maximum
            }
            'minimum' {
                $null -ne $minimum -and $null -eq $maximum
            }
            'maximum' {
                $null -eq $minimum -and $null -ne $maximum
            }
            'range' {
                $null -ne $minimum -and $null -ne $maximum -and $minimum -lt $maximum
            }
            'unknown' {
                $null -eq $minimum -and $null -eq $maximum
            }
            default {
                $false
            }
        }
        if (-not $boundsValid) {
            throw "$context bounds do not match cardinality_kind '$kind'."
        }
        $representativeIds = @(Get-OccurrenceStringList $item 'representative_iteration_ids' $context)
        foreach ($iterationId in $representativeIds) {
            if (
                -not $iterations.Contains($iterationId) -or
                $iterations[$iterationId].recurrence_id -cne $recurrenceId
            ) {
                throw "$context.representative_iteration_ids must belong to recurrence '$recurrenceId'."
            }
        }
        $representedCount = $representativeIds.Count
        if ($null -ne $maximum -and $representedCount -gt $maximum) {
            throw "$context represents more concrete iterations than its maximum_count."
        }
        if ($coverage -ceq 'complete') {
            if ($kind -cne 'exact' -or $representedCount -ne $minimum) {
                throw "$context complete coverage requires an exact count and full enumeration."
            }
        }
        elseif ($coverage -ceq 'representative') {
            if ($representedCount -eq 0) {
                throw "$context representative coverage requires concrete iteration IDs."
            }
            if ($kind -ceq 'exact' -and $representedCount -eq $minimum) {
                throw "$context exact fully enumerated coverage must use 'complete'."
            }
        }
        elseif ($representedCount -gt 0) {
            throw "$context unmaterialized coverage cannot reference concrete iterations."
        }
        $certainty = Get-RequiredOccurrenceString $item 'certainty' $context
        Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
        $semanticKey = @(
            $recurrenceId
            $kind
            $(if ($null -eq $minimum) {
                    '<null>'
                }
                else {
                    $minimum
                })
            $(if ($null -eq $maximum) {
                    '<null>'
                }
                else {
                    $maximum
                })
            $coverage
            (@($representativeIds | Sort-Object) -join ',')
            $certainty
        ) -join '|'
        if (-not $cardinalitySemantics.Add($semanticKey)) {
            throw "$context duplicates an existing semantic recurrence cardinality."
        }
        $cardinalities[$id] = [pscustomobject]@{
            id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            recurrence_id=$recurrenceId
            cardinality_kind=$kind
            minimum_count=$minimum
            maximum_count=$maximum
            coverage_mode=$coverage
            representative_iteration_ids=@($representativeIds)
            certainty=$certainty
        }
    }

    $rawPhases = Get-ProjectMapValue $Data 'phases'
    Assert-OccurrenceMap $rawPhases 'occurrences.phases'
    $phases = [ordered]@{}
    foreach ($id in @($rawPhases.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'recurrence phase ID'
        $context = "phases.$id"
        $item = $rawPhases[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('label', 'recurrence_id', 'start_ordinal', 'end_ordinal') $context
        $recurrenceId = Get-RequiredOccurrenceString $item 'recurrence_id' $context
        if (-not $recurrences.Contains($recurrenceId)) {
            throw "$context.recurrence_id references unknown recurrence '$recurrenceId'."
        }
        $start = Get-RequiredOccurrencePositiveInteger $item 'start_ordinal' $context
        $end = Get-OptionalOccurrenceNonnegativeInteger $item 'end_ordinal' $context
        if ($end -eq 0 -or ($null -ne $end -and $end -lt $start)) {
            throw "$context.end_ordinal must be null or at least start_ordinal."
        }
        foreach ($prior in @($phases.Values | Where-Object { $_.recurrence_id -ceq $recurrenceId })) {
            $priorEnd = if ($null -eq $prior.end_ordinal) {
                [int]::MaxValue
            }
            else {
                $prior.end_ordinal
            }
            $thisEnd = if ($null -eq $end) {
                [int]::MaxValue
            }
            else {
                $end
            }
            if ($start -le $priorEnd -and $prior.start_ordinal -le $thisEnd) {
                throw "$context overlaps recurrence phase '$($prior.id)'."
            }
        }
        $phases[$id] = [pscustomobject]@{id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            recurrence_id=$recurrenceId
            start_ordinal=$start
            end_ordinal=$end
        }
    }

    $rawSchedules = Get-ProjectMapValue $Data 'schedules'
    Assert-OccurrenceMap $rawSchedules 'occurrences.schedules'
    $schedules = [ordered]@{}
    foreach ($id in @($rawSchedules.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'recurrence schedule ID'
        $context = "schedules.$id"
        $item = $rawSchedules[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('label', 'pattern_id', 'schedule_kind', 'interval', 'unit', 'anchor_position_id', 'anchor_value') $context
        $patternId = Get-RequiredOccurrenceString $item 'pattern_id' $context
        if (-not $patterns.Contains($patternId)) {
            throw "$context.pattern_id references unknown recurrence pattern '$patternId'."
        }
        $kind = Get-RequiredOccurrenceString $item 'schedule_kind' $context
        $unit = Get-RequiredOccurrenceString $item 'unit' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.schedule-kind' $kind "$context.schedule_kind"
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.schedule-unit' $unit "$context.unit"
        $interval = Get-RequiredOccurrencePositiveInteger $item 'interval' $context
        $anchorPosition = Get-OptionalOccurrenceString $item 'anchor_position_id' $context
        $anchorValue = Get-OptionalOccurrenceString $item 'anchor_value' $context
        if ($kind -ceq 'chronology-step') {
            if ($unit -cne 'coordinate' -or $null -eq $anchorPosition -or -not $Chronology.positions.Contains($anchorPosition) -or $null -ne $anchorValue) {
                throw "$context chronology-step schedules require unit 'coordinate', a known anchor_position_id, and null anchor_value."
            }
            $anchor = $Chronology.positions[$anchorPosition]
            if ($Chronology.coordinate_systems[$anchor.coordinate_system_id].kind -ceq 'era-ordinal') {
                throw "$context chronology-step schedules do not cross era-ordinal coordinates."
            }
        }
        else {
            if ($unit -ceq 'coordinate' -or $null -ne $anchorPosition -or $null -eq $anchorValue) {
                throw "$context civil-calendar schedules require a civil unit, null anchor_position_id, and anchor_value."
            }
            $format = switch ($unit) {
                'year' {
                    'yyyy'
                }
                'month' {
                    'yyyy-MM'
                }
                'day' {
                    'yyyy-MM-dd'
                }
                'week' {
                    'yyyy-MM-dd'
                }
                default {
                    throw "$context.unit '$unit' is not valid for a civil-calendar schedule."
                }
            }
            $parsed = [datetime]::MinValue
            if (-not [datetime]::TryParseExact($anchorValue, $format, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$parsed)) {
                throw "$context.anchor_value does not match schedule unit '$unit': $anchorValue"
            }
        }
        $schedules[$id] = [pscustomobject]@{id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            pattern_id=$patternId
            schedule_kind=$kind
            interval=$interval
            unit=$unit
            anchor_position_id=$anchorPosition
            anchor_value=$anchorValue
        }
    }

    $rawOccurrences = Get-ProjectMapValue $Data 'occurrences'
    Assert-OccurrenceMap $rawOccurrences 'occurrences.occurrences'
    $occurrences = [ordered]@{}
    $bindingIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($id in @($rawOccurrences.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'occurrence ID'
        $context = "occurrences.$id"
        $item = $rawOccurrences[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('template_id', 'label', 'iteration_id', 'branch_id', 'bindings') $context
        $templateId = Get-RequiredOccurrenceString $item 'template_id' $context
        $branchId = Get-RequiredOccurrenceString $item 'branch_id' $context
        $iterationId = Get-OptionalOccurrenceString $item 'iteration_id' $context
        if (-not $templates.Contains($templateId)) {
            throw "$context.template_id references unknown template '$templateId'."
        }
        if (-not $branches.Contains($branchId)) {
            throw "$context.branch_id references unknown branch '$branchId'."
        }
        if ($null -ne $iterationId -and -not $iterations.Contains($iterationId)) {
            throw "$context.iteration_id references unknown iteration '$iterationId'."
        }
        $rawBindings = $item['bindings']
        Assert-OccurrenceList $rawBindings "$context.bindings"
        $bindings = @()
        $semanticBindings = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $index = 0
        foreach ($rawBinding in @($rawBindings)) {
            $bindingContext = "$context.bindings[$index]"
            Assert-OccurrenceMap $rawBinding $bindingContext
            Assert-KnowledgeMapKeys $rawBinding @('id', 'position_id', 'role') $bindingContext
            $bindingId = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $rawBinding 'id' $bindingContext) "$bindingContext.id"
            if (-not $bindingIds.Add($bindingId)) {
                throw "$bindingContext.id duplicates '$bindingId'."
            }
            $positionId = Get-RequiredOccurrenceString $rawBinding 'position_id' $bindingContext
            if (-not $Chronology.positions.Contains($positionId)) {
                throw "$bindingContext.position_id references unknown chronology position '$positionId'."
            }
            $role = Get-RequiredOccurrenceString $rawBinding 'role' $bindingContext
            Assert-OccurrencePackValue $SchemaPacks 'occurrence.binding-role' $role "$bindingContext.role"
            if (-not $semanticBindings.Add("$positionId|$role")) {
                throw "$context.bindings duplicates '$role' binding to '$positionId'."
            }
            $bindings += [pscustomobject]@{id=$bindingId
                position_id=$positionId
                role=$role
            }
            $index++
        }
        $primary = @($bindings | Where-Object { $_.role -ceq 'primary' })
        for ($left = 0; $left -lt $primary.Count; $left++) {
            for ($right = $left + 1; $right -lt $primary.Count; $right++) {
                $comparison = Get-KnowledgeChronologyComparison $Chronology $primary[$left].position_id $primary[$right].position_id
                if ($comparison -in @('before', 'after')) {
                    throw "$context.bindings declares ordered chronology positions '$($primary[$left].position_id)' and '$($primary[$right].position_id)' as primary coordinates of one occurrence."
                }
            }
        }
        $occurrences[$id] = [pscustomobject]@{id=[string]$id
            template_id=$templateId
            label=Get-OptionalOccurrenceString $item 'label' $context
            iteration_id=$iterationId
            branch_id=$branchId
            bindings=@($bindings)
        }
    }
    foreach ($branch in @($branches.Values)) {
        if ($null -ne $branch.fork_occurrence_id -and -not $occurrences.Contains($branch.fork_occurrence_id)) {
            throw "branches.$($branch.id).fork_occurrence_id references unknown occurrence '$($branch.fork_occurrence_id)'."
        }
        if ($null -ne $branch.fork_occurrence_id -and $occurrences[$branch.fork_occurrence_id].branch_id -cne $branch.parent_branch_id) {
            throw "branches.$($branch.id).fork_occurrence_id must belong to parent branch '$($branch.parent_branch_id)'."
        }
    }
    foreach ($context in @($Chronology.narrative_contexts)) {
        if ($null -ne $context.branch_id -and -not $branches.Contains($context.branch_id)) {
            throw "Chronology context '$($context.id)' references unknown occurrence branch '$($context.branch_id)'."
        }
    }

    $rawParticipations = Get-ProjectMapValue $Data 'occurrence_participations'
    Assert-OccurrenceMap $rawParticipations 'occurrences.occurrence_participations'
    $participations = [ordered]@{}
    $participationSemantics = [ordered]@{}
    $chronologyContextIds = @($Chronology.narrative_contexts | ForEach-Object { $_.id })
    foreach ($id in @($rawParticipations.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'occurrence participation ID'
        $context = "occurrence_participations.$id"
        $item = $rawParticipations[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys `
            $item `
        @('occurrence_id', 'subject_type', 'subject_id', 'role', 'perspective', 'status', 'chronology_context_id') `
            $context
        $occurrenceId = Get-RequiredOccurrenceString $item 'occurrence_id' $context
        if (-not $occurrences.Contains($occurrenceId)) {
            throw "$context.occurrence_id references unknown occurrence '$occurrenceId'."
        }
        $subjectType = Get-RequiredOccurrenceString $item 'subject_type' $context
        $subjectId = Get-RequiredOccurrenceString $item 'subject_id' $context
        if (
            $null -eq $SubjectTargets -or
            -not $SubjectTargets.Contains($subjectType) -or
            @($SubjectTargets[$subjectType]) -cnotcontains $subjectId
        ) {
            throw "$context.subject references unknown target '$subjectType`:$subjectId'."
        }
        $role = Get-RequiredOccurrenceString $item 'role' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.participation-role' $role "$context.role"
        $perspective = Get-RequiredOccurrenceString $item 'perspective' $context
        Assert-OccurrencePackValue `
            $SchemaPacks `
            'occurrence.participation-perspective' `
            $perspective `
            "$context.perspective"
        $status = Get-RequiredOccurrenceString $item 'status' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.participation-status' $status "$context.status"
        $chronologyContextId = Get-OptionalOccurrenceString $item 'chronology_context_id' $context
        if ($null -ne $chronologyContextId -and $chronologyContextIds -cnotcontains $chronologyContextId) {
            throw "$context.chronology_context_id references unknown chronology context '$chronologyContextId'."
        }
        $semanticKey = @(
            $occurrenceId,
            $subjectType,
            $subjectId,
            $role,
            $perspective,
            $status,
            $chronologyContextId
        ) -join '|'
        if (-not $participationSemantics.Contains($semanticKey)) {
            $participationSemantics[$semanticKey] = @()
        }
        $participationSemantics[$semanticKey] = @($participationSemantics[$semanticKey]) + @([string]$id)
        $participations[$id] = [pscustomobject]@{id=[string]$id
            occurrence_id=$occurrenceId
            subject_type=$subjectType
            subject_id=$subjectId
            role=$role
            perspective=$perspective
            status=$status
            chronology_context_id=$chronologyContextId
        }
    }

    $rawTracks = Get-ProjectMapValue $Data 'tracks'
    Assert-OccurrenceMap $rawTracks 'occurrences.tracks'
    $trackMetadata = [ordered]@{}
    foreach ($id in @($rawTracks.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'occurrence track ID'
        $context = "tracks.$id"
        $item = $rawTracks[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('label', 'kind', 'subject_type', 'subject_id') $context
        $kind = Get-RequiredOccurrenceString $item 'kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.track-kind' $kind "$context.kind"
        $subjectType = Get-RequiredOccurrenceString $item 'subject_type' $context
        $subjectId = Get-RequiredOccurrenceString $item 'subject_id' $context
        if ($null -eq $SubjectTargets -or -not $SubjectTargets.Contains($subjectType) -or @($SubjectTargets[$subjectType]) -cnotcontains $subjectId) {
            throw "$context references unknown subject '$subjectType`:$subjectId'."
        }
        $trackMetadata[$id] = [pscustomobject]@{id=[string]$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            kind=$kind
            subject_type=$subjectType
            subject_id=$subjectId
        }
    }

    $rawTrackEntries = Get-ProjectMapValue $Data 'track_entries'
    Assert-OccurrenceMap $rawTrackEntries 'occurrences.track_entries'
    $trackEntries = [ordered]@{}
    $trackOrdinals = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $trackParticipations = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($id in @($rawTrackEntries.Keys)) {
        $null = Assert-OccurrenceStableId ([string]$id) 'occurrence track-entry ID'
        $context = "track_entries.$id"
        $item = $rawTrackEntries[$id]
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('track_id', 'participation_id', 'ordinal') $context
        $trackId = Get-RequiredOccurrenceString $item 'track_id' $context
        $participationId = Get-RequiredOccurrenceString $item 'participation_id' $context
        $ordinal = Get-RequiredOccurrencePositiveInteger $item 'ordinal' $context
        if (-not $trackMetadata.Contains($trackId)) {
            throw "$context.track_id references unknown track '$trackId'."
        }
        if (-not $participations.Contains($participationId)) {
            throw "$context.participation_id references unknown participation '$participationId'."
        }
        $participation = $participations[$participationId]
        $track = $trackMetadata[$trackId]
        if (
            $participation.subject_type -cne $track.subject_type -or
            $participation.subject_id -cne $track.subject_id
        ) {
            throw "$context.participation_id subject does not match track '$trackId'."
        }
        if (-not $trackOrdinals.Add("$trackId|$ordinal")) {
            throw "$context.ordinal duplicates ordinal $ordinal on track '$trackId'."
        }
        if (-not $trackParticipations.Add("$trackId|$participationId")) {
            throw "$context.participation_id already appears on track '$trackId'."
        }
        $trackEntries[$id] = [pscustomobject]@{id=[string]$id
            track_id=$trackId
            participation_id=$participationId
            ordinal=$ordinal
        }
    }

    $tracks = [ordered]@{}
    foreach ($id in @($trackMetadata.Keys)) {
        $metadata = $trackMetadata[$id]
        $entries = @($trackEntries.Values | Where-Object { $_.track_id -ceq $id } | Sort-Object ordinal)
        for ($index = 0; $index -lt $entries.Count; $index++) {
            if ([int]$entries[$index].ordinal -ne ($index + 1)) {
                throw "Track '$id' entry ordinals must be contiguous from 1."
            }
        }
        $entryIds = @($entries | ForEach-Object { $_.id })
        $occurrenceIds = @(
            $entries |
                ForEach-Object { $participations[$_.participation_id].occurrence_id }
        )
        $tracks[$id] = [pscustomobject]@{id=[string]$id
            label=$metadata.label
            kind=$metadata.kind
            subject_type=$metadata.subject_type
            subject_id=$metadata.subject_id
            entry_ids=$entryIds
            occurrence_ids=$occurrenceIds
        }
    }
    $participationTracks = @{}
    foreach ($participationId in @($participations.Keys)) {
        $participationTracks[$participationId] = @()
    }
    foreach ($entry in @($trackEntries.Values)) {
        $participationTracks[$entry.participation_id] = @(
            @($participationTracks[$entry.participation_id]) + @($entry.track_id) |
                Sort-Object -Unique
        )
    }
    foreach ($semanticKey in @($participationSemantics.Keys)) {
        $duplicateIds = @($participationSemantics[$semanticKey])
        if ($duplicateIds.Count -lt 2) {
            continue
        }
        $sharedTracks = @($participationTracks[$duplicateIds[0]])
        foreach ($participationId in @($duplicateIds | Select-Object -Skip 1)) {
            $candidateTracks = @($participationTracks[$participationId])
            $sharedTracks = @($sharedTracks | Where-Object { $candidateTracks -ccontains $_ })
        }
        if ($sharedTracks.Count -eq 0) {
            $joinedIds = @($duplicateIds | ForEach-Object { "'$_'" }) -join ', '
            throw "Semantic duplicate participations $joinedIds must share a track that orders each encounter."
        }
    }
    foreach ($track in @($tracks.Values)) {
        $last = @{}
        foreach ($occurrenceId in @($track.occurrence_ids)) {
            $iterationId = $occurrences[$occurrenceId].iteration_id
            if ($null -eq $iterationId) {
                continue
            }
            $iteration = $iterations[$iterationId]
            if ($last.ContainsKey($iteration.recurrence_id) -and $iteration.ordinal -lt $last[$iteration.recurrence_id]) {
                throw "Track '$($track.id)' moves backward in recurrence '$($iteration.recurrence_id)'."
            }
            $last[$iteration.recurrence_id] = $iteration.ordinal
        }
    }

    $seenIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $semanticTransitions = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $transitions = @()
    $rawTransitions = $Data['transitions']
    Assert-OccurrenceList $rawTransitions 'occurrences.transitions'
    $index = 0
    foreach ($item in @($rawTransitions)) {
        $context = "transitions[$index]"
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('id', 'source_occurrence_id', 'target_occurrence_id', 'transition_kind', 'transition_profile', 'recurrence_id', 'track_ids', 'certainty') $context
        $id = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' $context) "$context.id"
        if (-not $seenIds.Add($id)) {
            throw "$context.id duplicates '$id'."
        }
        $sourceId = Get-RequiredOccurrenceString $item 'source_occurrence_id' $context
        $targetId = Get-RequiredOccurrenceString $item 'target_occurrence_id' $context
        if (-not $occurrences.Contains($sourceId) -or -not $occurrences.Contains($targetId)) {
            throw "$context must reference known source and target occurrences."
        }
        if ($sourceId -ceq $targetId) {
            throw "$context source and target occurrences must differ."
        }
        $kind = Get-RequiredOccurrenceString $item 'transition_kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.transition-kind' $kind "$context.transition_kind"
        $profile = Get-RequiredOccurrenceString $item 'transition_profile' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.transition-profile' $profile "$context.transition_profile"
        if (-not $SchemaPacks.transition_profiles.ContainsKey($kind) -or $SchemaPacks.transition_profiles[$kind] -cne $profile) {
            throw "$context.transition_kind/transition_profile is not a declared typed mapping."
        }
        $recurrenceId = Get-OptionalOccurrenceString $item 'recurrence_id' $context
        if ($null -ne $recurrenceId -and -not $recurrences.Contains($recurrenceId)) {
            throw "$context.recurrence_id references unknown recurrence '$recurrenceId'."
        }
        $trackIds = @(Get-OccurrenceStringList $item 'track_ids' $context)
        foreach ($trackId in $trackIds) {
            if (-not $tracks.Contains($trackId)) {
                throw "$context.track_ids references unknown track '$trackId'."
            }
            $trackOccurrences = @($tracks[$trackId].occurrence_ids)
            $sourceIndex = [Array]::IndexOf($trackOccurrences, $sourceId)
            $targetIndex = [Array]::IndexOf($trackOccurrences, $targetId)
            if ($sourceIndex -lt 0 -or $targetIndex -lt 0) {
                throw "$context endpoints must both appear on track '$trackId'."
            }
            if (
                @($trackOccurrences | Where-Object { $_ -ceq $sourceId }).Count -ne 1 -or
                @($trackOccurrences | Where-Object { $_ -ceq $targetId }).Count -ne 1
            ) {
                throw "$context endpoints must each appear exactly once on track '$trackId'; participation-relative transitions are not available."
            }
            if ($sourceIndex -ge $targetIndex) {
                throw "$context must advance in declared track order on '$trackId'."
            }
        }
        $certainty = Get-RequiredOccurrenceString $item 'certainty' $context
        Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
        $transition = [pscustomobject]@{id=$id
            source_occurrence_id=$sourceId
            target_occurrence_id=$targetId
            transition_kind=$kind
            transition_profile=$profile
            recurrence_id=$recurrenceId
            track_ids=$trackIds
            certainty=$certainty
        }
        Assert-OccurrenceTransitionProfile $transition $occurrences $iterations $recurrences $branches $Chronology $context
        $semanticKey = "$sourceId|$targetId|$kind|$profile|$recurrenceId|$(@($trackIds|Sort-Object) -join ',')"
        if (-not $semanticTransitions.Add($semanticKey)) {
            throw "$context duplicates an existing semantic transition."
        }
        $transitions += $transition
        $index++
    }
    foreach ($branch in @($branches.Values)) {
        if ($null -eq $branch.parent_branch_id) {
            continue
        }
        $matches = @($transitions | Where-Object { $_.transition_profile -ceq 'branch-fork' -and $occurrences[$_.target_occurrence_id].branch_id -ceq $branch.id })
        if ($matches.Count -ne 1) {
            throw "branches.$($branch.id) must have exactly one matching branch-fork transition."
        }
    }

    $causal = @()
    $semanticCausal = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawCausal = $Data['causal_relations']
    Assert-OccurrenceList $rawCausal 'occurrences.causal_relations'
    $index = 0
    foreach ($item in @($rawCausal)) {
        $context = "causal_relations[$index]"
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('id', 'source_occurrence_id', 'relation_type', 'target_occurrence_id', 'certainty') $context
        $id = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' $context) "$context.id"
        if (-not $seenIds.Add($id)) {
            throw "$context.id duplicates '$id'."
        }
        $sourceId = Get-RequiredOccurrenceString $item 'source_occurrence_id' $context
        $targetId = Get-RequiredOccurrenceString $item 'target_occurrence_id' $context
        if (-not $occurrences.Contains($sourceId) -or -not $occurrences.Contains($targetId)) {
            throw "$context must reference known source and target occurrences."
        }
        $kind = Get-RequiredOccurrenceString $item 'relation_type' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.causal-relation-type' $kind "$context.relation_type"
        if (-not $semanticCausal.Add("$sourceId|$kind|$targetId")) {
            throw "$context duplicates an existing semantic causal relation."
        }
        $certainty = Get-RequiredOccurrenceString $item 'certainty' $context
        Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
        $causal += [pscustomobject]@{id=$id
            source_occurrence_id=$sourceId
            relation_type=$kind
            target_occurrence_id=$targetId
            certainty=$certainty
        }
        $index++
    }

    $outcomes = @()
    $outcomeMap = [ordered]@{}
    $semanticOutcomes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawOutcomes = $Data['outcomes']
    Assert-OccurrenceList $rawOutcomes 'occurrences.outcomes'
    $index = 0
    foreach ($item in @($rawOutcomes)) {
        $context = "outcomes[$index]"
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('id', 'occurrence_id', 'subject_type', 'subject_id', 'outcome_kind', 'result_target_type', 'result_target_id', 'certainty') $context
        $id = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' $context) "$context.id"
        if (-not $seenIds.Add($id)) {
            throw "$context.id duplicates '$id'."
        }
        $occurrenceId = Get-RequiredOccurrenceString $item 'occurrence_id' $context
        if (-not $occurrences.Contains($occurrenceId)) {
            throw "$context.occurrence_id references unknown occurrence '$occurrenceId'."
        }
        $subjectType = Get-RequiredOccurrenceString $item 'subject_type' $context
        $subjectId = Get-RequiredOccurrenceString $item 'subject_id' $context
        if ($null -eq $SubjectTargets -or -not $SubjectTargets.Contains($subjectType) -or @($SubjectTargets[$subjectType]) -cnotcontains $subjectId) {
            throw "$context references unknown subject '$subjectType`:$subjectId'."
        }
        $kind = Get-RequiredOccurrenceString $item 'outcome_kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.outcome-kind' $kind "$context.outcome_kind"
        $resultType = Get-OptionalOccurrenceString $item 'result_target_type' $context
        $resultId = Get-OptionalOccurrenceString $item 'result_target_id' $context
        if (($null -eq $resultType) -ne ($null -eq $resultId)) {
            throw "$context must set both result target fields, or neither."
        }
        $resultTargetArguments = @(
            $resultType
            $resultId
            $branches
            $templates
            $patterns
            $recurrences
            $iterations
            $occurrences
            $tracks
            @{}
            @{}
            @{}
            $PayloadTargets
            $schedules
            $phases
        )
        if ($null -ne $resultType -and -not (Test-OccurrenceTarget @resultTargetArguments)) {
            throw "$context references unknown result target '$resultType`:$resultId'."
        }
        $certainty = Get-RequiredOccurrenceString $item 'certainty' $context
        Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
        if (-not $semanticOutcomes.Add("$occurrenceId|$subjectType|$subjectId|$kind|$resultType|$resultId")) {
            throw "$context duplicates an existing semantic occurrence outcome."
        }
        $record = [pscustomobject]@{id=$id
            occurrence_id=$occurrenceId
            subject_type=$subjectType
            subject_id=$subjectId
            outcome_kind=$kind
            result_target_type=$resultType
            result_target_id=$resultId
            certainty=$certainty
        }
        $outcomes += $record
        $outcomeMap[$id] = $record
        $index++
    }
    for ($left = 0; $left -lt $outcomes.Count; $left++) {
        for ($right = $left + 1; $right -lt $outcomes.Count; $right++) {
            $a = $outcomes[$left]
            $b = $outcomes[$right]
            if (
                $a.occurrence_id -ceq $b.occurrence_id -and
                $a.subject_type -ceq $b.subject_type -and
                $a.subject_id -ceq $b.subject_id -and
                $a.result_target_type -ceq $b.result_target_type -and
                $a.result_target_id -ceq $b.result_target_id
            ) {
                $pair = @([string]$a.outcome_kind, [string]$b.outcome_kind) | Sort-Object
                $pairId = "$($pair[0])|$($pair[1])"
                if ($SchemaPacks.outcome_incompatibilities.ContainsKey($pairId)) {
                    throw "Outcome '$($b.id)' kind '$($b.outcome_kind)' is incompatible with outcome '$($a.id)' kind '$($a.outcome_kind)'."
                }
            }
        }
    }

    $rawRules = $Data['rules']
    Assert-OccurrenceList $rawRules 'occurrences.rules'
    $ruleIds = [ordered]@{}
    foreach ($item in @($rawRules)) {
        $id = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' 'rules') 'rules.id'
        if ($ruleIds.Contains($id)) {
            throw "rules.id duplicates '$id'."
        }
        $ruleIds[$id] = $true
    }
    $rawStates = $Data['state_transitions']
    Assert-OccurrenceList $rawStates 'occurrences.state_transitions'
    $stateIds = [ordered]@{}
    foreach ($item in @($rawStates)) {
        $id = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' 'state_transitions') 'state_transitions.id'
        if ($stateIds.Contains($id)) {
            throw "state_transitions.id duplicates '$id'."
        }
        $stateIds[$id] = $true
    }
    $rules = @()
    $ruleMap = [ordered]@{}
    $nestedRuleIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $semanticRules = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $index = 0
    foreach ($item in @($rawRules)) {
        $context = "rules[$index]"
        Assert-OccurrenceMap $item $context
        $ruleKeys = @(
            'id'
            'label'
            'pattern_id'
            'rule_kind'
            'condition_logic'
            'applicability'
            'priority'
            'resolution_group'
            'selection_mode'
            'override_mode'
            'conditions'
            'effects'
        )
        Assert-KnowledgeMapKeys $item $ruleKeys $context
        $id = Get-RequiredOccurrenceString $item 'id' $context
        if (-not $seenIds.Add($id)) {
            throw "$context.id duplicates '$id'."
        }
        $patternId = Get-RequiredOccurrenceString $item 'pattern_id' $context
        if (-not $patterns.Contains($patternId)) {
            throw "$context.pattern_id references unknown recurrence pattern '$patternId'."
        }
        $kind = Get-RequiredOccurrenceString $item 'rule_kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-kind' $kind "$context.rule_kind"
        $logic = Get-RequiredOccurrenceString $item 'condition_logic' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-condition-logic' $logic "$context.condition_logic"
        $app = $item['applicability']
        Assert-OccurrenceMap $app "$context.applicability"
        $applicabilityKeys = @(
            'application_level'
            'recurrence_ids'
            'phase_ids'
            'branch_ids'
            'min_iteration_ordinal'
            'max_iteration_ordinal'
            'chronology_window'
            'effective_window'
        )
        Assert-KnowledgeMapKeys $app $applicabilityKeys "$context.applicability"
        $level = Get-RequiredOccurrenceString $app 'application_level' "$context.applicability"
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-application-level' $level "$context.applicability.application_level"
        $appRecurrences = @(Get-OccurrenceStringList $app 'recurrence_ids' "$context.applicability")
        $appPhases = @(Get-OccurrenceStringList $app 'phase_ids' "$context.applicability")
        $appBranches = @(Get-OccurrenceStringList $app 'branch_ids' "$context.applicability")
        foreach ($recurrenceId in $appRecurrences) {
            if (-not $recurrences.Contains($recurrenceId) -or $recurrences[$recurrenceId].pattern_id -cne $patternId) {
                throw "$context.applicability.recurrence_ids references incompatible recurrence '$recurrenceId'."
            }
        }
        foreach ($phaseId in $appPhases) {
            if (-not $phases.Contains($phaseId) -or $recurrences[$phases[$phaseId].recurrence_id].pattern_id -cne $patternId) {
                throw "$context.applicability.phase_ids references incompatible phase '$phaseId'."
            }
        }
        foreach ($branchId in $appBranches) {
            if (-not $branches.Contains($branchId)) {
                throw "$context.applicability.branch_ids references unknown branch '$branchId'."
            }
        }
        $minimum = Get-OptionalOccurrenceNonnegativeInteger $app 'min_iteration_ordinal' "$context.applicability"
        $maximum = Get-OptionalOccurrenceNonnegativeInteger $app 'max_iteration_ordinal' "$context.applicability"
        if ($minimum -eq 0 -or $maximum -eq 0 -or ($null -ne $minimum -and $null -ne $maximum -and $minimum -gt $maximum)) {
            throw "$context.applicability iteration bounds must be positive and ordered."
        }
        $chronologyWindow = $null
        $rawWindow = $app['chronology_window']
        if ($null -ne $rawWindow) {
            Assert-OccurrenceMap $rawWindow "$context.applicability.chronology_window"
            Assert-KnowledgeMapKeys $rawWindow @('start_position_id', 'end_position_id') "$context.applicability.chronology_window"
            $start = Get-OptionalOccurrenceString $rawWindow 'start_position_id' "$context.applicability.chronology_window"
            $end = Get-OptionalOccurrenceString $rawWindow 'end_position_id' "$context.applicability.chronology_window"
            if ($null -eq $start -and $null -eq $end) {
                throw "$context.applicability.chronology_window requires at least one chronology position."
            }
            foreach ($positionId in @($start, $end)) {
                if ($null -ne $positionId -and -not $Chronology.positions.Contains($positionId)) {
                    throw "$context.applicability.chronology_window references unknown position '$positionId'."
                }
            }
            if ($null -ne $start -and $null -ne $end -and (Get-KnowledgeChronologyComparison $Chronology $start $end) -ceq 'after') {
                throw "$context.applicability.chronology_window is reversed."
            }
            $chronologyWindow = [pscustomobject]@{start_position_id=$start
                end_position_id=$end
            }
        }
        $effectiveWindow = ConvertTo-KnowledgeTemporalWindow $app 'effective_window' "$context.applicability" $SchemaPacks
        if ($level -ceq 'pattern-default' -and $appRecurrences.Count -gt 0) {
            throw "$context pattern-default rules cannot restrict recurrence_ids."
        }
        if ($level -ceq 'execution-override' -and $appRecurrences.Count -eq 0) {
            throw "$context execution-override rules require recurrence_ids."
        }
        $priority = Get-OptionalOccurrenceNonnegativeInteger $item 'priority' $context
        if ($null -eq $priority) {
            throw "$context.priority must be a nonnegative integer."
        }
        $group = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'resolution_group' $context) "$context.resolution_group"
        $selection = Get-RequiredOccurrenceString $item 'selection_mode' $context
        $override = Get-RequiredOccurrenceString $item 'override_mode' $context
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-selection-mode' $selection "$context.selection_mode"
        Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-override-mode' $override "$context.override_mode"
        if ($override -ceq 'replace-group' -and $level -cne 'execution-override') {
            throw "$context.override_mode 'replace-group' requires an execution-override rule."
        }
        $conditions = @()
        $conditionSemanticsInRule = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $rawConditions = $item['conditions']
        Assert-OccurrenceList $rawConditions "$context.conditions"
        if (@($rawConditions).Count -eq 0) {
            throw "$context.conditions must be non-empty."
        }
        foreach ($condition in @($rawConditions)) {
            $conditionContext = "$context.conditions"
            $conditionKeys = @(
                'id'
                'condition_kind'
                'target_type'
                'target_id'
                'expected_value'
                'subject_type'
                'subject_id'
                'state_kind'
                'track_id'
                'comparison_value'
            )
            Assert-KnowledgeMapKeys $condition $conditionKeys $conditionContext
            $conditionId = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $condition 'id' $conditionContext) "$conditionContext.id"
            if (-not $nestedRuleIds.Add($conditionId)) {
                throw "$context condition ID duplicates '$conditionId'."
            }
            $conditionKind = Get-RequiredOccurrenceString $condition 'condition_kind' $conditionContext
            Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-condition-kind' $conditionKind "$conditionContext.condition_kind"
            $targetType = Get-RequiredOccurrenceString $condition 'target_type' $conditionContext
            $targetId = Get-RequiredOccurrenceString $condition 'target_id' $conditionContext
            $expected = Get-RequiredOccurrenceString $condition 'expected_value' $conditionContext
            $subjectType = Get-OptionalOccurrenceString $condition 'subject_type' $conditionContext
            $subjectId = Get-OptionalOccurrenceString $condition 'subject_id' $conditionContext
            $stateKind = Get-OptionalOccurrenceString $condition 'state_kind' $conditionContext
            $trackId = Get-OptionalOccurrenceString $condition 'track_id' $conditionContext
            $comparison = Get-OptionalOccurrenceNonnegativeInteger $condition 'comparison_value' $conditionContext
            if (($null -eq $subjectType) -ne ($null -eq $subjectId)) {
                throw "$conditionContext must set both subject fields, or neither."
            }
            if ($null -ne $subjectType -and ($null -eq $SubjectTargets -or -not $SubjectTargets.Contains($subjectType) -or @($SubjectTargets[$subjectType]) -cnotcontains $subjectId)) {
                throw "$conditionContext references unknown subject '$subjectType`:$subjectId'."
            }
            $conditionTargetArguments = @(
                $targetType
                $targetId
                $branches
                $templates
                $patterns
                $recurrences
                $iterations
                $occurrences
                $tracks
                $outcomeMap
                $ruleIds
                $stateIds
                $PayloadTargets
                $schedules
                $phases
            )
            if (-not (Test-OccurrenceTarget @conditionTargetArguments)) {
                throw "$conditionContext references unknown target '$targetType`:$targetId'."
            }
            if ($conditionKind -ceq 'occurrence-reached') {
                if ($targetType -cne 'occurrence-template' -or $expected -cne 'occurred' -or $null -ne $subjectType -or $null -ne $stateKind -or $null -ne $trackId -or $null -ne $comparison) {
                    throw "$conditionContext occurrence-reached condition shape is invalid."
                }
                Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-condition-value' $expected "$conditionContext.expected_value"
            }
            elseif ($conditionKind -ceq 'occurrence-outcome') {
                if ($targetType -cne 'occurrence-template' -or $null -eq $subjectType -or $null -ne $stateKind -or $null -ne $trackId -or $null -ne $comparison) {
                    throw "$conditionContext occurrence-outcome condition shape is invalid."
                }
                Assert-OccurrencePackValue $SchemaPacks 'occurrence.outcome-kind' $expected "$conditionContext.expected_value"
            }
            elseif ($conditionKind -ceq 'state-availability') {
                if (
                    $null -eq $subjectType -or
                    $null -eq $stateKind -or
                    $null -eq $trackId -or
                    $null -ne $comparison -or
                    -not $tracks.Contains($trackId) -or
                    $tracks[$trackId].subject_type -cne $subjectType -or
                    $tracks[$trackId].subject_id -cne $subjectId
                ) {
                    throw "$conditionContext state-availability condition shape or track subject is invalid."
                }
                Assert-OccurrencePackValue $SchemaPacks 'state.availability-status' $expected "$conditionContext.expected_value"
                Assert-OccurrencePackValue $SchemaPacks 'state.state-kind' $stateKind "$conditionContext.state_kind"
            }
            elseif ($conditionKind -ceq 'iteration-ordinal') {
                if ($targetType -cne 'recurrence-pattern' -or $null -eq $comparison -or $comparison -lt 1 -or $null -ne $subjectType -or $null -ne $stateKind -or $null -ne $trackId) {
                    throw "$conditionContext iteration-ordinal condition shape is invalid."
                }
                Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-comparison' $expected "$conditionContext.expected_value"
                if ($targetId -cne $patternId) {
                    throw "$conditionContext iteration-ordinal condition must target owning pattern '$patternId'."
                }
            }
            elseif ($conditionKind -ceq 'schedule-due') {
                if ($targetType -cne 'recurrence-schedule' -or $expected -cne 'due' -or $null -ne $subjectType -or $null -ne $stateKind -or $null -ne $trackId -or $null -ne $comparison) {
                    throw "$conditionContext schedule-due condition shape is invalid."
                }
                Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-condition-value' $expected "$conditionContext.expected_value"
                if ($schedules[$targetId].pattern_id -cne $patternId) {
                    throw "$conditionContext schedule must belong to owning pattern '$patternId'."
                }
            }
            $conditionSemantic = "$conditionKind|$targetType|$targetId|$expected|$subjectType|$subjectId|$stateKind|$trackId|$comparison"
            if (-not $conditionSemanticsInRule.Add($conditionSemantic)) {
                throw "$conditionContext duplicates a semantic condition within its rule."
            }
            $conditions += [pscustomobject]@{id=$conditionId
                condition_kind=$conditionKind
                target_type=$targetType
                target_id=$targetId
                expected_value=$expected
                subject_type=$subjectType
                subject_id=$subjectId
                state_kind=$stateKind
                track_id=$trackId
                comparison_value=$comparison
            }
        }
        $effects = @()
        $effectSemanticsInRule = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $rawEffects = $item['effects']
        Assert-OccurrenceList $rawEffects "$context.effects"
        if (@($rawEffects).Count -eq 0) {
            throw "$context.effects must be non-empty."
        }
        foreach ($effect in @($rawEffects)) {
            Assert-KnowledgeMapKeys $effect @('id', 'effect_kind', 'target_type', 'target_id') "$context.effects"
            $effectId = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $effect 'id' "$context.effects") "$context.effects.id"
            if (-not $nestedRuleIds.Add($effectId)) {
                throw "$context effect ID duplicates '$effectId'."
            }
            $effectKind = Get-RequiredOccurrenceString $effect 'effect_kind' "$context.effects"
            Assert-OccurrencePackValue $SchemaPacks 'occurrence.rule-effect-kind' $effectKind "$context.effects.effect_kind"
            $targetType = Get-RequiredOccurrenceString $effect 'target_type' "$context.effects"
            $targetId = Get-RequiredOccurrenceString $effect 'target_id' "$context.effects"
            if (-not $SchemaPacks.effect_target_compatibilities.ContainsKey("$effectKind|$targetType")) {
                throw "$context.effects.effect_kind/target_type is not a declared typed compatibility."
            }
            if (-not $SchemaPacks.rule_effect_compatibilities.ContainsKey("$kind|$effectKind")) {
                throw "$context.effects.rule_kind/effect_kind is not a declared typed compatibility."
            }
            $effectTargetArguments = @(
                $targetType
                $targetId
                $branches
                $templates
                $patterns
                $recurrences
                $iterations
                $occurrences
                $tracks
                $outcomeMap
                $ruleIds
                $stateIds
                $PayloadTargets
                $schedules
                $phases
            )
            if (-not (Test-OccurrenceTarget @effectTargetArguments)) {
                throw "$context effect references unknown target '$targetType`:$targetId'."
            }
            if ($targetType -ceq 'recurrence-pattern') {
                $declaredScope = $SchemaPacks.effect_policies[$effectKind].recurrence_pattern_scope
                if ($declaredScope -ceq 'owning-pattern' -and $targetId -cne $patternId) {
                    throw "$context.effects effect kind '$effectKind' must target owning pattern '$patternId'."
                }
            }
            $effectSemantic = "$effectKind|$targetType|$targetId"
            if (-not $effectSemanticsInRule.Add($effectSemantic)) {
                throw "$context.effects duplicates a semantic effect within its rule."
            }
            $effects += [pscustomobject]@{id=$effectId
                effect_kind=$effectKind
                target_type=$targetType
                target_id=$targetId
            }
        }
        $applicability = [pscustomobject]@{application_level=$level
            recurrence_ids=$appRecurrences
            phase_ids=$appPhases
            branch_ids=$appBranches
            min_iteration_ordinal=$minimum
            max_iteration_ordinal=$maximum
            chronology_window=$chronologyWindow
            effective_window=$effectiveWindow
        }
        $chronologySemantic = $(if ($null -eq $chronologyWindow) {
                ''
            }
            else {
                "$($chronologyWindow.start_position_id),$($chronologyWindow.end_position_id)"
            })
        $temporalSemantic = $(if ($null -eq $effectiveWindow) {
                ''
            }
            else {
                $effectiveWindow | ConvertTo-Json -Compress -Depth 5
            })
        $conditionSemantics = @(
            $conditions | ForEach-Object {
                @(
                    $_.condition_kind
                    $_.target_type
                    $_.target_id
                    $_.expected_value
                    $_.subject_type
                    $_.subject_id
                    $_.state_kind
                    $_.track_id
                    $_.comparison_value
                ) -join '|'
            } | Sort-Object
        ) -join ';'
        $effectSemantics = @($effects | ForEach-Object { "$($_.effect_kind)|$($_.target_type)|$($_.target_id)" } | Sort-Object) -join ';'
        $semantic = @(
            $patternId
            $kind
            $logic
            $level
            (@($appRecurrences | Sort-Object) -join ',')
            (@($appPhases | Sort-Object) -join ',')
            (@($appBranches | Sort-Object) -join ',')
            $minimum
            $maximum
            $chronologySemantic
            $temporalSemantic
            $priority
            $group
            $selection
            $override
            $conditionSemantics
            $effectSemantics
        ) -join '|'
        if (-not $semanticRules.Add($semantic)) {
            throw "$context duplicates an existing semantic recurrence rule."
        }
        $record = [pscustomobject]@{id=$id
            label=Get-RequiredOccurrenceString $item 'label' $context
            pattern_id=$patternId
            rule_kind=$kind
            condition_logic=$logic
            applicability=$applicability
            priority=$priority
            resolution_group=$group
            selection_mode=$selection
            override_mode=$override
            conditions=@($conditions)
            effects=@($effects)
        }
        $rules += $record
        $ruleMap[$id] = $record
        $index++
    }

    $states = @()
    $stateMap = [ordered]@{}
    $sourceIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $semanticStates = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $index = 0
    foreach ($item in @($rawStates)) {
        $context = "state_transitions[$index]"
        Assert-OccurrenceMap $item $context
        $stateTransitionKeys = @(
            'id'
            'subject_type'
            'subject_id'
            'payload_target_type'
            'payload_target_id'
            'state_kind'
            'change_kind'
            'change_profile'
            'mechanism'
            'prior_availability'
            'resulting_availability'
            'prior_attitude'
            'resulting_attitude'
            'completeness'
            'activation_occurrence_id'
            'condition_rule_id'
            'track_ids'
            'source_targets'
            'certainty'
        )
        Assert-KnowledgeMapKeys $item $stateTransitionKeys $context
        $id = Get-RequiredOccurrenceString $item 'id' $context
        if (-not $seenIds.Add($id)) {
            throw "$context.id duplicates '$id'."
        }
        $subjectType = Get-RequiredOccurrenceString $item 'subject_type' $context
        $subjectId = Get-RequiredOccurrenceString $item 'subject_id' $context
        if ($null -eq $SubjectTargets -or -not $SubjectTargets.Contains($subjectType) -or @($SubjectTargets[$subjectType]) -cnotcontains $subjectId) {
            throw "$context references unknown subject '$subjectType`:$subjectId'."
        }
        $payloadType = Get-RequiredOccurrenceString $item 'payload_target_type' $context
        $payloadId = Get-RequiredOccurrenceString $item 'payload_target_id' $context
        $payloadTargetArguments = @(
            $payloadType
            $payloadId
            $branches
            $templates
            $patterns
            $recurrences
            $iterations
            $occurrences
            $tracks
            $outcomeMap
            $ruleMap
            $stateIds
            $PayloadTargets
            $schedules
            $phases
        )
        if (-not (Test-OccurrenceTarget @payloadTargetArguments)) {
            throw "$context references unknown payload '$payloadType`:$payloadId'."
        }
        $stateKind = Get-RequiredOccurrenceString $item 'state_kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'state.state-kind' $stateKind "$context.state_kind"
        $changeKind = Get-RequiredOccurrenceString $item 'change_kind' $context
        Assert-OccurrencePackValue $SchemaPacks 'state.change-kind' $changeKind "$context.change_kind"
        $profile = Get-RequiredOccurrenceString $item 'change_profile' $context
        Assert-OccurrencePackValue $SchemaPacks 'state.change-profile' $profile "$context.change_profile"
        if (-not $SchemaPacks.state_change_profiles.ContainsKey($changeKind) -or $SchemaPacks.state_change_profiles[$changeKind] -cne $profile) {
            throw "$context.change_kind/change_profile is not a declared typed mapping."
        }
        $mechanism = Get-RequiredOccurrenceString $item 'mechanism' $context
        Assert-OccurrencePackValue $SchemaPacks 'state.mechanism' $mechanism "$context.mechanism"
        $prior = Get-RequiredOccurrenceString $item 'prior_availability' $context
        $result = Get-RequiredOccurrenceString $item 'resulting_availability' $context
        Assert-OccurrencePackValue $SchemaPacks 'state.availability-status' $prior "$context.prior_availability"
        Assert-OccurrencePackValue $SchemaPacks 'state.availability-status' $result "$context.resulting_availability"
        $validProfile = (
            (
                $profile -ceq 'acquire' -and
                $prior -in @('unavailable', 'latent') -and
                $result -in @('partial', 'available')
            ) -or
            ($profile -ceq 'preserve' -and $prior -ceq $result) -or
            ($profile -ceq 'remove' -and $result -in @('unavailable', 'inaccessible')) -or
            (
                $profile -ceq 'restore' -and
                $prior -in @('unavailable', 'inaccessible') -and
                $result -in @('partial', 'available')
            ) -or
            ($profile -in @('supply', 'combine', 'derive') -and $result -in @('partial', 'available')) -or
            (
                $profile -ceq 'activate' -and
                $prior -in @('latent', 'inaccessible') -and
                $result -in @('partial', 'available')
            ) -or
            ($profile -ceq 'invalidate' -and $result -ceq 'invalidated')
        )
        if (-not $validProfile) {
            throw "$context state profile '$profile' is incompatible with '$prior' -> '$result'."
        }
        $priorAttitude = Get-OptionalOccurrenceString $item 'prior_attitude' $context
        $resultAttitude = Get-OptionalOccurrenceString $item 'resulting_attitude' $context
        if (($null -eq $priorAttitude) -ne ($null -eq $resultAttitude)) {
            throw "$context must set both epistemic attitudes, or neither."
        }
        if ($null -ne $priorAttitude) {
            Assert-OccurrencePackValue $SchemaPacks 'state.epistemic-attitude' $priorAttitude "$context.prior_attitude"
            Assert-OccurrencePackValue $SchemaPacks 'state.epistemic-attitude' $resultAttitude "$context.resulting_attitude"
        }
        $completeness = Get-RequiredOccurrenceString $item 'completeness' $context
        Assert-OccurrencePackValue $SchemaPacks 'state.completeness' $completeness "$context.completeness"
        $activationId = Get-RequiredOccurrenceString $item 'activation_occurrence_id' $context
        if (-not $occurrences.Contains($activationId)) {
            throw "$context.activation_occurrence_id references unknown occurrence '$activationId'."
        }
        $conditionRuleId = Get-OptionalOccurrenceString $item 'condition_rule_id' $context
        if ($null -ne $conditionRuleId -and -not $ruleMap.Contains($conditionRuleId)) {
            throw "$context.condition_rule_id references unknown rule '$conditionRuleId'."
        }
        $trackIds = @(Get-OccurrenceStringList $item 'track_ids' $context)
        if ($trackIds.Count -eq 0) {
            throw "$context.track_ids must be non-empty."
        }
        foreach ($trackId in $trackIds) {
            if (-not $tracks.Contains($trackId)) {
                throw "$context references unknown track '$trackId'."
            }
            $track = $tracks[$trackId]
            if ($track.subject_type -cne $subjectType -or $track.subject_id -cne $subjectId) {
                throw "$context subject must match track '$trackId' subject."
            }
            if ($track.occurrence_ids -cnotcontains $activationId) {
                throw "$context activation must appear on track '$trackId'."
            }
            if (@($track.occurrence_ids | Where-Object { $_ -ceq $activationId }).Count -ne 1) {
                throw "$context activation appears more than once on track '$trackId'; participation-relative state transitions are not available."
            }
        }
        $sources = @()
        $rawSources = $item['source_targets']
        Assert-OccurrenceList $rawSources "$context.source_targets"
        foreach ($source in @($rawSources)) {
            $sourceId = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $source 'id' "$context.source_targets") "$context.source_targets.id"
            if (-not $sourceIds.Add($sourceId)) {
                throw "$context source ID duplicates '$sourceId'."
            }
            $sourceType = Get-RequiredOccurrenceString $source 'target_type' "$context.source_targets"
            $sourceTargetId = Get-RequiredOccurrenceString $source 'target_id' "$context.source_targets"
            $sourceTargetArguments = @(
                $sourceType
                $sourceTargetId
                $branches
                $templates
                $patterns
                $recurrences
                $iterations
                $occurrences
                $tracks
                $outcomeMap
                $ruleMap
                $stateIds
                $PayloadTargets
                $schedules
                $phases
            )
            if (-not (Test-OccurrenceTarget @sourceTargetArguments)) {
                throw "$context source references unknown target '$sourceType`:$sourceTargetId'."
            }
            $role = Get-RequiredOccurrenceString $source 'role' "$context.source_targets"
            Assert-OccurrencePackValue $SchemaPacks 'state.source-role' $role "$context.source_targets.role"
            $sources += [pscustomobject]@{id=$sourceId
                target_type=$sourceType
                target_id=$sourceTargetId
                role=$role
            }
        }
        $certainty = Get-RequiredOccurrenceString $item 'certainty' $context
        Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
        $semantic = @(
            $subjectType
            $subjectId
            $payloadType
            $payloadId
            $stateKind
            $changeKind
            $profile
            $mechanism
            $prior
            $result
            $priorAttitude
            $resultAttitude
            $completeness
            $activationId
            $conditionRuleId
            (@($trackIds | Sort-Object) -join ',')
        ) -join '|'
        if (-not $semanticStates.Add($semantic)) {
            throw "$context duplicates an existing semantic state transition."
        }
        $record = [pscustomobject]@{id=$id
            subject_type=$subjectType
            subject_id=$subjectId
            payload_target_type=$payloadType
            payload_target_id=$payloadId
            state_kind=$stateKind
            change_kind=$changeKind
            change_profile=$profile
            mechanism=$mechanism
            prior_availability=$prior
            resulting_availability=$result
            prior_attitude=$priorAttitude
            resulting_attitude=$resultAttitude
            completeness=$completeness
            activation_occurrence_id=$activationId
            condition_rule_id=$conditionRuleId
            track_ids=$trackIds
            source_targets=@($sources)
            certainty=$certainty
        }
        $states += $record
        $stateMap[$id] = $record
        $index++
    }
    foreach ($track in @($tracks.Values)) {
        $chains = @{}
        foreach ($state in @($states | Where-Object { $_.track_ids -ccontains $track.id })) {
            $key = "$($state.subject_type)|$($state.subject_id)|$($state.payload_target_type)|$($state.payload_target_id)|$($state.state_kind)"
            if (-not $chains.ContainsKey($key)) {
                $chains[$key] = @()
            }
            $chains[$key] = @($chains[$key]) + $state
        }
        foreach ($members in @($chains.Values)) {
            $ordered = @($members | Sort-Object { [Array]::IndexOf(@($track.occurrence_ids), $_.activation_occurrence_id) })
            for ($i = 1; $i -lt $ordered.Count; $i++) {
                if ($ordered[$i - 1].activation_occurrence_id -ceq $ordered[$i].activation_occurrence_id) {
                    throw "State chain on track '$($track.id)' has multiple transitions at one occurrence."
                }
                if ($ordered[$i - 1].resulting_availability -cne $ordered[$i].prior_availability -or $ordered[$i - 1].resulting_attitude -cne $ordered[$i].prior_attitude) {
                    throw "State transition '$($ordered[$i].id)' does not continue '$($ordered[$i-1].id)'."
                }
            }
        }
    }

    $carryovers = @()
    $semanticCarryovers = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawCarryovers = $Data['carryovers']
    Assert-OccurrenceList $rawCarryovers 'occurrences.carryovers'
    $index = 0
    foreach ($item in @($rawCarryovers)) {
        $context = "carryovers[$index]"
        Assert-OccurrenceMap $item $context
        Assert-KnowledgeMapKeys $item @('id', 'source_iteration_id', 'target_iteration_id', 'track_id', 'state_transition_id', 'certainty') $context
        $id = Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' $context) "$context.id"
        if (-not $seenIds.Add($id)) {
            throw "$context.id duplicates '$id'."
        }
        $sourceId = Get-RequiredOccurrenceString $item 'source_iteration_id' $context
        $targetId = Get-RequiredOccurrenceString $item 'target_iteration_id' $context
        $trackId = Get-RequiredOccurrenceString $item 'track_id' $context
        $stateId = Get-RequiredOccurrenceString $item 'state_transition_id' $context
        if (-not $iterations.Contains($sourceId) -or -not $iterations.Contains($targetId) -or -not $tracks.Contains($trackId) -or -not $stateMap.Contains($stateId)) {
            throw "$context must reference known iterations, track, and state transition."
        }
        $source = $iterations[$sourceId]
        $target = $iterations[$targetId]
        if ($source.recurrence_id -cne $target.recurrence_id -or $source.ordinal -ge $target.ordinal) {
            throw "$context must advance between iterations of the same recurrence."
        }
        $track = $tracks[$trackId]
        $trackIterationIds = @($track.occurrence_ids | ForEach-Object { $occurrences[$_].iteration_id } | Sort-Object -Unique)
        if ($trackIterationIds -cnotcontains $sourceId -or $trackIterationIds -cnotcontains $targetId) {
            throw "$context.track_id must participate in both source and target iterations."
        }
        $state = $stateMap[$stateId]
        if ($state.track_ids -cnotcontains $trackId) {
            throw "$context state transition must apply to track '$trackId'."
        }
        $sourceIndices = @()
        $targetIndices = @()
        for ($i = 0; $i -lt $track.occurrence_ids.Count; $i++) {
            $iterationId = $occurrences[$track.occurrence_ids[$i]].iteration_id
            if ($iterationId -ceq $sourceId) {
                $sourceIndices += $i
            }
            if ($iterationId -ceq $targetId) {
                $targetIndices += $i
            }
        }
        $activationIndex = [Array]::IndexOf(@($track.occurrence_ids), $state.activation_occurrence_id)
        if ($activationIndex -gt ($sourceIndices | Measure-Object -Maximum).Maximum) {
            throw "$context state transition activates after the source iteration ends."
        }
        $certainty = Get-RequiredOccurrenceString $item 'certainty' $context
        Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
        if (-not $semanticCarryovers.Add("$sourceId|$targetId|$trackId|$stateId")) {
            throw "$context duplicates an existing semantic carryover."
        }
        $carryovers += [pscustomobject]@{id=$id
            source_iteration_id=$sourceId
            target_iteration_id=$targetId
            track_id=$trackId
            state_transition_id=$stateId
            certainty=$certainty
        }
        $index++
    }

    foreach ($rawState in @($rawStates)) {
        foreach ($source in @($rawState['source_targets'])) {
            Assert-KnowledgeMapKeys $source @('id', 'target_type', 'target_id', 'role') 'state_transitions.source_targets'
        }
    }
    foreach ($carryover in @($carryovers)) {
        $track = $tracks[$carryover.track_id]
        $state = $stateMap[$carryover.state_transition_id]
        $ids = @($track.occurrence_ids)
        $activationIndex = [Array]::IndexOf($ids, $state.activation_occurrence_id)
        $targetIndices = @()
        for ($i = 0; $i -lt $ids.Count; $i++) {
            if ($occurrences[$ids[$i]].iteration_id -ceq $carryover.target_iteration_id) {
                $targetIndices += $i
            }
        }
        $targetStart = ($targetIndices | Measure-Object -Minimum).Minimum
        foreach ($candidate in @($states)) {
            if ($candidate.id -ceq $state.id -or $candidate.track_ids -cnotcontains $track.id) {
                continue
            }
            $sameChain = (
                $candidate.subject_type -ceq $state.subject_type -and
                $candidate.subject_id -ceq $state.subject_id -and
                $candidate.payload_target_type -ceq $state.payload_target_type -and
                $candidate.payload_target_id -ceq $state.payload_target_id -and
                $candidate.state_kind -ceq $state.state_kind
            )
            $candidateIndex = [Array]::IndexOf($ids, $candidate.activation_occurrence_id)
            if ($sameChain -and $candidateIndex -gt $activationIndex -and $candidateIndex -lt $targetStart) {
                throw "carryovers.$($carryover.id) state transition is superseded by '$($candidate.id)' before the target iteration begins."
            }
        }
    }
    $repetitionPolicies = [ordered]@{}
    foreach ($effectKind in $SchemaPacks.effect_policies.Keys) {
        $repetitionPolicies[$effectKind] = $SchemaPacks.effect_policies[$effectKind].repetition_policy
    }
    $globalIncompatibilities = @{}
    $sameTargetIncompatibilities = @{}
    foreach ($pairKey in $SchemaPacks.effect_incompatibilities.Keys) {
        if ($SchemaPacks.effect_incompatibilities[$pairKey] -ceq 'global') {
            $globalIncompatibilities[$pairKey] = $true
        }
        else {
            $sameTargetIncompatibilities[$pairKey] = $true
        }
    }
    return [pscustomobject]@{path=$Path
        schema_version=6
        chronology=$Chronology
        branches=$branches
        templates=$templates
        recurrence_patterns=$patterns
        recurrences=$recurrences
        iterations=$iterations
        recurrence_cardinalities=$cardinalities
        phases=$phases
        schedules=$schedules
        occurrences=$occurrences
        occurrence_participations=$participations
        tracks=$tracks
        track_entries=$trackEntries
        transitions=@($transitions)
        causal_relations=@($causal)
        outcomes=@($outcomes)
        rules=@($rules)
        state_transitions=@($states)
        carryovers=@($carryovers)
        effect_global_incompatibility_pairs=$globalIncompatibilities
        effect_same_target_incompatibility_pairs=$sameTargetIncompatibilities
        effect_repetition_policies=$repetitionPolicies
    }
}

function Get-KnowledgeOccurrenceRegistry {
    param([object]$Project, [object]$SchemaPacks, [object]$Chronology, [System.Collections.IDictionary]$SubjectTargets = $null, [System.Collections.IDictionary]$PayloadTargets = $null)
    $data = ConvertFrom-KnowledgeYamlFile $Project.occurrences_registry 6 'occurrence registry'
    return ConvertTo-KnowledgeOccurrenceRegistry $data $Project.occurrences_registry $SchemaPacks $Chronology $SubjectTargets $PayloadTargets
}
