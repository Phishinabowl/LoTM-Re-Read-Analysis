$sourceConfigHelper = Join-Path $PSScriptRoot "Source-Config.ps1"
if (-not (Get-Command Get-KnowledgeSourceProvenanceTarget -ErrorAction SilentlyContinue)) { . $sourceConfigHelper }
$entityConfigHelper = Join-Path $PSScriptRoot "Entity-Config.ps1"
if (-not (Get-Command Get-KnowledgeEntityProvenanceTarget -ErrorAction SilentlyContinue)) { . $entityConfigHelper }
$reconciliationConfigHelper = Join-Path $PSScriptRoot "Reconciliation-Config.ps1"
if (-not (Get-Command Get-KnowledgeReconciliationProvenanceTarget -ErrorAction SilentlyContinue)) { . $reconciliationConfigHelper }
$chronologyConfigHelper = Join-Path $PSScriptRoot "Chronology-Config.ps1"
if (-not (Get-Command Get-KnowledgeChronologyRegistry -ErrorAction SilentlyContinue)) { . $chronologyConfigHelper }
$occurrenceConfigHelper = Join-Path $PSScriptRoot "Occurrence-Config.ps1"
if (-not (Get-Command Get-KnowledgeOccurrenceProvenanceTargets -ErrorAction SilentlyContinue)) { . $occurrenceConfigHelper }

$script:SupportedProvenanceSchemaVersion = 3
$script:ProvenanceFieldPathPattern = "^[a-z][a-z0-9_]*(?:(?:\.[a-z][a-z0-9_]*)|(?:\[[0-9]+\]))*$"

function Get-KnowledgeProvenanceTarget {
  param([object]$ProvenanceRegistry,[string]$SubjectType,[string]$SubjectId)
  if($SubjectType -eq "claim-supersession"){
    $target=@($ProvenanceRegistry.claim_supersessions|Where-Object {$_.id -eq $SubjectId})
    if($target.Count -eq 0){throw "Unknown claim-supersession '$SubjectId'."}
    return $target[0]
  }
  try{return Get-KnowledgeSourceProvenanceTarget $ProvenanceRegistry.sources $SubjectType $SubjectId}catch{if($_.Exception.Message -notlike "Unsupported source-registry*"){throw}}
  try{return Get-KnowledgeEntityProvenanceTarget $ProvenanceRegistry.entities $SubjectType $SubjectId}catch{if($_.Exception.Message -notlike "Unsupported entity-registry*"){throw}}
  try{return Get-KnowledgeReconciliationProvenanceTarget $ProvenanceRegistry.reconciliations $SubjectType $SubjectId}catch{if($_.Exception.Message -notlike "Unsupported reconciliation provenance*"){throw}}
  $occurrenceTargets=Get-KnowledgeOccurrenceProvenanceTargets $ProvenanceRegistry.occurrences
  if($occurrenceTargets.Contains($SubjectType)){if(-not $occurrenceTargets[$SubjectType].Contains($SubjectId)){throw "Unknown $SubjectType '$SubjectId'."};return $occurrenceTargets[$SubjectType][$SubjectId]}
  throw "Unsupported provenance subject type '$SubjectType'."
}

function Resolve-ProvenanceRecordFieldPath {
  param([object]$Record,[string]$FieldPath,[string]$Context)
  $current=$Record
  foreach($match in [regex]::Matches($FieldPath,'[a-z][a-z0-9_]*|\[[0-9]+\]')){
    $token=$match.Value
    if($token.StartsWith('[')){$index=[int]$token.Substring(1,$token.Length-2);if($current -isnot [System.Collections.IList] -or $index -ge $current.Count){throw "Provenance registry '$Context' does not resolve on its subject."};$current=$current[$index];continue}
    $value=Get-ProjectMapValue $current $token ([System.DBNull]::Value);if($value -is [System.DBNull]){throw "Provenance registry '$Context' does not resolve on its subject."};$current=$value
  }
  return $current
}

