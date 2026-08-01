$projectConfigHelper=Join-Path $PSScriptRoot 'Project-Config.ps1'
if(-not (Get-Command Get-ProjectMapValue -ErrorAction SilentlyContinue)){. $projectConfigHelper}
$schemaPackHelper=Join-Path $PSScriptRoot 'Schema-Pack-Config.ps1'
if(-not (Get-Command Get-SchemaPackAllowedValues -ErrorAction SilentlyContinue)){. $schemaPackHelper}

$script:SupportedOccurrenceSchemaVersion=2
$script:OccurrenceStableIdPattern='^[a-z0-9]+(?:-[a-z0-9]+)*$'

function Get-RequiredOccurrenceString{param([object]$Map,[string]$Key,[string]$Context);$value=Get-ProjectMapValue $Map $Key;if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw "$Context.$Key must be a non-empty string."};return $value.Trim()}
function Get-OptionalOccurrenceString{param([object]$Map,[string]$Key,[string]$Context);$value=Get-ProjectMapValue $Map $Key;if($null -eq $value){return $null};if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw "$Context.$Key must be a non-empty string or null."};return $value.Trim()}
function Get-OccurrenceStringList{
  param([object]$Map,[string]$Key,[string]$Context)
  $value=$Map[$Key];if($null -eq $value){throw "$Context.$Key must be a list."};if($value -is [string] -or $value -isnot [System.Collections.IList]){throw "$Context.$Key must be a list."}
  $result=@();$seen=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach($entry in @($value)){if($entry -isnot [string] -or [string]::IsNullOrWhiteSpace($entry) -or -not $seen.Add($entry.Trim())){throw "$Context.$Key must contain unique non-empty strings."};$result+=$entry.Trim()};return @($result)
}
function Assert-OccurrenceStableId{param([string]$Value,[string]$Context);if($Value -cnotmatch $script:OccurrenceStableIdPattern){throw "$Context must be a lowercase kebab-case stable ID: $Value"};return $Value}
function Assert-OccurrencePackValue{param([object]$Packs,[string]$Namespace,[string]$Value,[string]$Context);if(@(Get-SchemaPackAllowedValues $Packs $Namespace) -cnotcontains $Value){throw "$Context uses '$Value', which is not provided in '$Namespace'."}}
function Assert-OccurrenceMap{param([object]$Value,[string]$Context);if($Value -isnot [System.Collections.IDictionary]){throw "$Context must be a mapping."}}
function Assert-OccurrenceList{param([object]$Value,[string]$Context);if($Value -is [string] -or $Value -isnot [System.Collections.IList]){throw "$Context must be a list."}}

function Assert-OccurrenceParentAcyclic{
  param([System.Collections.IDictionary]$Items,[string]$ParentProperty,[string]$Kind)
  foreach($itemId in @($Items.Keys)){$seen=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$current=[string]$itemId;while($null -ne $current){if(-not $seen.Add($current)){throw "$Kind parent cycle includes '$current'."};$current=$Items[$current].$ParentProperty}}
}

