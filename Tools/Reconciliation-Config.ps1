$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) { . $projectConfigHelper }
$schemaPackHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-KnowledgeSchemaPackRegistry -ErrorAction SilentlyContinue)) { . $schemaPackHelper }

$script:SupportedReconciliationSchemaVersion = 3
$script:ReconciliationStableIdPattern = "^[a-z0-9]+(?:-[a-z0-9]+)*$"
$script:ReconciliationRootFields = @("schema_version","resolution","records")
$script:ReconciliationResolutionFields = @("max_branches")
$script:ReconciliationRecordFields = @("id","source_type","source_id","source_state","source_label_mode","source_label","operation","targets","reason","status","superseded_by_id","audit")
$script:ReconciliationTargetFields = @("target_type","target_id")
$script:ReconciliationAuditFields = @("mode","recorded_at","actor_ref","approval_ref","migration_id")

function Get-RequiredReconciliationString {
  param([object]$Mapping,[string]$Key,[string]$Context)
  $value=Get-ProjectMapValue $Mapping $Key
  if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw "Reconciliation registry '$Context.$Key' must be a non-empty string."}
  return $value.Trim()
}

function Get-OptionalReconciliationString {
  param([object]$Mapping,[string]$Key,[string]$Context)
  $value=Get-ProjectMapValue $Mapping $Key
  if($null -eq $value){return $null}
  if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw "Reconciliation registry '$Context.$Key' must be null or a non-empty string."}
  return $value.Trim()
}

function Assert-ReconciliationStableId {
  param([string]$Value,[string]$Context)
  if($Value -cnotmatch $script:ReconciliationStableIdPattern){throw "Reconciliation registry '$Context' must be a lowercase kebab-case stable ID: $Value"}
}

function Assert-ReconciliationPackValue {
  param([object]$SchemaPacks,[string]$Namespace,[string]$Value,[string]$Context)
  if(@(Get-SchemaPackAllowedValues $SchemaPacks $Namespace) -cnotcontains $Value){throw "Reconciliation registry '$Context' uses unregistered $Namespace value '$Value'."}
}

function Get-ReconciliationCurrentTarget {
  param([object]$Registry,[string]$TargetType,[string]$TargetId)
  if(-not $Registry.targets.Contains($TargetType)){throw "Unsupported reconciliation target type '$TargetType'."}
  if(-not $Registry.targets[$TargetType].Contains($TargetId)){throw "Unknown current $TargetType '$TargetId'."}
  return $Registry.targets[$TargetType][$TargetId]
}

function Test-ReconciliationCurrentTarget {
  param([object]$Registry,[string]$TargetType,[string]$TargetId)
  try { $null = Get-ReconciliationCurrentTarget $Registry $TargetType $TargetId; return $true }
  catch {
    if ($_.Exception.Message -like "Unknown current $TargetType *") { return $false }
    throw
  }
}

function Get-KnowledgeReconciliationProvenanceSubjectTypes { return @("reconciliation-record") }

function Get-KnowledgeReconciliationProvenanceTarget {
  param([object]$Registry,[string]$SubjectType,[string]$SubjectId)
  if ($SubjectType -ne "reconciliation-record") { throw "Unsupported reconciliation provenance subject type '$SubjectType'." }
  if (-not $Registry.records_by_id.Contains($SubjectId)) { throw "Unknown reconciliation-record '$SubjectId'." }
  return $Registry.records_by_id[$SubjectId]
}