function ConvertTo-ProvenanceLocator {
  param([object]$Raw,[string]$Context,[string]$SourceId,[object]$Sources,[object]$SchemaPacks)
  if($Raw -isnot [System.Collections.IDictionary]){throw "Provenance registry '$Context' must be a mapping."};Assert-KnowledgeMapKeys $Raw @("id","medium_id","evidence_mode","locator_type","position","start","end") "Provenance registry '$Context'"
  $id=Get-RequiredSourceString $Raw "id" $Context;Test-StableSourceId $id "$Context.id"
  $mediumId=Get-RequiredSourceString $Raw "medium_id" $Context
  if(-not $Sources.mediums.Contains($mediumId)){throw "Provenance registry '$Context.medium_id' references unknown medium '$mediumId'."}
  $source=$Sources.sources[$SourceId]
  if($source.locator_medium_ids -cnotcontains $mediumId){throw "Provenance registry '$Context.medium_id' is not allowed by the evidence source."}
  $evidenceMode=Get-RequiredSourceString $Raw "evidence_mode" $Context
  if($source.evidence_modes -cnotcontains $evidenceMode){throw "Provenance registry '$Context.evidence_mode' is not declared by the evidence source."}
  $locatorType=Get-RequiredSourceString $Raw "locator_type" $Context
  Assert-SourceSchemaPackValues $SchemaPacks "provenance.locator-type" @($locatorType) "$Context.locator_type"
  $medium=$Sources.mediums[$mediumId]
  if($locatorType -eq "point"){
    if($null -ne (Get-ProjectMapValue $Raw "start") -or $null -ne (Get-ProjectMapValue $Raw "end")){throw "Provenance registry '$Context' point locator cannot declare start or end."}
    $position=Get-ProjectMapValue $Raw "position"
    Assert-SourceEvidencePosition $position $medium @($source.work_ids) $Sources.works $Sources.segments $Sources.ordering_schemes "$Context.position"
    Assert-SourceLocatorCoverage $source $medium $evidenceMode @($position) $Sources.segments $Sources.content_groups $Sources.manifestations $Sources.release_components $Sources.release_packages $Sources.ordering_schemes $Context
    return [pscustomobject]@{id=$id;medium_id=$mediumId;evidence_mode=$evidenceMode;locator_type=$locatorType;position=$position;start=$null;end=$null}
  }
  if($null -ne (Get-ProjectMapValue $Raw "position")){throw "Provenance registry '$Context' range locator cannot declare position."}
  $start=Get-ProjectMapValue $Raw "start";$end=Get-ProjectMapValue $Raw "end"
  Assert-SourceEvidencePosition $start $medium @($source.work_ids) $Sources.works $Sources.segments $Sources.ordering_schemes "$Context.start"
  Assert-SourceEvidencePosition $end $medium @($source.work_ids) $Sources.works $Sources.segments $Sources.ordering_schemes "$Context.end"
  $startFields=@($start.Keys|Sort-Object);$endFields=@($end.Keys|Sort-Object)
  if(($startFields -join "|") -ne ($endFields -join "|")){throw "Provenance registry '$Context' range start/end fields must be identical."}
  if([string]$start[$medium.work_scope_field] -ne [string]$end[$medium.work_scope_field]){throw "Provenance registry '$Context' range endpoints must identify the same work."}
  if((Compare-SourcePositions $start $end $medium $Sources.ordering_schemes $Context) -gt 0){throw "Provenance registry '$Context' range start must not follow end."}
  Assert-SourceLocatorCoverage $source $medium $evidenceMode @($start,$end) $Sources.segments $Sources.content_groups $Sources.manifestations $Sources.release_components $Sources.release_packages $Sources.ordering_schemes $Context
  return [pscustomobject]@{id=$id;medium_id=$mediumId;evidence_mode=$evidenceMode;locator_type=$locatorType;position=$null;start=$start;end=$end}
}

