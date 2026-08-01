$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-ProjectMapValue -ErrorAction SilentlyContinue)) { . $projectConfigHelper }
$schemaPackConfigHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-SchemaPackAllowedValues -ErrorAction SilentlyContinue)) { . $schemaPackConfigHelper }

$script:SupportedChronologySchemaVersion = 1
$script:ChronologyStableIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'

function Get-RequiredChronologyString {
  param([object]$Map,[string]$Key,[string]$Context)
  $value=Get-ProjectMapValue $Map $Key
  if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw "$Context.$Key must be a non-empty string."}
  return $value.Trim()
}

function Get-OptionalChronologyString {
  param([object]$Map,[string]$Key,[string]$Context)
  $value=Get-ProjectMapValue $Map $Key
  if($null -eq $value){return $null}
  if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw "$Context.$Key must be a non-empty string or null."}
  return $value.Trim()
}

function Get-ChronologyStringList {
  param([object]$Map,[string]$Key,[string]$Context)
  $value=Get-ProjectMapValue $Map $Key
  if($null -eq $value){return @()}
  if($value -is [string]){$value=@($value)}
  elseif($value -isnot [System.Collections.IList]){throw "$Context.$Key must be a list."}
  $result=@();$seen=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach($item in @($value)){
    if($item -isnot [string] -or [string]::IsNullOrWhiteSpace($item) -or -not $seen.Add($item.Trim())){throw "$Context.$Key must contain unique non-empty strings."}
    $result += $item.Trim()
  }
  return @($result)
}

function Assert-ChronologyStableId {
  param([string]$Value,[string]$Context)
  if($Value -cnotmatch $script:ChronologyStableIdPattern){throw "$Context must be a lowercase kebab-case stable ID: $Value"}
  return $Value
}

function Assert-ChronologyPackValue {
  param([object]$SchemaPacks,[string]$Namespace,[string]$Value,[string]$Context)
  $allowed=@(Get-SchemaPackAllowedValues $SchemaPacks $Namespace)
  if($allowed.Count -eq 0 -or $allowed -cnotcontains $Value){throw "$Context uses '$Value', which is not provided in '$Namespace'."}
}

function Assert-ChronologyCapability {
  param([object]$SchemaPacks,[string]$Capability)
  if(-not (Test-SchemaPackCapabilityEnabled $SchemaPacks $Capability)){throw "Chronology registry requires enabled capability '$Capability'."}
}

function Get-ChronologyPositionKey {
  param([object]$Position,[object]$Eras)
  if($null -eq $Position.era_id){return @([int64]$Position.value)}
  return @([int64]$Eras[$Position.era_id].ordinal,[int64]$Position.value)
}

function Compare-ChronologyKey {
  param([object[]]$Left,[object[]]$Right)
  $count=[Math]::Min($Left.Count,$Right.Count)
  for($i=0;$i -lt $count;$i++){
    if([int64]$Left[$i] -lt [int64]$Right[$i]){return -1}
    if([int64]$Left[$i] -gt [int64]$Right[$i]){return 1}
  }
  return $Left.Count.CompareTo($Right.Count)
}

function Add-KnowledgeChronologyGraphEdge {
  param([System.Collections.IDictionary]$Graph,[string]$SourceId,[string]$TargetId)
  if(-not $Graph.Contains($SourceId)){$Graph[$SourceId]=@()}
  if(@($Graph[$SourceId]) -cnotcontains $TargetId){$Graph[$SourceId]=@($Graph[$SourceId])+$TargetId}
}

function Test-KnowledgeChronologyGraphReachable {
  param([System.Collections.IDictionary]$Graph,[string]$SourceId,[string]$TargetId)
  $pending=New-Object 'System.Collections.Generic.Stack[string]'
  if($Graph.Contains($SourceId)){foreach($nextId in @($Graph[$SourceId])){$pending.Push([string]$nextId)}}
  $seen=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  while($pending.Count -gt 0){$current=$pending.Pop();if($current -ceq $TargetId){return $true};if(-not $seen.Add($current)){continue};if($Graph.Contains($current)){foreach($nextId in @($Graph[$current])){$pending.Push([string]$nextId)}}}
  return $false
}