function Get-KnowledgeOccurrencesForIteration{param([object]$Registry,[string]$IterationId);if(-not $Registry.iterations.Contains($IterationId)){throw "Unknown iteration '$IterationId'."};return @($Registry.occurrences.Values|Where-Object {$_.iteration_id -ceq $IterationId})}
function Get-KnowledgeOccurrencesAtPosition{param([object]$Registry,[string]$PositionId);return @($Registry.occurrences.Values|Where-Object {@($_.bindings|Where-Object {$_.position_id -ceq $PositionId}).Count -gt 0})}
function Get-KnowledgeOccurrencesForIterationOnTrack{
  param([object]$Registry,[string]$IterationId,[string]$TrackId)
  if(-not $Registry.iterations.Contains($IterationId)){throw "Unknown iteration '$IterationId'."}
  if(-not $Registry.tracks.Contains($TrackId)){throw "Unknown track '$TrackId'."}
  return @($Registry.tracks[$TrackId].occurrence_ids|ForEach-Object {$Registry.occurrences[$_]}|Where-Object {$_.iteration_id -ceq $IterationId})
}
function Get-KnowledgeAdjacentTrackOccurrence{
  param([object]$Registry,[string]$TrackId,[string]$OccurrenceId,[int]$Offset)
  if(-not $Registry.tracks.Contains($TrackId)){throw "Unknown track '$TrackId'."};$ids=@($Registry.tracks[$TrackId].occurrence_ids);$index=[Array]::IndexOf($ids,$OccurrenceId);if($index -lt 0){throw "Occurrence '$OccurrenceId' is not on track '$TrackId'."};$target=$index+$Offset;if($target -lt 0 -or $target -ge $ids.Count){return $null};return $Registry.occurrences[$ids[$target]]
}
function Get-KnowledgePreviousTrackOccurrence{param([object]$Registry,[string]$TrackId,[string]$OccurrenceId);return Get-KnowledgeAdjacentTrackOccurrence $Registry $TrackId $OccurrenceId -1}
function Get-KnowledgeNextTrackOccurrence{param([object]$Registry,[string]$TrackId,[string]$OccurrenceId);return Get-KnowledgeAdjacentTrackOccurrence $Registry $TrackId $OccurrenceId 1}
function Get-KnowledgePreviousBeforeIteration{
  param([object]$Registry,[string]$TrackId,[string]$IterationId)
  $items=@(Get-KnowledgeOccurrencesForIterationOnTrack $Registry $IterationId $TrackId);if($items.Count -eq 0){return $null};return Get-KnowledgePreviousTrackOccurrence $Registry $TrackId $items[0].id
}
function Get-KnowledgeNextAfterIteration{
  param([object]$Registry,[string]$TrackId,[string]$IterationId)
  $items=@(Get-KnowledgeOccurrencesForIterationOnTrack $Registry $IterationId $TrackId);if($items.Count -eq 0){return $null};return Get-KnowledgeNextTrackOccurrence $Registry $TrackId $items[-1].id
}
function Get-KnowledgeCarryoversIntoIteration{param([object]$Registry,[string]$IterationId);if(-not $Registry.iterations.Contains($IterationId)){throw "Unknown iteration '$IterationId'."};return @($Registry.carryovers|Where-Object {$_.target_iteration_id -ceq $IterationId})}
function Get-KnowledgeOccurrenceRecurrence{param([object]$Registry,[string]$OccurrenceId);if(-not $Registry.occurrences.Contains($OccurrenceId)){throw "Unknown occurrence '$OccurrenceId'."};$iterationId=$Registry.occurrences[$OccurrenceId].iteration_id;if($null -eq $iterationId){return $null};return $Registry.recurrences[$Registry.iterations[$iterationId].recurrence_id]}
function Get-KnowledgeOccurrenceProvenanceTargets{
  param([object]$Registry)
  $bindings=[ordered]@{};foreach($occurrence in @($Registry.occurrences.Values)){foreach($binding in @($occurrence.bindings)){$bindings[$binding.id]=$binding}}
  $transitions=[ordered]@{};foreach($item in @($Registry.transitions)){$transitions[$item.id]=$item};$causal=[ordered]@{};foreach($item in @($Registry.causal_relations)){$causal[$item.id]=$item};$carryovers=[ordered]@{};foreach($item in @($Registry.carryovers)){$carryovers[$item.id]=$item}
  return [ordered]@{'occurrence-branch'=$Registry.branches;'occurrence-template'=$Registry.templates;recurrence=$Registry.recurrences;'recurrence-iteration'=$Registry.iterations;occurrence=$Registry.occurrences;'occurrence-binding'=$bindings;'occurrence-track'=$Registry.tracks;'occurrence-transition'=$transitions;'causal-relation'=$causal;'iteration-carryover'=$carryovers}
}