function Get-KnowledgeProvenanceRegistry {
  param([object]$ProjectConfig,[object]$SourceRegistry,[object]$EntityRegistry,[object]$ReconciliationRegistry,[object]$SchemaPackRegistry,[object]$OccurrenceRegistry=$null)
  if($null -eq $SchemaPackRegistry){$SchemaPackRegistry=Get-KnowledgeSchemaPackRegistry $ProjectConfig}
  if($null -eq $OccurrenceRegistry){$chronology=Get-KnowledgeChronologyRegistry $ProjectConfig $SchemaPackRegistry @($SourceRegistry.works.Keys) @($SourceRegistry.continuities.Keys);$OccurrenceRegistry=Get-KnowledgeOccurrenceRegistry $ProjectConfig $SchemaPackRegistry $chronology}
  $path=$ProjectConfig.provenance_registry
  $registry=ConvertFrom-KnowledgeYamlFile $path $script:SupportedProvenanceSchemaVersion "provenance registry"
  if($null -eq $registry -or $registry -isnot [System.Collections.IDictionary]){throw "Provenance registry root must be a mapping: $path"}
  Assert-KnowledgeMapKeys $registry @("schema_version","claim_supersessions","assertions") "Provenance registry root"
  $schemaVersion=Get-ProjectMapValue $registry "schema_version"
  if($schemaVersion -isnot [int] -or $schemaVersion -ne $script:SupportedProvenanceSchemaVersion){throw "Unsupported provenance schema_version '$schemaVersion'; expected $($script:SupportedProvenanceSchemaVersion)."}
  $sourceSubjectTypes=@(Get-KnowledgeSourceProvenanceSubjectTypes);$entitySubjectTypes=@(Get-KnowledgeEntityProvenanceSubjectTypes);$reconciliationSubjectTypes=@(Get-KnowledgeReconciliationProvenanceSubjectTypes);$occurrenceSubjectTypes=@((Get-KnowledgeOccurrenceProvenanceTargets $OccurrenceRegistry).Keys);$allProviderTypes=@($sourceSubjectTypes+$entitySubjectTypes+$reconciliationSubjectTypes+$occurrenceSubjectTypes);$duplicates=@($allProviderTypes|Group-Object|Where-Object Count -gt 1|ForEach-Object Name)
  if($duplicates.Count -gt 0){throw "Provenance subject types have multiple providers: $($duplicates -join ', ')."}
  $providedSubjectTypes=@($sourceSubjectTypes+$entitySubjectTypes+$reconciliationSubjectTypes+$occurrenceSubjectTypes+@("claim-supersession")|Sort-Object -Unique);$allowedSubjectTypes=@(Get-SchemaPackAllowedValues $SchemaPackRegistry "provenance.subject-type")
  $missingProviders=@($allowedSubjectTypes|Where-Object {$providedSubjectTypes -cnotcontains $_});$unregisteredProviders=@($providedSubjectTypes|Where-Object {$allowedSubjectTypes -cnotcontains $_})
  if($missingProviders.Count -gt 0 -or $unregisteredProviders.Count -gt 0){$details=@();if($missingProviders.Count -gt 0){$details+=@("missing providers: $($missingProviders -join ', ')")};if($unregisteredProviders.Count -gt 0){$details+=@("unregistered providers: $($unregisteredProviders -join ', ')")};throw "Provenance subject-provider mismatch ($($details -join '; '))."}

  $rawSupersessions=@(Get-ProjectMapValue $registry "claim_supersessions")
  $supersessions=@();$seenSupersessionIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for($i=0;$i -lt $rawSupersessions.Count;$i++){
    $context="claim_supersessions[$i]";$item=$rawSupersessions[$i]
    if($item -isnot [System.Collections.IDictionary]){throw "Provenance registry '$context' must be a mapping."};Assert-KnowledgeMapKeys $item @("id","source_claim_key","target_claim_key","relationship_type","applicability_scope_id","continuity_ids") "Provenance registry '$context'"
    $id=Get-RequiredSourceString $item "id" $context;Test-StableSourceId $id "$context.id";if(-not $seenSupersessionIds.Add($id)){throw "Provenance registry claim-supersession ID '$id' is duplicated."}
    $sourceClaim=Get-RequiredSourceString $item "source_claim_key" $context;$targetClaim=Get-RequiredSourceString $item "target_claim_key" $context;Test-StableSourceId $sourceClaim "$context.source_claim_key";Test-StableSourceId $targetClaim "$context.target_claim_key"
    if($sourceClaim -eq $targetClaim){throw "Provenance registry '$context' cannot supersede a claim with itself."}
    $relationshipType=Get-RequiredSourceString $item "relationship_type" $context;Assert-SourceSchemaPackValues $SchemaPackRegistry "narrative.claim-change-type" @($relationshipType) "$context.relationship_type"
    $scopeId=Get-RequiredSourceString $item "applicability_scope_id" $context;if(-not $SourceRegistry.applicability_scopes.Contains($scopeId)){throw "Provenance registry '$context.applicability_scope_id' references unknown scope '$scopeId'."}
    $scope=$SourceRegistry.applicability_scopes[$scopeId];if($scope.target_type -ne "provenance-claim" -or $scope.target_id -ne $targetClaim){throw "Provenance registry '$context' scope must target the superseded claim '$targetClaim'."}
    $continuityIds=@(Get-SourceStringListAllowEmpty $item "continuity_ids" $context);$unknown=@($continuityIds|Where-Object {-not $SourceRegistry.continuities.Contains($_)}|Sort-Object -Unique);if($unknown.Count -gt 0){throw "Provenance registry '$context.continuity_ids' references unknown continuities: $($unknown -join ', ')."}
    $supersessions+=,[pscustomobject]@{id=$id;source_claim_key=$sourceClaim;relationship_type=$relationshipType;target_claim_key=$targetClaim;applicability_scope_id=$scopeId;continuity_ids=@($continuityIds)}
  }

  $rawAssertions=@(Get-ProjectMapValue $registry "assertions")
  $assertions=@();$seenAssertionIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$seenLocatorIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$claimShapes=[ordered]@{}
  $shell=[pscustomobject]@{sources=$SourceRegistry;entities=$EntityRegistry;reconciliations=$ReconciliationRegistry;occurrences=$OccurrenceRegistry;claim_supersessions=@($supersessions)}
  for($i=0;$i -lt $rawAssertions.Count;$i++){
    $context="assertions[$i]";$item=$rawAssertions[$i]
    if($item -isnot [System.Collections.IDictionary]){throw "Provenance registry '$context' must be a mapping."};Assert-KnowledgeMapKeys $item @("id","claim_key","subject_type","subject_id","claim_namespace","field_path","asserted_value","assertion_status","observed_at","effective_window","evidence_links") "Provenance registry '$context'"
    $id=Get-RequiredSourceString $item "id" $context;Test-StableSourceId $id "$context.id";if(-not $seenAssertionIds.Add($id)){throw "Provenance registry assertion ID '$id' is duplicated."}
    $claimKey=Get-RequiredSourceString $item "claim_key" $context;Test-StableSourceId $claimKey "$context.claim_key"
    $subjectType=Get-RequiredSourceString $item "subject_type" $context;Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.subject-type" @($subjectType) "$context.subject_type";$subjectId=Get-RequiredSourceString $item "subject_id" $context
    $target=Get-KnowledgeProvenanceTarget $shell $subjectType $subjectId
    $namespace=Get-RequiredSourceString $item "claim_namespace" $context;Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.claim-namespace" @($namespace) "$context.claim_namespace"
    $fieldPath=Get-OptionalSourceString $item "field_path" $context;if($null -ne $fieldPath){if($fieldPath -cnotmatch $script:ProvenanceFieldPathPattern){throw "Provenance registry '$context.field_path' must be a dotted/indexed machine field path."};$null=Resolve-ProvenanceRecordFieldPath $target $fieldPath "$context.field_path"}
    $shape="$subjectType|$subjectId|$namespace|$fieldPath";if($claimShapes.Contains($claimKey) -and $claimShapes[$claimKey] -ne $shape){throw "Provenance registry claim key '$claimKey' is reused for a different subject, namespace, or field path."};$claimShapes[$claimKey]=$shape
    if(-not $item.Contains("asserted_value")){throw "Provenance registry '$context.asserted_value' is required, including when null."};$assertedValue=Get-ProjectMapValue $item "asserted_value"
    $status=Get-RequiredSourceString $item "assertion_status" $context;Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.assertion-status" @($status) "$context.assertion_status"
    $rawLinks=@(Get-ProjectMapValue $item "evidence_links");if($rawLinks.Count -eq 0){throw "Provenance registry '$context.evidence_links' must be a non-empty list."};$links=@();$seenSources=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for($j=0;$j -lt $rawLinks.Count;$j++){
      $linkContext="$context.evidence_links[$j]";$link=$rawLinks[$j];$sourceId=Get-RequiredSourceString $link "source_id" $linkContext;if(-not $SourceRegistry.sources.Contains($sourceId)){throw "Provenance registry '$linkContext.source_id' references unknown source '$sourceId'."};if(-not $seenSources.Add($sourceId)){throw "Provenance registry '$context.evidence_links' repeats source '$sourceId'."}
      if($link -isnot [System.Collections.IDictionary]){throw "Provenance registry '$linkContext' must be a mapping."};Assert-KnowledgeMapKeys $link @("source_id","evidence_role","locators") "Provenance registry '$linkContext'"
      $role=Get-RequiredSourceString $link "evidence_role" $linkContext;Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.evidence-role" @($role) "$linkContext.evidence_role";$rawLocators=@(Get-ProjectMapValue $link "locators");if($rawLocators.Count -eq 0){throw "Provenance registry '$linkContext.locators' must be a non-empty list."};$locators=@()
      for($k=0;$k -lt $rawLocators.Count;$k++){$locator=ConvertTo-ProvenanceLocator $rawLocators[$k] "$linkContext.locators[$k]" $sourceId $SourceRegistry $SchemaPackRegistry;if(-not $seenLocatorIds.Add([string]$locator.id)){throw "Provenance registry evidence-locator ID '$($locator.id)' is duplicated."};$locators+=,$locator}
      $links+=,[pscustomobject]@{source_id=$sourceId;evidence_role=$role;locators=@($locators)}
    }
    $roles=@($links|ForEach-Object {$_.evidence_role}|Sort-Object -Unique);if($status -in @("verified","inferred") -and $roles -cnotcontains "supports"){throw "Provenance registry '$context' status '$status' requires supporting evidence."};if($status -eq "disputed" -and ($roles -cnotcontains "supports" -or $roles -cnotcontains "contradicts")){throw "Provenance registry '$context' disputed status requires supporting and contradicting evidence."}
    $assertions+=,[pscustomobject]@{id=$id;claim_key=$claimKey;subject_type=$subjectType;subject_id=$subjectId;claim_namespace=$namespace;field_path=$fieldPath;asserted_value=$assertedValue;assertion_status=$status;observed_at=ConvertTo-KnowledgeTemporalWindow $item "observed_at" $context $SchemaPackRegistry;effective_window=ConvertTo-KnowledgeTemporalWindow $item "effective_window" $context $SchemaPackRegistry;evidence_links=@($links)}
  }
  foreach($scope in $SourceRegistry.applicability_scopes.Values){if($scope.target_type -eq "provenance-claim" -and -not $claimShapes.Contains($scope.target_id)){throw "Provenance registry applicability scope '$($scope.id)' references unknown provenance claim '$($scope.target_id)'."}}
  $edges=[ordered]@{};foreach($item in $supersessions){if(-not $claimShapes.Contains($item.source_claim_key) -or -not $claimShapes.Contains($item.target_claim_key)){throw "Provenance registry claim supersession '$($item.id)' references an unknown claim."};if($claimShapes[$item.source_claim_key] -ne $claimShapes[$item.target_claim_key]){throw "Provenance registry claim supersession '$($item.id)' must relate claims with the same subject, namespace, and field path."};if(-not $edges.Contains($item.source_claim_key)){$edges[$item.source_claim_key]=@()};$edges[$item.source_claim_key]=@($edges[$item.source_claim_key])+@($item.target_claim_key)}
  $visited=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$active=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  function Visit-ProvenanceClaim([string]$ClaimKey){if($active.Contains($ClaimKey)){throw "Provenance registry contains a claim-supersession cycle involving '$ClaimKey'."};if($visited.Contains($ClaimKey)){return};[void]$active.Add($ClaimKey);if($edges.Contains($ClaimKey)){foreach($target in @($edges[$ClaimKey])){Visit-ProvenanceClaim $target}};[void]$active.Remove($ClaimKey);[void]$visited.Add($ClaimKey)}
  foreach($claimKey in $edges.Keys){Visit-ProvenanceClaim $claimKey}
  return [pscustomobject]@{path=$path;schema_version=[int]$schemaVersion;assertions=@($assertions);claim_supersessions=@($supersessions);sources=$SourceRegistry;entities=$EntityRegistry;reconciliations=$ReconciliationRegistry;occurrences=$OccurrenceRegistry}
}

