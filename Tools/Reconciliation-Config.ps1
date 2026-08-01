$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) { . $projectConfigHelper }
$schemaPackHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-KnowledgeSchemaPackRegistry -ErrorAction SilentlyContinue)) { . $schemaPackHelper }

$script:SupportedReconciliationSchemaVersion = 1
$script:ReconciliationStableIdPattern = "^[a-z0-9]+(?:-[a-z0-9]+)*$"

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

function Assert-ReconciliationPackValue {
  param([object]$SchemaPacks,[string]$Namespace,[string]$Value,[string]$Context)
  if(@(Get-SchemaPackAllowedValues $SchemaPacks $Namespace) -notcontains $Value){throw "Reconciliation registry '$Context' uses unregistered $Namespace value '$Value'."}
}

function Get-ReconciliationCurrentTarget {
  param([object]$Registry,[string]$TargetType,[string]$TargetId)
  if(-not $Registry.targets.Contains($TargetType)){throw "Unsupported reconciliation target type '$TargetType'."}
  if(-not $Registry.targets[$TargetType].Contains($TargetId)){throw "Unknown $TargetType '$TargetId'."}
  return $Registry.targets[$TargetType][$TargetId]
}

function Test-ReconciliationCurrentTarget {
  param([object]$Registry,[string]$TargetType,[string]$TargetId)
  try { $null = Get-ReconciliationCurrentTarget $Registry $TargetType $TargetId; return $true }
  catch {
    if ($_.Exception.Message -like "Unknown $TargetType *") { return $false }
    throw
  }
}

function Get-KnowledgeReconciliationProvenanceSubjectTypes { return @("reconciliation-record") }

function Get-KnowledgeReconciliationProvenanceTarget {
  param([object]$Registry,[string]$SubjectType,[string]$SubjectId)
  if ($SubjectType -ne "reconciliation-record") { throw "Unsupported reconciliation provenance subject type '$SubjectType'." }
  $target = @($Registry.records | Where-Object id -eq $SubjectId)
  if ($target.Count -ne 1) { throw "Unknown reconciliation-record '$SubjectId'." }
  return $target[0]
}

function Resolve-KnowledgeReconciliationTarget {
  param([object]$Registry,[string]$TargetType,[string]$TargetId)
  if (@($Registry.target_types) -notcontains $TargetType) { throw "Unsupported reconciliation target type '$TargetType'." }
  $active = [ordered]@{}
  foreach ($record in @($Registry.records | Where-Object status -eq "active")) { $active["$($record.source_type)|$($record.source_id)"] = $record }
  $requestedKey = "$TargetType|$TargetId"
  if (-not $active.Contains($requestedKey)) {
    if (-not (Test-ReconciliationCurrentTarget $Registry $TargetType $TargetId)) { throw "Unknown current or historical $TargetType '$TargetId'." }
    return [pscustomobject]@{outcome="canonical";requested_type=$TargetType;requested_id=$TargetId;canonical_targets=@([pscustomobject]@{target_type=$TargetType;target_id=$TargetId});reconciliation_ids=@()}
  }
  $path = New-Object 'System.Collections.Generic.List[string]'
  function Resolve-ReconciliationEndpoint([string]$Type,[string]$Id) {
    $key="$Type|$Id"
    if (-not $active.Contains($key)) { return @([pscustomobject]@{target_type=$Type;target_id=$Id}) }
    $record=$active[$key];if(-not $path.Contains([string]$record.id)){$path.Add([string]$record.id)}
    if($record.operation -eq "retire"){return @()}
    $resolved=@();foreach($target in @($record.targets)){foreach($item in @(Resolve-ReconciliationEndpoint $target.target_type $target.target_id)){if(@($resolved|Where-Object {$_.target_type -eq $item.target_type -and $_.target_id -eq $item.target_id}).Count -eq 0){$resolved+=,$item}}};return @($resolved)
  }
  $canonical=@(Resolve-ReconciliationEndpoint $TargetType $TargetId);$first=$active[$requestedKey]
  $outcome=if($canonical.Count -eq 0){"retired"}elseif($first.operation -eq "split" -or $canonical.Count -gt 1){"ambiguous"}else{"redirected"}
  return [pscustomobject]@{outcome=$outcome;requested_type=$TargetType;requested_id=$TargetId;canonical_targets=@($canonical);reconciliation_ids=@($path)}
}