function Resolve-KnowledgeReconciliationTarget {
  param([object]$Registry,[string]$TargetType,[string]$TargetId)
  if (@($Registry.target_types) -cnotcontains $TargetType) { throw "Unsupported reconciliation target type '$TargetType'." }
  $requestedKey = "$TargetType|$TargetId"
  if (-not $Registry.active_records.Contains($requestedKey)) {
    if (-not (Test-ReconciliationCurrentTarget $Registry $TargetType $TargetId)) { throw "Unknown current or historical $TargetType '$TargetId'." }
    $endpoint=[pscustomobject]@{target_type=$TargetType;target_id=$TargetId}
    $branch=[pscustomobject]@{outcome="canonical";canonical_target=$endpoint;reconciliation_ids=@()}
    return [pscustomobject]@{outcome="canonical";requested_type=$TargetType;requested_id=$TargetId;canonical_targets=@($endpoint);reconciliation_ids=@();branches=@($branch)}
  }

  $stack=New-Object 'System.Collections.Generic.Stack[object]'
  $stack.Push([pscustomobject]@{target_type=$TargetType;target_id=$TargetId;path=@()})
  $branches=New-Object 'System.Collections.Generic.List[object]'
  while($stack.Count -gt 0){
    $item=$stack.Pop();$key="$($item.target_type)|$($item.target_id)"
    if(-not $Registry.active_records.Contains($key)){
      if($branches.Count -ge $Registry.max_branches){throw "Reconciliation resolution for '$TargetType`:$TargetId' exceeds configured max_branches $($Registry.max_branches)."}
      $endpoint=[pscustomobject]@{target_type=$item.target_type;target_id=$item.target_id}
      $branches.Add([pscustomobject]@{outcome="canonical";canonical_target=$endpoint;reconciliation_ids=@($item.path)})
      continue
    }
    $record=$Registry.active_records[$key];$nextPath=@($item.path)+@([string]$record.id)
    if($record.operation -eq "retire"){
      if($branches.Count -ge $Registry.max_branches){throw "Reconciliation resolution for '$TargetType`:$TargetId' exceeds configured max_branches $($Registry.max_branches)."}
      $branches.Add([pscustomobject]@{outcome="retired";canonical_target=$null;reconciliation_ids=@($nextPath)})
      continue
    }
    $recordTargets=@($record.targets)
    for($i=$recordTargets.Count-1;$i -ge 0;$i--){
      $target=$recordTargets[$i]
      $stack.Push([pscustomobject]@{target_type=$target.target_type;target_id=$target.target_id;path=@($nextPath)})
    }
  }
  $canonical=New-Object 'System.Collections.Generic.List[object]'
  $path=New-Object 'System.Collections.Generic.List[string]'
  foreach($branch in $branches){
    if($null -ne $branch.canonical_target){
      $exists=@($canonical|Where-Object {$_.target_type -eq $branch.canonical_target.target_type -and $_.target_id -eq $branch.canonical_target.target_id}).Count -gt 0
      if(-not $exists){$canonical.Add($branch.canonical_target)}
    }
    foreach($recordId in @($branch.reconciliation_ids)){if(-not $path.Contains([string]$recordId)){$path.Add([string]$recordId)}}
  }
  if($branches.Count -gt 1){$outcome="ambiguous"}elseif($branches[0].outcome -eq "retired"){$outcome="retired"}else{$outcome="redirected"}
  return [pscustomobject]@{outcome=$outcome;requested_type=$TargetType;requested_id=$TargetId;canonical_targets=$canonical.ToArray();reconciliation_ids=$path.ToArray();branches=$branches.ToArray()}
}