function Get-KnowledgeProvenanceApplicabilityDecision {
  param([object]$ProvenanceRegistry,[string]$TargetType,[string]$TargetId,[AllowNull()][AllowEmptyString()][string]$TerritoryId=$null,[object]$EffectiveAt=$null)
  if($TargetType -ne "provenance-claim"){return Get-KnowledgeApplicabilityDecision $ProvenanceRegistry.sources $TargetType $TargetId $TerritoryId $EffectiveAt}
  $assertions=@($ProvenanceRegistry.assertions|Where-Object {$_.claim_key -eq $TargetId});if($assertions.Count -eq 0){throw "Unknown provenance-claim applicability target '$TargetId'."}
  if(-not [string]::IsNullOrWhiteSpace($TerritoryId) -and -not $ProvenanceRegistry.sources.territories.Contains($TerritoryId)){throw "Unknown territory '$TerritoryId'."}
  $effective=ConvertTo-KnowledgeApplicabilityInstant $EffectiveAt;$effectiveQuery=$effective;$matches=@();$subjectType=[string]$assertions[0].subject_type;$subjectId=[string]$assertions[0].subject_id
  foreach($scope in $ProvenanceRegistry.sources.applicability_scopes.Values){
    if($scope.target_type -eq "provenance-claim" -and $scope.target_id -eq $TargetId){$targetMatch="exact"}else{$active=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$subjectMatch=Get-KnowledgeApplicabilityTargetMatch $ProvenanceRegistry.sources $scope.target_type $scope.target_id $subjectType $subjectId $active;if($null -eq $subjectMatch){continue};$targetMatch="claim-subject"}
    $territoryMatch=Get-KnowledgeApplicabilityTerritoryMatch $ProvenanceRegistry.sources $scope $TerritoryId;if($null -eq $territoryMatch){continue};$temporalMatch=Get-KnowledgeApplicabilityTemporalMatch $scope.effective_window $effectiveQuery;if($null -eq $temporalMatch){continue};$matches+=,[pscustomobject]@{scope_id=$scope.id;outcome=if(Test-KnowledgeTemporalMatchIndeterminate $temporalMatch){"indeterminate"}else{"applicable"};target_match=$targetMatch;territory_match=$territoryMatch;temporal_match=$temporalMatch;precedence=[int]$scope.precedence}
  }
  $matches=@($matches|Sort-Object @{Expression="precedence";Descending=$true},@{Expression="scope_id";Descending=$false});$applicable=@($matches|Where-Object {$_.outcome -eq "applicable"});$highest=if($applicable.Count -eq 0){$null}else{[int]$applicable[0].precedence};$winners=if($null -eq $highest){@()}else{@($applicable|Where-Object {$_.precedence -eq $highest}|ForEach-Object {$_.scope_id})}
  return [pscustomobject]@{target_type=$TargetType;target_id=$TargetId;territory_id=if([string]::IsNullOrWhiteSpace($TerritoryId)){$null}else{$TerritoryId};effective_at=if($null -eq $effective){$null}else{$effective.label};matching_scope_ids=@($applicable|ForEach-Object {$_.scope_id});indeterminate_scope_ids=@($matches|Where-Object {$_.outcome -eq "indeterminate"}|ForEach-Object {$_.scope_id});winning_scope_ids=@($winners);highest_precedence=$highest;ambiguous=($winners.Count -gt 1);matches=@($matches)}
}