function Test-OccurrencePayloadTarget{
  param([string]$TargetType,[string]$TargetId,[object]$Branches,[object]$Templates,[object]$Recurrences,[object]$Iterations,[object]$Occurrences,[object]$Tracks,[System.Collections.IDictionary]$ExternalTargets)
  $internal=[ordered]@{'occurrence-branch'=$Branches;'occurrence-template'=$Templates;recurrence=$Recurrences;'recurrence-iteration'=$Iterations;occurrence=$Occurrences;'occurrence-track'=$Tracks}
  if($internal.Contains($TargetType)){return $internal[$TargetType].Contains($TargetId)}
  if($null -ne $ExternalTargets -and $ExternalTargets.Contains($TargetType)){return @($ExternalTargets[$TargetType]) -ccontains $TargetId}
  return $false
}

function Assert-OccurrenceTransitionProfile{
  param([object]$Transition,[object]$Occurrences,[object]$Iterations,[object]$Branches,[string]$Context)
  $sourceOccurrence=$Occurrences[$Transition.source_occurrence_id];$targetOccurrence=$Occurrences[$Transition.target_occurrence_id]
  $sourceIteration=if($null -ne $sourceOccurrence.iteration_id){$Iterations[$sourceOccurrence.iteration_id]}else{$null}
  $targetIteration=if($null -ne $targetOccurrence.iteration_id){$Iterations[$targetOccurrence.iteration_id]}else{$null}
  $recurrenceId=$Transition.recurrence_id;$profile=$Transition.transition_profile
  if($profile -in @('ordered','jump')){
    if($null -ne $recurrenceId -and ($null -eq $sourceIteration -or $null -eq $targetIteration -or $sourceIteration.recurrence_id -cne $recurrenceId -or $targetIteration.recurrence_id -cne $recurrenceId)){throw "$Context scoped '$profile' endpoints must belong to recurrence '$recurrenceId'."};return
  }
  if($profile -ceq 'recurrence-advance'){
    if($null -eq $sourceIteration -or $null -eq $targetIteration -or $null -eq $recurrenceId){throw "$Context recurrence-advance transitions require recurrence-bound source and target iterations."}
    if($sourceIteration.recurrence_id -cne $recurrenceId -or $targetIteration.recurrence_id -cne $recurrenceId -or $sourceIteration.ordinal -ge $targetIteration.ordinal){throw "$Context recurrence-advance transition must advance iterations in recurrence '$recurrenceId'."};return
  }
  if($profile -ceq 'recurrence-exit'){
    if($null -eq $sourceIteration -or $null -eq $recurrenceId -or $sourceIteration.recurrence_id -cne $recurrenceId){throw "$Context recurrence-exit source must belong to recurrence '$recurrenceId'."}
    if($null -ne $targetIteration -and $targetIteration.recurrence_id -ceq $recurrenceId){throw "$Context recurrence-exit target must leave recurrence '$recurrenceId'."};return
  }
  if($profile -ceq 'branch-fork'){
    if($null -ne $recurrenceId -and ($null -eq $sourceIteration -or $null -eq $targetIteration -or $sourceIteration.recurrence_id -cne $recurrenceId -or $targetIteration.recurrence_id -cne $recurrenceId)){throw "$Context scoped '$profile' endpoints must belong to recurrence '$recurrenceId'."}
    $targetBranch=$Branches[$targetOccurrence.branch_id]
    if($null -eq $targetBranch.parent_branch_id -or $targetBranch.parent_branch_id -cne $sourceOccurrence.branch_id -or $targetBranch.fork_occurrence_id -cne $sourceOccurrence.id){throw "$Context branch-fork endpoints do not match the target branch lineage."};return
  }
  if($profile -ceq 'branch-merge'){
    if($null -ne $recurrenceId -and ($null -eq $sourceIteration -or $null -eq $targetIteration -or $sourceIteration.recurrence_id -cne $recurrenceId -or $targetIteration.recurrence_id -cne $recurrenceId)){throw "$Context scoped '$profile' endpoints must belong to recurrence '$recurrenceId'."}
    if($sourceOccurrence.branch_id -ceq $targetOccurrence.branch_id){throw "$Context branch-merge endpoints must belong to different branches."};return
  }
  throw "$Context uses unsupported transition profile '$profile'."
}