function Get-KnowledgeChronologyComparison {
  param([object]$ChronologyRegistry,[string]$LeftId,[string]$RightId)
  if(-not $ChronologyRegistry.positions.Contains($LeftId)){throw "Unknown chronology position '$LeftId'."}
  if(-not $ChronologyRegistry.positions.Contains($RightId)){throw "Unknown chronology position '$RightId'."}
  if($LeftId -ceq $RightId){return 'concurrent'}
  if($ChronologyRegistry.PSObject.Properties.Name -contains 'equivalence_classes' -and $ChronologyRegistry.equivalence_classes.Count -gt 0){
    $leftClass=[string]$ChronologyRegistry.equivalence_classes[$LeftId];$rightClass=[string]$ChronologyRegistry.equivalence_classes[$RightId]
    if($leftClass -ceq $rightClass){return 'concurrent'}
    if(Test-KnowledgeChronologyGraphReachable $ChronologyRegistry.order_edges $leftClass $rightClass){return 'before'}
    if(Test-KnowledgeChronologyGraphReachable $ChronologyRegistry.order_edges $rightClass $leftClass){return 'after'}
    return 'incomparable'
  }
  $left=$ChronologyRegistry.positions[$LeftId];$right=$ChronologyRegistry.positions[$RightId]
  if($left.coordinate_system_id -ceq $right.coordinate_system_id){
    $system=$ChronologyRegistry.coordinate_systems[$left.coordinate_system_id]
    if($null -ne $left.era_id -and $null -ne $right.era_id){
      $leftEra=$ChronologyRegistry.eras[$left.era_id];$rightEra=$ChronologyRegistry.eras[$right.era_id]
      if($leftEra.ordinal -ne $rightEra.ordinal){return $(if($leftEra.ordinal -lt $rightEra.ordinal){'before'}else{'after'})}
      $direction=$leftEra.direction
    }else{$direction=$system.direction}
    if($left.value -eq $right.value){return 'concurrent'}
    $before=$left.value -lt $right.value
    if($direction -ceq 'descending'){$before=-not $before}
    return $(if($before){'before'}else{'after'})
  }
  foreach($pair in @(@($left,$right),@($right,$left))){$relative=$pair[0];$origin=$pair[1];$relativeSystem=$ChronologyRegistry.coordinate_systems[$relative.coordinate_system_id];if($relativeSystem.kind -ceq 'relative' -and $relative.value -eq 0 -and $relativeSystem.origin_position_id -ceq $origin.id -and $relative.certainty -ceq 'exact' -and $origin.certainty -ceq 'exact'){return 'concurrent'}}
  foreach($mapping in @($ChronologyRegistry.mappings)){
    if($mapping.mapping_kind -ceq 'equivalent' -and $mapping.certainty -ceq 'exact' -and (($mapping.source_position_id -ceq $LeftId -and $mapping.target_position_id -ceq $RightId) -or ($mapping.source_position_id -ceq $RightId -and $mapping.target_position_id -ceq $LeftId))){return 'concurrent'}
  }
  foreach($relation in @($ChronologyRegistry.relations)){
    if($relation.certainty -cne 'exact'){continue}
    if($relation.source_position_id -ceq $LeftId -and $relation.target_position_id -ceq $RightId){return $relation.relation_type}
    if($relation.source_position_id -ceq $RightId -and $relation.target_position_id -ceq $LeftId){
      if($relation.relation_type -ceq 'before'){return 'after'}
      if($relation.relation_type -ceq 'after'){return 'before'}
      return $relation.relation_type
    }
  }
  return 'incomparable'
}