function ConvertTo-ReconciliationProviderState {
  param([object[]]$Providers)
  $targets=[ordered]@{};$aliases=[ordered]@{};$providerIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $index=0
  foreach($provider in @($Providers)){
    $providerId=Get-ProjectMapValue $provider "provider_id"
    $providerTargets=Get-ProjectMapValue $provider "targets"
    $providerAliases=Get-ProjectMapValue $provider "aliases" ([ordered]@{})
    if($providerId -isnot [string] -or [string]::IsNullOrWhiteSpace($providerId)){throw "Reconciliation provider $index requires a non-empty provider_id."}
    $providerId=$providerId.Trim();Assert-ReconciliationStableId $providerId "providers[$index].provider_id"
    if(-not $providerIds.Add($providerId)){throw "Reconciliation provider ID '$providerId' is duplicated."}
    if($providerTargets -isnot [System.Collections.IDictionary] -or $providerAliases -isnot [System.Collections.IDictionary]){throw "Reconciliation provider '$providerId' targets and aliases must be mappings."}
    foreach($targetType in $providerTargets.Keys){
      if($targets.Contains($targetType)){throw "Reconciliation target types have multiple providers: $targetType."}
      if($providerTargets[$targetType] -isnot [System.Collections.IDictionary]){throw "Reconciliation provider '$providerId' target '$targetType' must be a stable-record mapping."}
      $targetCopy=[ordered]@{}
      foreach($targetId in $providerTargets[$targetType].Keys){$targetCopy[$targetId]=$providerTargets[$targetType][$targetId]}
      $targets[$targetType]=$targetCopy
      $aliasMap=if($providerAliases.Contains($targetType)){$providerAliases[$targetType]}else{[ordered]@{}}
      if($aliasMap -isnot [System.Collections.IDictionary]){throw "Reconciliation provider '$providerId' aliases for '$targetType' must be a mapping."}
      $aliasKeys=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
      foreach($alias in $aliasMap.Keys){[void]$aliasKeys.Add([string]$alias)}
      $aliases[$targetType]=$aliasKeys
    }
    $extraAliases=@($providerAliases.Keys|Where-Object {$providerTargets.Keys -cnotcontains $_})
    if($extraAliases.Count -gt 0){throw "Reconciliation provider '$providerId' has aliases for unprovided target types: $($extraAliases -join ', ')."}
    $index++
  }
  return [pscustomobject]@{targets=$targets;aliases=$aliases}
}

function ConvertTo-ReconciliationAudit {
  param([object]$Item,[string]$Context,[object]$SchemaPacks)
  $audit=Get-ProjectMapValue $Item "audit"
  if($audit -isnot [System.Collections.IDictionary]){throw "Reconciliation registry '$Context.audit' must be a mapping."}
  Assert-KnowledgeMapKeys $audit $script:ReconciliationAuditFields "Reconciliation registry '$Context.audit'"
  $mode=Get-RequiredReconciliationString $audit "mode" "$Context.audit"
  Assert-ReconciliationPackValue $SchemaPacks "reconciliation.audit-mode" $mode "$Context.audit.mode"
  $recordedAt=Get-OptionalReconciliationString $audit "recorded_at" "$Context.audit"
  $actorRef=Get-OptionalReconciliationString $audit "actor_ref" "$Context.audit"
  $approvalRef=Get-OptionalReconciliationString $audit "approval_ref" "$Context.audit"
  $migrationId=Get-OptionalReconciliationString $audit "migration_id" "$Context.audit"
  if($null -ne $migrationId){Assert-ReconciliationStableId $migrationId "$Context.audit.migration_id"}
  if($mode -eq "explicit"){
    if($null -eq $recordedAt -or $null -eq $actorRef){throw "Reconciliation registry '$Context.audit' explicit mode requires recorded_at and actor_ref."}
    if(-not (Test-KnowledgeRfc3339Timestamp $recordedAt)){throw "Reconciliation registry '$Context.audit.recorded_at' must be valid RFC 3339 with a timezone."}
  }elseif($null -ne $recordedAt -or $null -ne $actorRef -or $null -ne $approvalRef){throw "Reconciliation registry '$Context.audit' repository-history mode derives actor, time, and approval from version control."}
  return [pscustomobject]@{mode=$mode;recorded_at=$recordedAt;actor_ref=$actorRef;approval_ref=$approvalRef;migration_id=$migrationId}
}