function Get-KnowledgeClaimAuthorityEvaluation {
  param([object]$ProvenanceRegistry,[string]$ProfileId,[string]$ClaimKey)
  $assertions=@($ProvenanceRegistry.assertions|Where-Object {$_.claim_key -eq $ClaimKey});if($assertions.Count -eq 0){throw "Unknown claim key '$ClaimKey'."};$namespace=[string]$assertions[0].claim_namespace;$decisions=@()
  foreach($assertion in $assertions){foreach($link in @($assertion.evidence_links)){if($link.evidence_role -ne "supports"){continue};foreach($locator in @($link.locators)){$decision=Get-KnowledgeSourceAuthorityDecision $ProvenanceRegistry.sources $ProfileId $namespace ([string]$link.source_id) ([string]$locator.evidence_mode);$decisions+=,[pscustomobject]@{candidate_id="$($assertion.id):$($link.source_id):$($locator.id)";assertion_id=[string]$assertion.id;decision=$decision}}}}
  if($decisions.Count -eq 0){throw "Claim key '$ClaimKey' has no supporting evidence locators."};$groups=@($decisions|ForEach-Object {$ProvenanceRegistry.sources.sources[$_.decision.source_id].comparison_group}|Sort-Object -Unique);if($groups.Count -ne 1){return [pscustomobject]@{outcome="incomparable";profile_id=$ProfileId;claim_key=$ClaimKey;best_rank=$null;winning_assertion_ids=@();decisions=@($decisions)}}
  $profile=$ProvenanceRegistry.sources.authority_profiles[$ProfileId];$best=[ordered]@{};foreach($item in $decisions){$id=[string]$item.assertion_id;$rank=[int]$item.decision.rank;if(-not $best.Contains($id) -or ($profile.source_priority_order -eq "ascending" -and $rank -lt $best[$id]) -or ($profile.source_priority_order -eq "descending" -and $rank -gt $best[$id])){$best[$id]=$rank}};$bestRank=if($profile.source_priority_order -eq "ascending"){[int](($best.Values|Measure-Object -Minimum).Minimum)}else{[int](($best.Values|Measure-Object -Maximum).Maximum)};$winners=@($assertions|Where-Object {$best.Contains($_.id) -and $best[$_.id] -eq $bestRank}|ForEach-Object {$_.id});$values=@($assertions|Where-Object {$winners -ccontains $_.id}|ForEach-Object {ConvertTo-SourceCanonicalJson $_.asserted_value});$outcome=if($winners.Count -eq 1){"winner"}elseif(@($values|Sort-Object -Unique).Count -eq 1){"tie"}else{"conflict"}
  return [pscustomobject]@{outcome=$outcome;profile_id=$ProfileId;claim_key=$ClaimKey;best_rank=$bestRank;winning_assertion_ids=@($winners);decisions=@($decisions)}
}