function ConvertTo-KnowledgeChronologyRegistry {
  param(
    [object]$Data,[string]$Path,[object]$SchemaPacks,
    [string[]]$WorkIds=$null,[string[]]$ContinuityIds=$null
  )
  Assert-ChronologyCapability $SchemaPacks 'chronology-coordinate-systems'
  if($Data -isnot [System.Collections.IDictionary]){throw 'Chronology registry root must be a mapping.'}
  Assert-KnowledgeMapKeys $Data @('schema_version','coordinate_systems','eras','positions','spans','relations','mappings','narrative_contexts') 'Chronology registry root'
  $schemaVersion=Get-ProjectMapValue $Data 'schema_version'
  if($schemaVersion -isnot [int] -or $schemaVersion -ne $script:SupportedChronologySchemaVersion){throw "Unsupported chronology schema_version '$schemaVersion'; expected $($script:SupportedChronologySchemaVersion)."}

  $rawSystems=Get-ProjectMapValue $Data 'coordinate_systems'
  if($rawSystems -isnot [System.Collections.IDictionary] -or $rawSystems.Count -eq 0){throw 'chronology.coordinate_systems cannot be empty.'}
  $systems=[ordered]@{}
  foreach($systemId in @($rawSystems.Keys)){
    $null=Assert-ChronologyStableId ([string]$systemId) 'chronology coordinate-system ID'
    $context="coordinate_systems.$systemId";$item=$rawSystems[$systemId]
    if($item -isnot [System.Collections.IDictionary]){throw "$context must be a mapping."}
    Assert-KnowledgeMapKeys $item @('label','kind','value_domain','direction','zero_policy','aliases','origin_position_id') $context
    $kind=Get-RequiredChronologyString $item 'kind' $context;$domain=Get-RequiredChronologyString $item 'value_domain' $context;$direction=Get-RequiredChronologyString $item 'direction' $context;$zero=Get-RequiredChronologyString $item 'zero_policy' $context
    Assert-ChronologyPackValue $SchemaPacks 'chronology.coordinate-kind' $kind "$context.kind";Assert-ChronologyPackValue $SchemaPacks 'chronology.value-domain' $domain "$context.value_domain";Assert-ChronologyPackValue $SchemaPacks 'chronology.direction' $direction "$context.direction";Assert-ChronologyPackValue $SchemaPacks 'chronology.zero-policy' $zero "$context.zero_policy"
    $origin=Get-OptionalChronologyString $item 'origin_position_id' $context
    if($null -ne $origin){$null=Assert-ChronologyStableId $origin "$context.origin_position_id"}
    if($kind -ceq 'relative' -and $null -eq $origin){throw "$context.origin_position_id is required for relative coordinates."}
    if($kind -cne 'relative' -and $null -ne $origin){throw "$context.origin_position_id is only valid for relative coordinates."}
    if($zero -ceq 'absent' -and $domain -cne 'positive-integer'){throw "$context with absent zero must use positive-integer values."}
    $systems[$systemId]=[pscustomobject]@{id=[string]$systemId;label=Get-RequiredChronologyString $item 'label' $context;kind=$kind;value_domain=$domain;direction=$direction;zero_policy=$zero;aliases=@(Get-ChronologyStringList $item 'aliases' $context);origin_position_id=$origin}
  }

  $rawEras=Get-ProjectMapValue $Data 'eras';if($rawEras -isnot [System.Collections.IDictionary]){throw 'chronology.eras must be a mapping.'}
  $eras=[ordered]@{};$eraOrdinals=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach($eraId in @($rawEras.Keys)){
    $null=Assert-ChronologyStableId ([string]$eraId) 'chronology era ID';$context="eras.$eraId";$item=$rawEras[$eraId]
    if($item -isnot [System.Collections.IDictionary]){throw "$context must be a mapping."};Assert-KnowledgeMapKeys $item @('coordinate_system_id','label','ordinal','aliases','direction') $context
    $systemId=Get-RequiredChronologyString $item 'coordinate_system_id' $context;if(-not $systems.Contains($systemId)){throw "$context.coordinate_system_id references unknown coordinate system '$systemId'."};if($systems[$systemId].kind -cne 'era-ordinal'){throw "$context can only belong to an era-ordinal coordinate system."}
    $ordinal=Get-ProjectMapValue $item 'ordinal';if($ordinal -isnot [int] -or $ordinal -lt 1){throw "$context.ordinal must be a positive integer."};if(-not $eraOrdinals.Add("$systemId|$ordinal")){throw "$context.ordinal duplicates ordinal $ordinal in '$systemId'."}
    $eraDirection=Get-OptionalChronologyString $item 'direction' $context;if($null -eq $eraDirection){$eraDirection=[string]$systems[$systemId].direction};Assert-ChronologyPackValue $SchemaPacks 'chronology.direction' $eraDirection "$context.direction"
    $eras[$eraId]=[pscustomobject]@{id=[string]$eraId;coordinate_system_id=$systemId;label=Get-RequiredChronologyString $item 'label' $context;ordinal=[int]$ordinal;aliases=@(Get-ChronologyStringList $item 'aliases' $context);direction=$eraDirection}
  }

  $rawPositions=Get-ProjectMapValue $Data 'positions';if($rawPositions -isnot [System.Collections.IDictionary]){throw 'chronology.positions must be a mapping.'}
  $positions=[ordered]@{};$occupied=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach($positionId in @($rawPositions.Keys)){
    $null=Assert-ChronologyStableId ([string]$positionId) 'chronology position ID';$context="positions.$positionId";$item=$rawPositions[$positionId]
    if($item -isnot [System.Collections.IDictionary]){throw "$context must be a mapping."};Assert-KnowledgeMapKeys $item @('coordinate_system_id','value','era_id','label','certainty') $context
    $systemId=Get-RequiredChronologyString $item 'coordinate_system_id' $context;if(-not $systems.Contains($systemId)){throw "$context.coordinate_system_id references unknown coordinate system '$systemId'."};$system=$systems[$systemId]
    $value=Get-ProjectMapValue $item 'value';if($value -isnot [int]){throw "$context.value must be an integer."};if($system.value_domain -ceq 'nonnegative-integer' -and $value -lt 0){throw "$context.value must be nonnegative."};if($system.value_domain -ceq 'positive-integer' -and $value -lt 1){throw "$context.value must be positive."};if($system.zero_policy -ceq 'absent' -and $value -eq 0){throw "$context.value cannot use zero in '$systemId'."}
    $eraId=Get-OptionalChronologyString $item 'era_id' $context
    if($system.kind -ceq 'era-ordinal'){if($null -eq $eraId -or -not $eras.Contains($eraId) -or $eras[$eraId].coordinate_system_id -cne $systemId){throw "$context.era_id must reference an era in '$systemId'."}}elseif($null -ne $eraId){throw "$context.era_id is only valid for era-ordinal coordinates."}
    if(-not $occupied.Add("$systemId|$eraId|$value")){throw "$context duplicates an existing coordinate."}
    $certainty=Get-RequiredChronologyString $item 'certainty' $context;Assert-ChronologyPackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty"
    $positions[$positionId]=[pscustomobject]@{id=[string]$positionId;coordinate_system_id=$systemId;value=[int64]$value;era_id=$eraId;label=Get-OptionalChronologyString $item 'label' $context;certainty=$certainty}
  }
  foreach($system in @($systems.Values)){if($null -ne $system.origin_position_id){if(-not $positions.Contains($system.origin_position_id)){throw "coordinate_systems.$($system.id).origin_position_id references unknown position '$($system.origin_position_id)'."};if($positions[$system.origin_position_id].coordinate_system_id -ceq $system.id){throw "coordinate_systems.$($system.id).origin_position_id must use another coordinate system."}}}
  $originEdges=[ordered]@{};foreach($system in @($systems.Values)){if($null -ne $system.origin_position_id){$originEdges[$system.id]=[string]$positions[$system.origin_position_id].coordinate_system_id}}
  foreach($systemId in @($originEdges.Keys)){$seen=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$current=[string]$systemId;while($originEdges.Contains($current)){if(-not $seen.Add($current)){throw "Chronology relative-origin cycle includes coordinate system '$current'."};$current=[string]$originEdges[$current]}}

  $spans=@();$rawSpans=Get-ProjectMapValue $Data 'spans';if($null -eq $rawSpans){$rawSpans=@()}elseif($rawSpans -is [System.Collections.IDictionary]){$rawSpans=@($rawSpans)}elseif($rawSpans -isnot [System.Collections.IList]){throw 'chronology.spans must be a list.'};$seenSpans=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for($i=0;$i -lt $rawSpans.Count;$i++){$context="spans[$i]";$item=$rawSpans[$i];if($item -isnot [System.Collections.IDictionary]){throw "$context must be a mapping."};Assert-KnowledgeMapKeys $item @('id','coordinate_system_id','start_position_id','end_position_id','start_inclusive','end_inclusive','certainty') $context;$id=Assert-ChronologyStableId (Get-RequiredChronologyString $item 'id' $context) "$context.id";if(-not $seenSpans.Add($id)){throw "$context.id duplicates '$id'."};$systemId=Get-RequiredChronologyString $item 'coordinate_system_id' $context;if(-not $systems.Contains($systemId)){throw "$context.coordinate_system_id references unknown coordinate system '$systemId'."};$start=Get-OptionalChronologyString $item 'start_position_id' $context;$end=Get-OptionalChronologyString $item 'end_position_id' $context;if($null -eq $start -and $null -eq $end){throw "$context requires at least one endpoint."};foreach($endpoint in @(@('start_position_id',$start),@('end_position_id',$end))){if($null -ne $endpoint[1] -and (-not $positions.Contains([string]$endpoint[1]) -or $positions[[string]$endpoint[1]].coordinate_system_id -cne $systemId)){throw "$context.$($endpoint[0]) must reference a position in '$systemId'."}};$startInclusive=Get-ProjectMapValue $item 'start_inclusive';$endInclusive=Get-ProjectMapValue $item 'end_inclusive';if($startInclusive -isnot [bool] -or $endInclusive -isnot [bool]){throw "$context inclusivity fields must be true or false."};$certainty=Get-RequiredChronologyString $item 'certainty' $context;Assert-ChronologyPackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty";$spans += [pscustomobject]@{id=$id;coordinate_system_id=$systemId;start_position_id=$start;end_position_id=$end;start_inclusive=[bool]$startInclusive;end_inclusive=[bool]$endInclusive;certainty=$certainty}}

  $relations=@();$mappings=@();$seenIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $rawRelations=Get-ProjectMapValue $Data 'relations';if($null -eq $rawRelations){$rawRelations=@()}elseif($rawRelations -is [System.Collections.IDictionary]){$rawRelations=@($rawRelations)}elseif($rawRelations -isnot [System.Collections.IList]){throw 'chronology.relations must be a list.'}
  for($i=0;$i -lt $rawRelations.Count;$i++){$context="relations[$i]";$item=$rawRelations[$i];if($item -isnot [System.Collections.IDictionary]){throw "$context must be a mapping."};Assert-KnowledgeMapKeys $item @('id','source_position_id','relation_type','target_position_id','certainty') $context;$id=Assert-ChronologyStableId (Get-RequiredChronologyString $item 'id' $context) "$context.id";if(-not $seenIds.Add($id)){throw "$context.id duplicates '$id'."};$source=Get-RequiredChronologyString $item 'source_position_id' $context;$target=Get-RequiredChronologyString $item 'target_position_id' $context;if(-not $positions.Contains($source) -or -not $positions.Contains($target) -or $source -ceq $target){throw "$context must reference two distinct known positions."};$type=Get-RequiredChronologyString $item 'relation_type' $context;$certainty=Get-RequiredChronologyString $item 'certainty' $context;Assert-ChronologyPackValue $SchemaPacks 'chronology.relation-type' $type "$context.relation_type";Assert-ChronologyPackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty";$relations += [pscustomobject]@{id=$id;source_position_id=$source;relation_type=$type;target_position_id=$target;certainty=$certainty}}
  $rawMappings=Get-ProjectMapValue $Data 'mappings';if($null -eq $rawMappings){$rawMappings=@()}elseif($rawMappings -is [System.Collections.IDictionary]){$rawMappings=@($rawMappings)}elseif($rawMappings -isnot [System.Collections.IList]){throw 'chronology.mappings must be a list.'}
  for($i=0;$i -lt $rawMappings.Count;$i++){$context="mappings[$i]";$item=$rawMappings[$i];if($item -isnot [System.Collections.IDictionary]){throw "$context must be a mapping."};Assert-KnowledgeMapKeys $item @('id','source_position_id','mapping_kind','target_position_id','certainty') $context;$id=Assert-ChronologyStableId (Get-RequiredChronologyString $item 'id' $context) "$context.id";if(-not $seenIds.Add($id)){throw "$context.id duplicates '$id'."};$source=Get-RequiredChronologyString $item 'source_position_id' $context;$target=Get-RequiredChronologyString $item 'target_position_id' $context;if(-not $positions.Contains($source) -or -not $positions.Contains($target) -or $source -ceq $target){throw "$context must reference two distinct known positions."};if($positions[$source].coordinate_system_id -ceq $positions[$target].coordinate_system_id){throw "$context must map positions in different coordinate systems."};$kind=Get-RequiredChronologyString $item 'mapping_kind' $context;$certainty=Get-RequiredChronologyString $item 'certainty' $context;Assert-ChronologyPackValue $SchemaPacks 'chronology.mapping-kind' $kind "$context.mapping_kind";Assert-ChronologyPackValue $SchemaPacks 'temporal.certainty' $certainty "$context.certainty";$mappings += [pscustomobject]@{id=$id;source_position_id=$source;mapping_kind=$kind;target_position_id=$target;certainty=$certainty}}

  $contexts=@();$rawContexts=Get-ProjectMapValue $Data 'narrative_contexts';if($null -eq $rawContexts){$rawContexts=@()}elseif($rawContexts -is [System.Collections.IDictionary]){$rawContexts=@($rawContexts)}elseif($rawContexts -isnot [System.Collections.IList]){throw 'chronology.narrative_contexts must be a list.'};if($rawContexts.Count -gt 0){Assert-ChronologyCapability $SchemaPacks 'narrative-chronology'};$seenContexts=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for($i=0;$i -lt $rawContexts.Count;$i++){$context="narrative_contexts[$i]";$item=$rawContexts[$i];if($item -isnot [System.Collections.IDictionary]){throw "$context must be a mapping."};Assert-KnowledgeMapKeys $item @('id','label','coordinate_system_id','role','continuity_ids','work_ids','branch_id') $context;$id=Assert-ChronologyStableId (Get-RequiredChronologyString $item 'id' $context) "$context.id";if(-not $seenContexts.Add($id)){throw "$context.id duplicates '$id'."};$systemId=Get-RequiredChronologyString $item 'coordinate_system_id' $context;if(-not $systems.Contains($systemId)){throw "$context.coordinate_system_id references unknown coordinate system '$systemId'."};$role=Get-RequiredChronologyString $item 'role' $context;Assert-ChronologyPackValue $SchemaPacks 'narrative.chronology-role' $role "$context.role";$contextWorks=@(Get-ChronologyStringList $item 'work_ids' $context);$contextContinuities=@(Get-ChronologyStringList $item 'continuity_ids' $context);if($contextWorks.Count -eq 0 -and $contextContinuities.Count -eq 0){throw "$context must name at least one work or continuity."};if($null -eq $WorkIds -or $null -eq $ContinuityIds){throw 'Narrative chronology contexts require composed work and continuity targets.'};$unknownWorks=@($contextWorks|Where-Object {$WorkIds -cnotcontains $_});$unknownContinuities=@($contextContinuities|Where-Object {$ContinuityIds -cnotcontains $_});if($unknownWorks.Count -gt 0){throw "$context.work_ids references unknown works: $($unknownWorks -join ', ')."};if($unknownContinuities.Count -gt 0){throw "$context.continuity_ids references unknown continuities: $($unknownContinuities -join ', ')."};$branch=Get-OptionalChronologyString $item 'branch_id' $context;if($null -ne $branch){$null=Assert-ChronologyStableId $branch "$context.branch_id"};$contexts += [pscustomobject]@{id=$id;label=Get-RequiredChronologyString $item 'label' $context;coordinate_system_id=$systemId;role=$role;continuity_ids=@($contextContinuities);work_ids=@($contextWorks);branch_id=$branch}}

  $baseRegistry=[pscustomobject]@{path=$Path;schema_version=[int]$schemaVersion;coordinate_systems=$systems;eras=$eras;positions=$positions;spans=@($spans);relations=@($relations);mappings=@($mappings);narrative_contexts=@($contexts)}
  foreach($span in @($spans)){if($null -ne $span.start_position_id -and $null -ne $span.end_position_id){$ordering=Get-KnowledgeChronologyComparison $baseRegistry $span.start_position_id $span.end_position_id;if($ordering -ceq 'after' -or ($ordering -ceq 'concurrent' -and -not ($span.start_inclusive -and $span.end_inclusive))){throw "Chronology span '$($span.id)' has an empty or reversed span."}}}

  $equivalenceAdj=[ordered]@{};foreach($positionId in @($positions.Keys)){$equivalenceAdj[$positionId]=@()}
  foreach($system in @($systems.Values)){if($system.kind -ceq 'relative' -and $null -ne $system.origin_position_id){$origin=$positions[$system.origin_position_id];foreach($position in @($positions.Values)){if($position.coordinate_system_id -ceq $system.id -and $position.value -eq 0 -and $position.certainty -ceq 'exact' -and $origin.certainty -ceq 'exact'){Add-KnowledgeChronologyGraphEdge $equivalenceAdj $position.id $origin.id;Add-KnowledgeChronologyGraphEdge $equivalenceAdj $origin.id $position.id}}}}
  foreach($mapping in @($mappings)){if($mapping.mapping_kind -ceq 'equivalent' -and $mapping.certainty -ceq 'exact'){Add-KnowledgeChronologyGraphEdge $equivalenceAdj $mapping.source_position_id $mapping.target_position_id;Add-KnowledgeChronologyGraphEdge $equivalenceAdj $mapping.target_position_id $mapping.source_position_id}}
  foreach($relation in @($relations)){if($relation.relation_type -ceq 'concurrent' -and $relation.certainty -ceq 'exact'){Add-KnowledgeChronologyGraphEdge $equivalenceAdj $relation.source_position_id $relation.target_position_id;Add-KnowledgeChronologyGraphEdge $equivalenceAdj $relation.target_position_id $relation.source_position_id}}

  $classes=[ordered]@{};foreach($positionId in @($positions.Keys|Sort-Object -CaseSensitive)){if($classes.Contains($positionId)){continue};$queue=New-Object 'System.Collections.Generic.Queue[string]';$queue.Enqueue([string]$positionId);$component=@();while($queue.Count -gt 0){$current=$queue.Dequeue();if($component -ccontains $current){continue};$component+=([string]$current);foreach($nextId in @($equivalenceAdj[$current])){if($component -cnotcontains $nextId){$queue.Enqueue([string]$nextId)}}};$classId=[string](@($component|Sort-Object -CaseSensitive)[0]);foreach($memberId in @($component)){$classes[$memberId]=$classId}}

  $orderEdges=[ordered]@{}
  foreach($systemId in @($systems.Keys)){ $systemPositions=@($positions.Values|Where-Object {$_.coordinate_system_id -ceq $systemId});for($i=0;$i -lt $systemPositions.Count;$i++){for($j=$i+1;$j -lt $systemPositions.Count;$j++){$left=$systemPositions[$i];$right=$systemPositions[$j];$comparison=Get-KnowledgeChronologyComparison $baseRegistry $left.id $right.id;$edgeSource=$(if($comparison -ceq 'before'){$left.id}else{$right.id});$edgeTarget=$(if($comparison -ceq 'before'){$right.id}else{$left.id});$sourceClass=[string]$classes[$edgeSource];$targetClass=[string]$classes[$edgeTarget];if($sourceClass -ceq $targetClass){throw "Intrinsic chronology contradicts exact equivalence between '$edgeSource' and '$edgeTarget'."};Add-KnowledgeChronologyGraphEdge $orderEdges $sourceClass $targetClass}}}

  $exactPairs=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$exactIncomparables=@()
  foreach($relation in @($relations)){
    if($relation.certainty -cne 'exact'){continue}
    $pair=@($relation.source_position_id,$relation.target_position_id)|Sort-Object -CaseSensitive;$pairKey="$($pair[0])|$($pair[1])"
    if(-not $exactPairs.Add($pairKey)){throw "Chronology relation '$($relation.id)' duplicates an exact relation between '$($pair[0])' and '$($pair[1])'."}
    $edgeSource=$null;$edgeTarget=$null;if($relation.relation_type -ceq 'before'){$edgeSource=$relation.source_position_id;$edgeTarget=$relation.target_position_id}elseif($relation.relation_type -ceq 'after'){$edgeSource=$relation.target_position_id;$edgeTarget=$relation.source_position_id}elseif($relation.relation_type -ceq 'incomparable'){$exactIncomparables+=,$relation}
    if($null -ne $edgeSource){$sourceClass=[string]$classes[$edgeSource];$targetClass=[string]$classes[$edgeTarget];if($sourceClass -ceq $targetClass){throw "Chronology relation '$($relation.id)' contradicts exact equivalence between '$edgeSource' and '$edgeTarget'."};Add-KnowledgeChronologyGraphEdge $orderEdges $sourceClass $targetClass}
  }
  $indegree=[ordered]@{};foreach($classId in @($classes.Values|Sort-Object -Unique -CaseSensitive)){$indegree[$classId]=0};foreach($sourceId in @($orderEdges.Keys)){foreach($targetId in @($orderEdges[$sourceId])){$indegree[$targetId]=[int]$indegree[$targetId]+1}}
  $ready=New-Object 'System.Collections.Generic.Queue[string]';foreach($classId in @($indegree.Keys|Sort-Object -CaseSensitive)){if([int]$indegree[$classId] -eq 0){$ready.Enqueue([string]$classId)}};$processed=0
  while($ready.Count -gt 0){$classId=$ready.Dequeue();$processed++;if($orderEdges.Contains($classId)){foreach($targetId in @($orderEdges[$classId])){$indegree[$targetId]=[int]$indegree[$targetId]-1;if([int]$indegree[$targetId] -eq 0){$ready.Enqueue([string]$targetId)}}}}
  if($processed -ne $indegree.Count){throw 'Combined exact chronology contains a before/after cycle.'}
  $registry=[pscustomobject]@{path=$Path;schema_version=[int]$schemaVersion;coordinate_systems=$systems;eras=$eras;positions=$positions;spans=@($spans);relations=@($relations);mappings=@($mappings);narrative_contexts=@($contexts);equivalence_classes=$classes;order_edges=$orderEdges}
  foreach($relation in @($exactIncomparables)){if((Get-KnowledgeChronologyComparison $registry $relation.source_position_id $relation.target_position_id) -cne 'incomparable'){throw "Chronology relation '$($relation.id)' contradicts derived exact order."}}
  return $registry
}

function Get-KnowledgeChronologyRegistry {
  param([object]$Project,[object]$SchemaPacks,[string[]]$WorkIds=$null,[string[]]$ContinuityIds=$null)
  $data=ConvertFrom-KnowledgeYamlFile $Project.chronology_registry $script:SupportedChronologySchemaVersion 'chronology registry'
  return ConvertTo-KnowledgeChronologyRegistry $data $Project.chronology_registry $SchemaPacks $WorkIds $ContinuityIds
}