function Get-KnowledgeReconciliationRegistry {
  param([object]$ProjectConfig,[object[]]$Providers,[object]$SchemaPackRegistry)
  if($null -eq $SchemaPackRegistry){$SchemaPackRegistry=Get-KnowledgeSchemaPackRegistry $ProjectConfig}
  if(-not (Test-SchemaPackCapabilityEnabled $SchemaPackRegistry "stable-identity-reconciliation")){throw "Capability 'stable-identity-reconciliation' must be enabled."}
  $providerTargets=[ordered]@{};foreach($provider in @($Providers)){if($provider -isnot [System.Collections.IDictionary]){throw "Reconciliation providers must be mappings of target types to stable-record maps."};foreach($targetType in $provider.Keys){if($providerTargets.Contains($targetType)){throw "Reconciliation target types have multiple providers: $targetType."};if($provider[$targetType] -isnot [System.Collections.IDictionary]){throw "Reconciliation provider '$targetType' must expose a stable-record mapping."};$providerTargets[$targetType]=$provider[$targetType]}}
  $targetTypes=@($providerTargets.Keys)
  $allowed=@(Get-SchemaPackAllowedValues $SchemaPackRegistry "reconciliation.target-type")
  $missing=@($allowed|Where-Object {$targetTypes -notcontains $_});$extra=@($targetTypes|Where-Object {$allowed -notcontains $_})
  if($missing.Count -gt 0 -or $extra.Count -gt 0){$details=@();if($missing.Count -gt 0){$details+="missing providers: $($missing -join ', ')"};if($extra.Count -gt 0){$details+="unregistered providers: $($extra -join ', ')"};throw "Reconciliation target-provider mismatch ($($details -join '; '))."}
  $path=$ProjectConfig.reconciliation_registry;$raw=ConvertFrom-Yaml -Yaml ([System.IO.File]::ReadAllText($path,[System.Text.UTF8Encoding]::new($true))) -Ordered
  if($null -eq $raw -or $raw -isnot [System.Collections.IDictionary]){throw "Reconciliation registry root must be a mapping: $path"}
  $schemaVersion=Get-ProjectMapValue $raw "schema_version";if([int]$schemaVersion -ne $script:SupportedReconciliationSchemaVersion){throw "Unsupported reconciliation schema_version '$schemaVersion'; expected $($script:SupportedReconciliationSchemaVersion)."}
  $rawRecords=Get-ProjectMapValue $raw "records" ([System.DBNull]::Value);if($rawRecords -is [System.DBNull] -or $rawRecords -is [string]){throw "Reconciliation registry 'records' must be a list."}
  $shell=[pscustomobject]@{path=$path;schema_version=[int]$schemaVersion;records=@();target_types=@($targetTypes);targets=$providerTargets}
  $records=@();$ids=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$activeSources=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $items=@($rawRecords);for($i=0;$i -lt $items.Count;$i++){
    $context="records[$i]";$item=$items[$i];if($item -isnot [System.Collections.IDictionary]){throw "Reconciliation registry '$context' must be a mapping."}
    $id=Get-RequiredReconciliationString $item "id" $context;if($id -notmatch $script:ReconciliationStableIdPattern){throw "Reconciliation registry '$context.id' must be a lowercase kebab-case stable ID: $id"};if(-not $ids.Add($id)){throw "Reconciliation record ID '$id' is duplicated."}
    $sourceType=Get-RequiredReconciliationString $item "source_type" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.target-type" $sourceType "$context.source_type"
    $sourceId=Get-RequiredReconciliationString $item "source_id" $context;if($sourceId -notmatch $script:ReconciliationStableIdPattern){throw "Reconciliation registry '$context.source_id' must be a lowercase kebab-case stable ID: $sourceId"}
    $sourceState=Get-RequiredReconciliationString $item "source_state" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.source-state" $sourceState "$context.source_state"
    $sourceLabel=Get-RequiredReconciliationString $item "source_label" $context;$operation=Get-RequiredReconciliationString $item "operation" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.operation" $operation "$context.operation"
    $reason=Get-RequiredReconciliationString $item "reason" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.reason" $reason "$context.reason";$status=Get-RequiredReconciliationString $item "status" $context;Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.status" $status "$context.status"
    $supersededBy=Get-OptionalReconciliationString $item "superseded_by_id" $context;if($null -ne $supersededBy -and $supersededBy -notmatch $script:ReconciliationStableIdPattern){throw "Reconciliation registry '$context.superseded_by_id' must be a lowercase kebab-case stable ID: $supersededBy"}
    if(-not $item.Contains("targets")){throw "Reconciliation registry '$context.targets' must be a list."};$rawTargets=Get-ProjectMapValue $item "targets";if($rawTargets -is [string]){throw "Reconciliation registry '$context.targets' must be a list."};$targets=@();$seenTargets=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach($target in @($rawTargets)){$targetType=Get-RequiredReconciliationString $target "target_type" "$context.targets";Assert-ReconciliationPackValue $SchemaPackRegistry "reconciliation.target-type" $targetType "$context.targets.target_type";$targetId=Get-RequiredReconciliationString $target "target_id" "$context.targets";if($targetId -notmatch $script:ReconciliationStableIdPattern){throw "Reconciliation target ID '$targetId' must be lowercase kebab-case."};if($targetType -ne $sourceType){throw "Reconciliation registry '$context.targets' must preserve target type '$sourceType'."};$key="$targetType|$targetId";if($key -eq "$sourceType|$sourceId"){throw "Reconciliation registry '$context.targets' cannot target its own source."};if(-not $seenTargets.Add($key)){throw "Reconciliation registry '$context.targets' repeats '$targetType`:$targetId'."};$targets+=,[pscustomobject]@{target_type=$targetType;target_id=$targetId}}
    $validCount=if($operation -eq "retire"){$targets.Count -eq 0}elseif($operation -eq "split"){$targets.Count -ge 2}else{$targets.Count -eq 1};if(-not $validCount){throw "Reconciliation registry '$context.targets' has invalid cardinality for '$operation'."}
    $exists=Test-ReconciliationCurrentTarget $shell $sourceType $sourceId;if(($sourceState -eq "present") -ne $exists){throw "Reconciliation registry '$context' source existence does not match source_state '$sourceState'."}
    if($status -eq "active"){if($null -ne $supersededBy){throw "Reconciliation registry active '$id' cannot have superseded_by_id."};if(-not $activeSources.Add("$sourceType|$sourceId")){throw "Reconciliation source '$sourceType`:$sourceId' has multiple active records."}}
    elseif($status -eq "superseded"){if($null -eq $supersededBy){throw "Reconciliation registry superseded '$id' requires superseded_by_id."}}
    else{if($null -ne $supersededBy){throw "Reconciliation registry reversed '$id' cannot have superseded_by_id."};if($sourceState -ne "present"){throw "Reconciliation registry reversed '$id' requires a present source."}}
    $records+=,[pscustomobject]@{id=$id;source_type=$sourceType;source_id=$sourceId;source_state=$sourceState;source_label=$sourceLabel;operation=$operation;targets=@($targets);reason=$reason;status=$status;superseded_by_id=$supersededBy}
  }
  $shell.records=@($records);$byId=[ordered]@{};foreach($record in $records){$byId[$record.id]=$record}
  foreach($record in $records){if($null -ne $record.superseded_by_id){if(-not $byId.Contains($record.superseded_by_id)){throw "Reconciliation record '$($record.id)' references unknown superseded_by_id '$($record.superseded_by_id)'."};$next=$byId[$record.superseded_by_id];if($next.source_type -ne $record.source_type -or $next.source_id -ne $record.source_id){throw "Reconciliation record '$($record.id)' supersession must retain the same source."}}}
  $active=[ordered]@{};foreach($record in @($records|Where-Object status -eq "active")){$active["$($record.source_type)|$($record.source_id)"]=$record}
  foreach($record in $active.Values){foreach($target in @($record.targets)){if(-not (Test-ReconciliationCurrentTarget $shell $target.target_type $target.target_id) -and -not $active.Contains("$($target.target_type)|$($target.target_id)")){throw "Reconciliation record '$($record.id)' targets unknown current or historical '$($target.target_type):$($target.target_id)'."}}}
  $visiting=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$visited=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  function Visit-ReconciliationKey([string]$Key){if($visiting.Contains($Key)){throw "Reconciliation active resolution graph contains a cycle at '$Key'."};if($visited.Contains($Key) -or -not $active.Contains($Key)){return};[void]$visiting.Add($Key);foreach($target in @($active[$Key].targets)){Visit-ReconciliationKey "$($target.target_type)|$($target.target_id)"};[void]$visiting.Remove($Key);[void]$visited.Add($Key)}
  foreach($key in $active.Keys){Visit-ReconciliationKey $key}
  foreach($record in $records){$seen=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$current=$record;while($null -ne $current.superseded_by_id){if(-not $seen.Add([string]$current.id)){throw "Reconciliation supersession chain contains a cycle at '$($current.id)'."};$current=$byId[$current.superseded_by_id]};if($record.status -eq "superseded" -and $current.status -ne "active"){throw "Reconciliation superseded record '$($record.id)' must lead to an active record."}}
  return $shell
}