function Assert-ReconciliationActiveGraphAcyclic {
  param([System.Collections.IDictionary]$Active)
  $indegree=[ordered]@{};$children=[ordered]@{}
  foreach($key in $Active.Keys){$indegree[$key]=0;$children[$key]=@()}
  foreach($key in $Active.Keys){foreach($target in @($Active[$key].targets)){$child="$($target.target_type)|$($target.target_id)";if($Active.Contains($child)){$children[$key]=@($children[$key])+@($child);$indegree[$child]=[int]$indegree[$child]+1}}}
  $queue=New-Object 'System.Collections.Generic.Queue[string]';foreach($key in $indegree.Keys){if([int]$indegree[$key] -eq 0){$queue.Enqueue([string]$key)}}
  $count=0;while($queue.Count -gt 0){$key=$queue.Dequeue();$count++;foreach($child in @($children[$key])){$indegree[$child]=[int]$indegree[$child]-1;if([int]$indegree[$child] -eq 0){$queue.Enqueue([string]$child)}}}
  if($count -ne $Active.Count){$cycle=@($indegree.Keys|Where-Object {[int]$indegree[$_] -gt 0})[0];throw "Reconciliation active resolution graph contains a cycle at '$cycle'."}
}

function Get-KnowledgeReconciliationRegistry {
  param([object]$ProjectConfig,[object[]]$Providers,[object]$SchemaPackRegistry)
  if($null -eq $SchemaPackRegistry){$SchemaPackRegistry=Get-KnowledgeSchemaPackRegistry $ProjectConfig}
  if(-not (Test-SchemaPackCapabilityEnabled $SchemaPackRegistry "stable-identity-reconciliation")){throw "Capability 'stable-identity-reconciliation' must be enabled."}
  $providerState=ConvertTo-ReconciliationProviderState $Providers;$providerTargets=$providerState.targets;$providerAliases=$providerState.aliases
  $targetTypes=@($providerTargets.Keys);$allowed=@(Get-SchemaPackAllowedValues $SchemaPackRegistry "reconciliation.target-type")
  $missing=@($allowed|Where-Object {$targetTypes -cnotcontains $_});$extra=@($targetTypes|Where-Object {$allowed -cnotcontains $_})
  if($missing.Count -gt 0 -or $extra.Count -gt 0){$details=@();if($missing.Count -gt 0){$details+="missing providers: $($missing -join ', ')"};if($extra.Count -gt 0){$details+="unregistered providers: $($extra -join ', ')"};throw "Reconciliation target-provider mismatch ($($details -join '; '))."}
  $path=$ProjectConfig.reconciliation_registry;$raw=ConvertFrom-KnowledgeYamlFile $path $script:SupportedReconciliationSchemaVersion "reconciliation registry"
  Assert-KnowledgeMapKeys $raw $script:ReconciliationRootFields "Reconciliation registry root"
  $schemaVersion=Get-ProjectMapValue $raw "schema_version";if($schemaVersion -isnot [int] -or $schemaVersion -ne $script:SupportedReconciliationSchemaVersion){throw "Unsupported reconciliation schema_version '$schemaVersion'; expected $($script:SupportedReconciliationSchemaVersion)."}
  $resolution=Get-ProjectMapValue $raw "resolution";if($resolution -isnot [System.Collections.IDictionary]){throw "Reconciliation registry 'resolution' must be a mapping."};Assert-KnowledgeMapKeys $resolution $script:ReconciliationResolutionFields "Reconciliation registry 'resolution'"
  $maxBranches=Get-ProjectMapValue $resolution "max_branches";if($maxBranches -isnot [int] -or $maxBranches -lt 1){throw "Reconciliation registry 'resolution.max_branches' must be a positive integer."}
  $rawRecords=Get-ProjectMapValue $raw "records" ([System.DBNull]::Value);if($rawRecords -is [System.DBNull] -or $rawRecords -is [string]){throw "Reconciliation registry 'records' must be a list."}
  $shell=[pscustomobject]@{path=$path;schema_version=[int]$schemaVersion;records=@();target_types=@($targetTypes);targets=$providerTargets;aliases=$providerAliases;records_by_id=[ordered]@{};active_records=[ordered]@{};max_branches=[int]$maxBranches}
  $records=@();$ids=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$activeSources=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $items=@($rawRecords);for($i=0;$i -lt $items.Count;$i++){
    $context="records[$i]";$item=$items[$i];if($item -isnot [System.Collections.IDictionary]){throw "Reconciliation registry '$context' must be a mapping."}
    Assert-KnowledgeMapKeys $item $script:ReconciliationRecordFields "Reconciliation registry '$context'"
    $id=Get-RequiredReconciliationString $item "id" $context;Assert-ReconciliationStableId $id "$context.id";if(-not $ids.Add($id)){throw "Reconciliation record ID '$id' is duplicated."}
    $sourceType=Get-RequiredReconciliationString $item "source_type" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.target-type" $sourceType "$context.source_type"
    $sourceId=Get-RequiredReconciliationString $item "source_id" $context;Assert-ReconciliationStableId $sourceId "$context.source_id"
    $sourceState=Get-RequiredReconciliationString $item "source_state" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.source-state" $sourceState "$context.source_state"
    $sourceLabelMode=Get-RequiredReconciliationString $item "source_label_mode" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.source-label-mode" $sourceLabelMode "$context.source_label_mode"
    $sourceLabel=Get-OptionalReconciliationString $item "source_label" $context
    if($sourceLabelMode -eq "snapshot" -and $null -eq $sourceLabel){throw "Reconciliation registry '$context' snapshot source_label_mode requires source_label."}
    if($sourceLabelMode -ne "snapshot" -and $null -ne $sourceLabel){throw "Reconciliation registry '$context' $sourceLabelMode source_label_mode forbids source_label."}
    $operation=Get-RequiredReconciliationString $item "operation" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.operation" $operation "$context.operation"
    $reason=Get-RequiredReconciliationString $item "reason" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.reason" $reason "$context.reason";Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.operation-reason-pair" "$operation-$reason" "$context.operation/reason"
    $status=Get-RequiredReconciliationString $item "status" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.status" $status "$context.status"
    $supersededBy=Get-OptionalReconciliationString $item "superseded_by_id" $context;if($null -ne $supersededBy){Assert-ReconciliationStableId $supersededBy "$context.superseded_by_id"}
    $audit=ConvertTo-ReconciliationAudit $item $context $SchemaPackRegistry
    if(-not $item.Contains("targets")){throw "Reconciliation registry '$context.targets' must be a list."};$rawTargets=Get-ProjectMapValue $item "targets";if($rawTargets -is [string]){throw "Reconciliation registry '$context.targets' must be a list."}
    $targets=@();$seenTargets=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach($target in @($rawTargets)){Assert-KnowledgeMapKeys $target $script:ReconciliationTargetFields "Reconciliation registry '$context.targets'";$targetType=Get-RequiredReconciliationString $target "target_type" "$context.targets";Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.target-type" $targetType "$context.targets.target_type";$targetId=Get-RequiredReconciliationString $target "target_id" "$context.targets";Assert-ReconciliationStableId $targetId "$context.targets.target_id";if($operation -eq "reclassify"){if($targetType -eq $sourceType){throw "Reconciliation registry '$context.targets' reclassify must change target type."}}elseif($targetType -ne $sourceType){throw "Reconciliation registry '$context.targets' must preserve target type '$sourceType'."};$key="$targetType|$targetId";if($key -eq "$sourceType|$sourceId"){throw "Reconciliation registry '$context.targets' cannot target its own source."};if(-not $seenTargets.Add($key)){throw "Reconciliation registry '$context.targets' repeats '$targetType`:$targetId'."};$targets+=,[pscustomobject]@{target_type=$targetType;target_id=$targetId}}
    $validCount=if($operation -eq "retire"){$targets.Count -eq 0}elseif($operation -eq "split"){$targets.Count -ge 2}else{$targets.Count -eq 1};if(-not $validCount){throw "Reconciliation registry '$context.targets' has invalid cardinality for '$operation'."}
    $exists=Test-ReconciliationCurrentTarget $shell $sourceType $sourceId;if(($sourceState -eq "present") -ne $exists){throw "Reconciliation registry '$context' source existence does not match source_state '$sourceState'."}
    if($sourceState -eq "tombstone" -and $providerAliases[$sourceType].Contains($sourceId)){throw "Reconciliation tombstone '$sourceType`:$sourceId' conflicts with a provider alias; historical stable IDs belong only to reconciliation."}
    if($status -eq "active" -and $operation -eq "retire" -and $sourceState -ne "tombstone"){throw "Reconciliation registry active retirement '$id' requires a tombstone source."}
    if($status -eq "active"){if($null -ne $supersededBy){throw "Reconciliation registry active '$id' cannot have superseded_by_id."};if(-not $activeSources.Add("$sourceType|$sourceId")){throw "Reconciliation source '$sourceType`:$sourceId' has multiple active records."}}
    elseif($status -eq "superseded"){if($null -eq $supersededBy){throw "Reconciliation registry superseded '$id' requires superseded_by_id."}}
    else{if($null -ne $supersededBy){throw "Reconciliation registry reversed '$id' cannot have superseded_by_id."};if($sourceState -ne "present"){throw "Reconciliation registry reversed '$id' requires a present source."}}
    $records+=,[pscustomobject]@{id=$id;source_type=$sourceType;source_id=$sourceId;source_state=$sourceState;source_label_mode=$sourceLabelMode;source_label=$sourceLabel;operation=$operation;targets=@($targets);reason=$reason;status=$status;superseded_by_id=$supersededBy;audit=$audit}
  }
  $shell.records=@($records);$byId=[ordered]@{};foreach($record in $records){$byId[$record.id]=$record};$shell.records_by_id=$byId
  foreach($record in $records){if($null -ne $record.superseded_by_id){if(-not $byId.Contains($record.superseded_by_id)){throw "Reconciliation record '$($record.id)' references unknown superseded_by_id '$($record.superseded_by_id)'."};$next=$byId[$record.superseded_by_id];if($next.source_type -ne $record.source_type -or $next.source_id -ne $record.source_id){throw "Reconciliation record '$($record.id)' supersession must retain the same source."}}}
  $active=[ordered]@{};foreach($record in @($records|Where-Object status -eq "active")){$active["$($record.source_type)|$($record.source_id)"]=$record};$shell.active_records=$active
  foreach($record in $active.Values){foreach($target in @($record.targets)){if(-not (Test-ReconciliationCurrentTarget $shell $target.target_type $target.target_id) -and -not $active.Contains("$($target.target_type)|$($target.target_id)")){throw "Reconciliation record '$($record.id)' targets unknown current or historical '$($target.target_type):$($target.target_id)'."}}}
  Assert-ReconciliationActiveGraphAcyclic $active
  $terminalById=[ordered]@{}
  foreach($record in $records){if($terminalById.Contains($record.id)){continue};$pathRecords=New-Object 'System.Collections.Generic.List[object]';$localIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$current=$record;while(-not $terminalById.Contains($current.id)){if(-not $localIds.Add([string]$current.id)){throw "Reconciliation supersession chain contains a cycle at '$($current.id)'."};$pathRecords.Add($current);if($null -eq $current.superseded_by_id){break};$current=$byId[$current.superseded_by_id]};$terminal=if($terminalById.Contains($current.id)){$terminalById[$current.id]}else{$current};foreach($item in $pathRecords){$terminalById[$item.id]=$terminal}}
  foreach($record in $records){if($record.status -eq "superseded" -and $terminalById[$record.id].status -ne "active"){throw "Reconciliation superseded record '$($record.id)' must lead to an active record."}}
  return $shell
}