function ConvertTo-KnowledgeOccurrenceRegistry{
  param([object]$Data,[string]$Path,[object]$SchemaPacks,[object]$Chronology,[System.Collections.IDictionary]$SubjectTargets=$null,[System.Collections.IDictionary]$PayloadTargets=$null)
  if(-not (Test-SchemaPackCapabilityEnabled $SchemaPacks 'occurrence-recurrence-modeling')){throw "Occurrence registry requires enabled capability 'occurrence-recurrence-modeling'."}
  Assert-OccurrenceMap $Data 'Occurrence registry root';Assert-KnowledgeMapKeys $Data @('schema_version','branches','templates','recurrences','iterations','occurrences','tracks','transitions','causal_relations','carryovers') 'Occurrence registry root'
  $schemaVersion=Get-ProjectMapValue $Data 'schema_version';if($schemaVersion -isnot [int] -or $schemaVersion -ne 2){throw "Unsupported occurrence schema_version '$schemaVersion'; expected 2."}

  $rawBranches=Get-ProjectMapValue $Data 'branches';Assert-OccurrenceMap $rawBranches 'occurrences.branches';if($rawBranches.Count -eq 0){throw 'occurrences.branches cannot be empty.'};$branches=[ordered]@{}
  foreach($id in @($rawBranches.Keys)){$null=Assert-OccurrenceStableId ([string]$id) 'occurrence branch ID';$context="branches.$id";$item=$rawBranches[$id];Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('label','parent_branch_id','fork_occurrence_id') $context;$parent=Get-OptionalOccurrenceString $item 'parent_branch_id' $context;$fork=Get-OptionalOccurrenceString $item 'fork_occurrence_id' $context;if(($null -eq $parent) -ne ($null -eq $fork)){throw "$context must set both parent_branch_id and fork_occurrence_id, or neither."};$branches[$id]=[pscustomobject]@{id=[string]$id;label=Get-RequiredOccurrenceString $item 'label' $context;parent_branch_id=$parent;fork_occurrence_id=$fork}}
  foreach($branch in @($branches.Values)){if($null -ne $branch.parent_branch_id -and -not $branches.Contains($branch.parent_branch_id)){throw "branches.$($branch.id).parent_branch_id references unknown branch '$($branch.parent_branch_id)'."}};Assert-OccurrenceParentAcyclic $branches 'parent_branch_id' 'Branch'

  $rawTemplates=Get-ProjectMapValue $Data 'templates';Assert-OccurrenceMap $rawTemplates 'occurrences.templates';$templates=[ordered]@{}
  foreach($id in @($rawTemplates.Keys)){$null=Assert-OccurrenceStableId ([string]$id) 'occurrence template ID';$context="templates.$id";$item=$rawTemplates[$id];Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('label','kind','aliases') $context;$kind=Get-RequiredOccurrenceString $item 'kind' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.template-kind' $kind "$context.kind";$templates[$id]=[pscustomobject]@{id=[string]$id;label=Get-RequiredOccurrenceString $item 'label' $context;kind=$kind;aliases=@(Get-OccurrenceStringList $item 'aliases' $context)}}

  $rawRecurrences=Get-ProjectMapValue $Data 'recurrences';Assert-OccurrenceMap $rawRecurrences 'occurrences.recurrences';$recurrences=[ordered]@{}
  foreach($id in @($rawRecurrences.Keys)){$null=Assert-OccurrenceStableId ([string]$id) 'recurrence ID';$context="recurrences.$id";$item=$rawRecurrences[$id];Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('label','kind','parent_recurrence_id') $context;$kind=Get-RequiredOccurrenceString $item 'kind' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.recurrence-kind' $kind "$context.kind";$recurrences[$id]=[pscustomobject]@{id=[string]$id;label=Get-RequiredOccurrenceString $item 'label' $context;kind=$kind;parent_recurrence_id=Get-OptionalOccurrenceString $item 'parent_recurrence_id' $context}}
  foreach($item in @($recurrences.Values)){if($null -ne $item.parent_recurrence_id -and -not $recurrences.Contains($item.parent_recurrence_id)){throw "recurrences.$($item.id).parent_recurrence_id references unknown recurrence '$($item.parent_recurrence_id)'."}};Assert-OccurrenceParentAcyclic $recurrences 'parent_recurrence_id' 'Recurrence'

  $rawIterations=Get-ProjectMapValue $Data 'iterations';Assert-OccurrenceMap $rawIterations 'occurrences.iterations';$iterations=[ordered]@{};$ordinals=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach($id in @($rawIterations.Keys)){$null=Assert-OccurrenceStableId ([string]$id) 'recurrence iteration ID';$context="iterations.$id";$item=$rawIterations[$id];Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('recurrence_id','ordinal','parent_iteration_id','status') $context;$recurrenceId=Get-RequiredOccurrenceString $item 'recurrence_id' $context;if(-not $recurrences.Contains($recurrenceId)){throw "$context.recurrence_id references unknown recurrence '$recurrenceId'."};$ordinal=Get-ProjectMapValue $item 'ordinal';if($ordinal -isnot [int] -or $ordinal -lt 1){throw "$context.ordinal must be a positive integer."};if(-not $ordinals.Add("$recurrenceId|$ordinal")){throw "$context.ordinal duplicates ordinal $ordinal in '$recurrenceId'."};$status=Get-RequiredOccurrenceString $item 'status' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.iteration-status' $status "$context.status";$iterations[$id]=[pscustomobject]@{id=[string]$id;recurrence_id=$recurrenceId;ordinal=[int]$ordinal;parent_iteration_id=Get-OptionalOccurrenceString $item 'parent_iteration_id' $context;status=$status}}
  foreach($iteration in @($iterations.Values)){$parentRecurrence=$recurrences[$iteration.recurrence_id].parent_recurrence_id;if($null -eq $parentRecurrence){if($null -ne $iteration.parent_iteration_id){throw "iterations.$($iteration.id).parent_iteration_id is only valid for a nested recurrence."}}elseif($null -eq $iteration.parent_iteration_id -or -not $iterations.Contains($iteration.parent_iteration_id) -or $iterations[$iteration.parent_iteration_id].recurrence_id -cne $parentRecurrence){throw "iterations.$($iteration.id).parent_iteration_id must reference an iteration of parent recurrence '$parentRecurrence'."}}

  $rawOccurrences=Get-ProjectMapValue $Data 'occurrences';Assert-OccurrenceMap $rawOccurrences 'occurrences.occurrences';$occurrences=[ordered]@{};$bindingIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach($id in @($rawOccurrences.Keys)){
    $null=Assert-OccurrenceStableId ([string]$id) 'occurrence ID';$context="occurrences.$id";$item=$rawOccurrences[$id];Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('template_id','label','iteration_id','branch_id','bindings') $context
    $templateId=Get-RequiredOccurrenceString $item 'template_id' $context;$branchId=Get-RequiredOccurrenceString $item 'branch_id' $context;$iterationId=Get-OptionalOccurrenceString $item 'iteration_id' $context
    if(-not $templates.Contains($templateId)){throw "$context.template_id references unknown template '$templateId'."};if(-not $branches.Contains($branchId)){throw "$context.branch_id references unknown branch '$branchId'."};if($null -ne $iterationId -and -not $iterations.Contains($iterationId)){throw "$context.iteration_id references unknown iteration '$iterationId'."}
    $rawBindings=$item['bindings'];Assert-OccurrenceList $rawBindings "$context.bindings";$bindings=@();$semanticBindings=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$index=0
    foreach($rawBinding in @($rawBindings)){
      $bindingContext="$context.bindings[$index]";Assert-OccurrenceMap $rawBinding $bindingContext;Assert-KnowledgeMapKeys $rawBinding @('id','position_id','role') $bindingContext
      $bindingId=Assert-OccurrenceStableId (Get-RequiredOccurrenceString $rawBinding 'id' $bindingContext) "$bindingContext.id";if(-not $bindingIds.Add($bindingId)){throw "$bindingContext.id duplicates '$bindingId'."}
      $positionId=Get-RequiredOccurrenceString $rawBinding 'position_id' $bindingContext;if(-not $Chronology.positions.Contains($positionId)){throw "$bindingContext.position_id references unknown chronology position '$positionId'."}
      $role=Get-RequiredOccurrenceString $rawBinding 'role' $bindingContext;Assert-OccurrencePackValue $SchemaPacks 'occurrence.binding-role' $role "$bindingContext.role";if(-not $semanticBindings.Add("$positionId|$role")){throw "$context.bindings duplicates '$role' binding to '$positionId'."}
      $bindings+=[pscustomobject]@{id=$bindingId;position_id=$positionId;role=$role};$index++
    }
    $primary=@($bindings|Where-Object {$_.role -ceq 'primary'});for($left=0;$left -lt $primary.Count;$left++){for($right=$left+1;$right -lt $primary.Count;$right++){$comparison=Get-KnowledgeChronologyComparison $Chronology $primary[$left].position_id $primary[$right].position_id;if($comparison -in @('before','after')){throw "$context.bindings declares ordered chronology positions '$($primary[$left].position_id)' and '$($primary[$right].position_id)' as primary coordinates of one occurrence."}}}
    $occurrences[$id]=[pscustomobject]@{id=[string]$id;template_id=$templateId;label=Get-OptionalOccurrenceString $item 'label' $context;iteration_id=$iterationId;branch_id=$branchId;bindings=@($bindings)}
  }
  foreach($branch in @($branches.Values)){if($null -ne $branch.fork_occurrence_id -and -not $occurrences.Contains($branch.fork_occurrence_id)){throw "branches.$($branch.id).fork_occurrence_id references unknown occurrence '$($branch.fork_occurrence_id)'."};if($null -ne $branch.fork_occurrence_id -and $occurrences[$branch.fork_occurrence_id].branch_id -cne $branch.parent_branch_id){throw "branches.$($branch.id).fork_occurrence_id must belong to parent branch '$($branch.parent_branch_id)'."}};foreach($context in @($Chronology.narrative_contexts)){if($null -ne $context.branch_id -and -not $branches.Contains($context.branch_id)){throw "Chronology context '$($context.id)' references unknown occurrence branch '$($context.branch_id)'."}}

  $rawTracks=Get-ProjectMapValue $Data 'tracks';Assert-OccurrenceMap $rawTracks 'occurrences.tracks';$tracks=[ordered]@{}
  foreach($id in @($rawTracks.Keys)){$null=Assert-OccurrenceStableId ([string]$id) 'occurrence track ID';$context="tracks.$id";$item=$rawTracks[$id];Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('label','kind','subject_type','subject_id','occurrence_ids') $context;$kind=Get-RequiredOccurrenceString $item 'kind' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.track-kind' $kind "$context.kind";$subjectType=Get-RequiredOccurrenceString $item 'subject_type' $context;$subjectId=Get-RequiredOccurrenceString $item 'subject_id' $context;if($null -eq $SubjectTargets -or -not $SubjectTargets.Contains($subjectType) -or @($SubjectTargets[$subjectType]) -cnotcontains $subjectId){throw "$context references unknown subject '$subjectType`:$subjectId'."};$occurrenceIds=@(Get-OccurrenceStringList $item 'occurrence_ids' $context);foreach($occurrenceId in $occurrenceIds){if(-not $occurrences.Contains($occurrenceId)){throw "$context.occurrence_ids references unknown occurrence '$occurrenceId'."}};$tracks[$id]=[pscustomobject]@{id=[string]$id;label=Get-RequiredOccurrenceString $item 'label' $context;kind=$kind;subject_type=$subjectType;subject_id=$subjectId;occurrence_ids=$occurrenceIds}}

  $seenIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$semanticTransitions=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$transitions=@();$rawTransitions=$Data['transitions'];Assert-OccurrenceList $rawTransitions 'occurrences.transitions';$index=0
  foreach($item in @($rawTransitions)){
    $context="transitions[$index]";Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('id','source_occurrence_id','target_occurrence_id','transition_kind','transition_profile','recurrence_id','track_ids','certainty') $context
    $id=Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' $context) "$context.id";if(-not $seenIds.Add($id)){throw "$context.id duplicates '$id'."}
    $sourceId=Get-RequiredOccurrenceString $item 'source_occurrence_id' $context;$targetId=Get-RequiredOccurrenceString $item 'target_occurrence_id' $context;if(-not $occurrences.Contains($sourceId) -or -not $occurrences.Contains($targetId)){throw "$context must reference known source and target occurrences."}
    $kind=Get-RequiredOccurrenceString $item 'transition_kind' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.transition-kind' $kind "$context.transition_kind"
    $profile=Get-RequiredOccurrenceString $item 'transition_profile' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.transition-profile' $profile "$context.transition_profile"
    Assert-OccurrencePackValue $SchemaPacks 'occurrence.transition-kind-profile' "$kind-uses-$profile" "$context.transition_kind/transition_profile"
    $recurrenceId=Get-OptionalOccurrenceString $item 'recurrence_id' $context;if($null -ne $recurrenceId -and -not $recurrences.Contains($recurrenceId)){throw "$context.recurrence_id references unknown recurrence '$recurrenceId'."}
    $trackIds=@(Get-OccurrenceStringList $item 'track_ids' $context);foreach($trackId in $trackIds){if(-not $tracks.Contains($trackId)){throw "$context.track_ids references unknown track '$trackId'."};$trackOccurrences=@($tracks[$trackId].occurrence_ids);$sourceIndex=[Array]::IndexOf($trackOccurrences,$sourceId);$targetIndex=[Array]::IndexOf($trackOccurrences,$targetId);if($sourceIndex -lt 0 -or $targetIndex -lt 0){throw "$context endpoints must both appear on track '$trackId'."};if($sourceIndex -ge $targetIndex){throw "$context must advance in declared track order on '$trackId'."}}
    $certainty=Get-RequiredOccurrenceString $item 'certainty' $context;Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
    $transition=[pscustomobject]@{id=$id;source_occurrence_id=$sourceId;target_occurrence_id=$targetId;transition_kind=$kind;transition_profile=$profile;recurrence_id=$recurrenceId;track_ids=$trackIds;certainty=$certainty};Assert-OccurrenceTransitionProfile $transition $occurrences $iterations $branches $context
    $semanticKey="$sourceId|$targetId|$kind|$profile|$recurrenceId|$(@($trackIds|Sort-Object) -join ',')";if(-not $semanticTransitions.Add($semanticKey)){throw "$context duplicates an existing semantic transition."}
    $transitions+=$transition;$index++
  }
  foreach($branch in @($branches.Values)){
    if($null -eq $branch.parent_branch_id){continue};$matches=@($transitions|Where-Object {$_.transition_profile -ceq 'branch-fork' -and $occurrences[$_.target_occurrence_id].branch_id -ceq $branch.id});if($matches.Count -ne 1){throw "branches.$($branch.id) must have exactly one matching branch-fork transition."}
  }

  $causal=@();$rawCausal=$Data['causal_relations'];Assert-OccurrenceList $rawCausal 'occurrences.causal_relations';$index=0
  foreach($item in @($rawCausal)){$context="causal_relations[$index]";Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('id','source_occurrence_id','relation_type','target_occurrence_id','certainty') $context;$id=Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' $context) "$context.id";if(-not $seenIds.Add($id)){throw "$context.id duplicates '$id'."};$sourceId=Get-RequiredOccurrenceString $item 'source_occurrence_id' $context;$targetId=Get-RequiredOccurrenceString $item 'target_occurrence_id' $context;if(-not $occurrences.Contains($sourceId) -or -not $occurrences.Contains($targetId)){throw "$context must reference known source and target occurrences."};$kind=Get-RequiredOccurrenceString $item 'relation_type' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.causal-relation-type' $kind "$context.relation_type";$certainty=Get-RequiredOccurrenceString $item 'certainty' $context;Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty";$causal+=[pscustomobject]@{id=$id;source_occurrence_id=$sourceId;relation_type=$kind;target_occurrence_id=$targetId;certainty=$certainty};$index++}

  $carryovers=@();$semanticCarryovers=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$rawCarryovers=$Data['carryovers'];Assert-OccurrenceList $rawCarryovers 'occurrences.carryovers';$index=0
  foreach($item in @($rawCarryovers)){
    $context="carryovers[$index]";Assert-OccurrenceMap $item $context;Assert-KnowledgeMapKeys $item @('id','source_iteration_id','target_iteration_id','track_id','carryover_kind','payload_target_type','payload_target_id','certainty') $context
    $id=Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'id' $context) "$context.id";if(-not $seenIds.Add($id)){throw "$context.id duplicates '$id'."}
    $sourceId=Get-RequiredOccurrenceString $item 'source_iteration_id' $context;$targetId=Get-RequiredOccurrenceString $item 'target_iteration_id' $context;$trackId=Get-RequiredOccurrenceString $item 'track_id' $context
    if(-not $iterations.Contains($sourceId) -or -not $iterations.Contains($targetId) -or -not $tracks.Contains($trackId)){throw "$context must reference known source/target iterations and track."}
    $source=$iterations[$sourceId];$target=$iterations[$targetId];if($source.recurrence_id -cne $target.recurrence_id -or $source.ordinal -ge $target.ordinal){throw "$context must advance between iterations of the same recurrence."}
    $trackIterationIds=@($tracks[$trackId].occurrence_ids|ForEach-Object {$occurrences[$_].iteration_id}|Sort-Object -Unique);if($trackIterationIds -cnotcontains $sourceId -or $trackIterationIds -cnotcontains $targetId){throw "$context.track_id must participate in both source and target iterations."}
    $kind=Get-RequiredOccurrenceString $item 'carryover_kind' $context;Assert-OccurrencePackValue $SchemaPacks 'occurrence.carryover-kind' $kind "$context.carryover_kind"
    $payloadType=Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'payload_target_type' $context) "$context.payload_target_type";$payloadId=Assert-OccurrenceStableId (Get-RequiredOccurrenceString $item 'payload_target_id' $context) "$context.payload_target_id"
    if(-not (Test-OccurrencePayloadTarget $payloadType $payloadId $branches $templates $recurrences $iterations $occurrences $tracks $PayloadTargets)){throw "$context references unknown payload target '$payloadType`:$payloadId'."}
    $certainty=Get-RequiredOccurrenceString $item 'certainty' $context;Assert-OccurrencePackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
    $semanticKey="$sourceId|$targetId|$trackId|$kind|$payloadType|$payloadId";if(-not $semanticCarryovers.Add($semanticKey)){throw "$context duplicates an existing semantic carryover."}
    $carryovers+=[pscustomobject]@{id=$id;source_iteration_id=$sourceId;target_iteration_id=$targetId;track_id=$trackId;carryover_kind=$kind;payload_target_type=$payloadType;payload_target_id=$payloadId;certainty=$certainty};$index++
  }

  return [pscustomobject]@{path=$Path;schema_version=2;branches=$branches;templates=$templates;recurrences=$recurrences;iterations=$iterations;occurrences=$occurrences;tracks=$tracks;transitions=@($transitions);causal_relations=@($causal);carryovers=@($carryovers)}
}

function Get-KnowledgeOccurrenceRegistry{
  param([object]$Project,[object]$SchemaPacks,[object]$Chronology,[System.Collections.IDictionary]$SubjectTargets=$null,[System.Collections.IDictionary]$PayloadTargets=$null)
  $data=ConvertFrom-KnowledgeYamlFile $Project.occurrences_registry 2 'occurrence registry';return ConvertTo-KnowledgeOccurrenceRegistry $data $Project.occurrences_registry $SchemaPacks $Chronology $SubjectTargets $PayloadTargets
}
