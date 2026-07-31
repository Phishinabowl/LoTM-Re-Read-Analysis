$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) {
  . $projectConfigHelper
}
$schemaPackConfigHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-KnowledgeSchemaPackRegistry -ErrorAction SilentlyContinue)) {
  . $schemaPackConfigHelper
}

$script:SupportedEntitySchemaVersion = 1
$script:EntityStableIdPattern = "^[a-z0-9]+(?:-[a-z0-9]+)*$"
$script:EntityLifecycles = @("active", "deferred")

function Get-RequiredEntityString {
  param([object]$Map, [string]$Key, [string]$Context)

  $value = Get-ProjectMapValue $Map $Key
  if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
    throw "Entity registry '$Context.$Key' must be a non-empty string."
  }
  return ([string]$value).Trim()
}

function Get-OptionalEntityString {
  param([object]$Map, [string]$Key, [string]$Context)

  $value = Get-ProjectMapValue $Map $Key
  if ($null -eq $value) { return $null }
  if ([string]::IsNullOrWhiteSpace([string]$value)) {
    throw "Entity registry '$Context.$Key' must be a non-empty string or null."
  }
  return ([string]$value).Trim()
}

function Get-RequiredEntityBoolean {
  param([object]$Map, [string]$Key, [string]$Context)

  $value = Get-ProjectMapValue $Map $Key
  if ($value -isnot [bool]) {
    throw "Entity registry '$Context.$Key' must be true or false."
  }
  return [bool]$value
}

function Get-EntityStringList {
  param([object]$Map, [string]$Key, [string]$Context)

  if (-not $Map.Contains($Key)) { throw "Entity registry '$Context.$Key' must be a list." }
  $raw = Get-ProjectMapValue $Map $Key
  if ($null -eq $raw) { return @() }
  if ($raw -is [System.Collections.IDictionary]) { throw "Entity registry '$Context.$Key' must be a list." }
  $raw = @($raw)
  $values = @()
  $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  for ($index = 0; $index -lt $raw.Count; $index += 1) {
    $value = [string]$raw[$index]
    if ([string]::IsNullOrWhiteSpace($value)) {
      throw "Entity registry '$Context.$Key[$index]' must be a non-empty string."
    }
    $value = $value.Trim()
    if (-not $seen.Add($value)) {
      throw "Entity registry '$Context.$Key' contains duplicate values."
    }
    $values += $value
  }
  return @($values)
}

function Assert-EntityStableId {
  param([string]$Value, [string]$Context)

  if ($Value -notmatch $script:EntityStableIdPattern) {
    throw "Entity registry '$Context' must be a lowercase kebab-case stable ID: $Value"
  }
}

function Assert-EntityPackValue {
  param([object]$SchemaPackRegistry, [string]$Namespace, [string]$Value, [string]$Context)

  $allowed = @(Get-SchemaPackAllowedValues $SchemaPackRegistry $Namespace)
  if ($allowed.Count -eq 0) {
    throw "Selected schema packs do not provide controlled namespace '$Namespace'."
  }
  if ($allowed -notcontains $Value) {
    throw "Entity registry '$Context' value '$Value' is not supplied by selected schema packs."
  }
}

function New-EntityAliasMap {
  param([object]$Records, [string]$Label)

  $aliases = [ordered]@{}
  $ids = @{}
  foreach ($recordId in $Records.Keys) { $ids[$recordId.ToLowerInvariant()] = $recordId }
  foreach ($record in $Records.Values) {
    foreach ($alias in @($record.label) + @($record.aliases)) {
      $normalized = ([string]$alias).ToLowerInvariant()
      if ($ids.ContainsKey($normalized) -and $ids[$normalized] -ne $record.id) {
        throw "Entity registry $Label alias '$alias' conflicts with ID '$($ids[$normalized])'."
      }
      if ($aliases.Contains($normalized) -and $aliases[$normalized] -ne $record.id) {
        throw "Entity registry $Label alias '$alias' is shared by '$($aliases[$normalized])' and '$($record.id)'."
      }
      $aliases[$normalized] = $record.id
    }
  }
  return $aliases
}

function Get-KnowledgeEntityRegistry {
  param(
    [object]$ProjectConfig,
    [object]$TaxonomyConfig,
    [object]$SourceRegistry,
    [object]$SchemaPackRegistry = $null
  )

  Import-ProjectYamlModule
  if ($null -eq $SchemaPackRegistry) {
    $SchemaPackRegistry = Get-KnowledgeSchemaPackRegistry $ProjectConfig
  }
  if (-not (Test-SchemaPackCapabilityEnabled $SchemaPackRegistry "entity-incarnations")) {
    throw "Entity registry requires enabled schema capability 'entity-incarnations'."
  }

  $registryPath = $ProjectConfig.entities_registry
  $registry = ConvertFrom-Yaml -Yaml ([System.IO.File]::ReadAllText($registryPath, [System.Text.UTF8Encoding]::new($true))) -Ordered
  if ($null -eq $registry -or $registry -isnot [System.Collections.IDictionary]) {
    throw "Entity registry root must be a mapping: $registryPath"
  }
  $schemaVersion = Get-ProjectMapValue $registry "schema_version"
  if ([int]$schemaVersion -ne $script:SupportedEntitySchemaVersion) {
    throw "Unsupported entity schema_version '$schemaVersion'; expected $($script:SupportedEntitySchemaVersion)."
  }

  $rawEntities = Get-ProjectMapValue $registry "entities"
  if ($null -eq $rawEntities -or $rawEntities -isnot [System.Collections.IDictionary]) {
    throw "Entity registry 'entities' must be a mapping."
  }
  $entities = [ordered]@{}
  foreach ($entityId in $rawEntities.Keys) {
    Assert-EntityStableId $entityId "entities.$entityId"
    $context = "entities.$entityId"
    $entity = $rawEntities[$entityId]
    if ($entity -isnot [System.Collections.IDictionary]) { throw "Entity registry '$context' must be a mapping." }
    $lifecycle = Get-RequiredEntityString $entity "lifecycle" $context
    if ($script:EntityLifecycles -notcontains $lifecycle) { throw "Entity registry '$context.lifecycle' must be one of: $($script:EntityLifecycles -join ', ')." }
    $categoryId = Get-RequiredEntityString $entity "category_id" $context
    if (-not $TaxonomyConfig.categories.Contains($categoryId)) { throw "Entity registry '$context.category_id' references unknown category '$categoryId'." }
    $entities[$entityId] = [pscustomobject]@{
      id = $entityId
      lifecycle = $lifecycle
      category_id = $categoryId
      label = Get-RequiredEntityString $entity "label" $context
      aliases = @(Get-EntityStringList $entity "aliases" $context)
    }
  }

  $allowedMembershipStatuses = @(Get-SchemaPackAllowedValues $SchemaPackRegistry "source.membership-status")
  if ($allowedMembershipStatuses.Count -eq 0) { throw "Selected schema packs do not provide controlled namespace 'source.membership-status'." }
  $rawIncarnations = Get-ProjectMapValue $registry "incarnations"
  if ($null -eq $rawIncarnations -or $rawIncarnations -isnot [System.Collections.IDictionary]) { throw "Entity registry 'incarnations' must be a mapping." }
  $incarnations = [ordered]@{}
  foreach ($incarnationId in $rawIncarnations.Keys) {
    Assert-EntityStableId $incarnationId "incarnations.$incarnationId"
    $context = "incarnations.$incarnationId"
    $incarnation = $rawIncarnations[$incarnationId]
    if ($incarnation -isnot [System.Collections.IDictionary]) { throw "Entity registry '$context' must be a mapping." }
    $lifecycle = Get-RequiredEntityString $incarnation "lifecycle" $context
    if ($script:EntityLifecycles -notcontains $lifecycle) { throw "Entity registry '$context.lifecycle' must be one of: $($script:EntityLifecycles -join ', ')." }
    $entityId = Get-RequiredEntityString $incarnation "entity_id" $context
    if (-not $entities.Contains($entityId)) { throw "Entity registry '$context.entity_id' references unknown entity '$entityId'." }
    $primaryContinuityId = Get-RequiredEntityString $incarnation "primary_continuity_id" $context
    if (-not $SourceRegistry.continuities.Contains($primaryContinuityId)) { throw "Entity registry '$context.primary_continuity_id' references unknown continuity '$primaryContinuityId'." }
    $rawMemberships = Get-ProjectMapValue $incarnation "continuity_memberships"
    if ($null -eq $rawMemberships -or $rawMemberships -is [string]) { throw "Entity registry '$context.continuity_memberships' must be a non-empty list." }
    $rawMemberships = @($rawMemberships)
    if ($rawMemberships.Count -eq 0) { throw "Entity registry '$context.continuity_memberships' must be a non-empty list." }
    $memberships = @()
    $seenContinuities = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawMemberships.Count; $index += 1) {
      $membershipContext = "$context.continuity_memberships[$index]"
      $membership = $rawMemberships[$index]
      if ($membership -isnot [System.Collections.IDictionary]) { throw "Entity registry '$membershipContext' must be a mapping." }
      $continuityId = Get-RequiredEntityString $membership "continuity_id" $membershipContext
      if (-not $SourceRegistry.continuities.Contains($continuityId)) { throw "Entity registry '$membershipContext.continuity_id' references unknown continuity '$continuityId'." }
      if (-not $seenContinuities.Add($continuityId)) { throw "Entity registry '$context.continuity_memberships' repeats '$continuityId'." }
      $status = Get-RequiredEntityString $membership "status" $membershipContext
      if ($allowedMembershipStatuses -notcontains $status) { throw "Entity registry '$membershipContext.status' value '$status' is not supplied by selected schema packs." }
      $memberships += [pscustomobject]@{ continuity_id = $continuityId; status = $status }
    }
    if (-not $seenContinuities.Contains($primaryContinuityId)) { throw "Entity registry '$context.primary_continuity_id' must appear in continuity_memberships." }
    $incarnations[$incarnationId] = [pscustomobject]@{
      id = $incarnationId
      lifecycle = $lifecycle
      entity_id = $entityId
      label = Get-RequiredEntityString $incarnation "label" $context
      aliases = @(Get-EntityStringList $incarnation "aliases" $context)
      primary_continuity_id = $primaryContinuityId
      continuity_memberships = @($memberships)
    }
  }

  $rawBindings = Get-ProjectMapValue $registry "incarnation_bindings"
  if ($null -eq $rawBindings) { $rawBindings = @() }
  if ($rawBindings -is [string]) { throw "Entity registry 'incarnation_bindings' must be a list." }
  $rawBindings = @($rawBindings)
  $bindings = @()
  $bindingIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $bindingShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for ($index = 0; $index -lt $rawBindings.Count; $index += 1) {
    $context = "incarnation_bindings[$index]"; $binding = $rawBindings[$index]
    if ($binding -isnot [System.Collections.IDictionary]) { throw "Entity registry '$context' must be a mapping." }
    $id = Get-RequiredEntityString $binding "id" $context; Assert-EntityStableId $id "$context.id"
    if (-not $bindingIds.Add($id)) { throw "Entity registry repeats binding ID '$id'." }
    $incarnationId = Get-RequiredEntityString $binding "incarnation_id" $context
    if (-not $incarnations.Contains($incarnationId)) { throw "Entity registry '$context.incarnation_id' references unknown incarnation '$incarnationId'." }
    $scopeId = Get-RequiredEntityString $binding "applicability_scope_id" $context
    if (-not $SourceRegistry.applicability_scopes.Contains($scopeId)) { throw "Entity registry '$context.applicability_scope_id' references unknown scope '$scopeId'." }
    $bindingType = Get-RequiredEntityString $binding "binding_type" $context
    Assert-EntityPackValue $SchemaPackRegistry "narrative.incarnation-binding-type" $bindingType "$context.binding_type"
    $status = Get-RequiredEntityString $binding "status" $context
    if ($allowedMembershipStatuses -notcontains $status) { throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs." }
    if (-not $bindingShapes.Add("$incarnationId|$scopeId|$bindingType")) { throw "Entity registry '$context' duplicates an incarnation binding." }
    $bindings += [pscustomobject]@{ id=$id; incarnation_id=$incarnationId; applicability_scope_id=$scopeId; binding_type=$bindingType; status=$status }
  }

  $rawTypes = Get-ProjectMapValue $registry "incarnation_relationship_types"
  if ($null -eq $rawTypes -or $rawTypes -isnot [System.Collections.IDictionary]) { throw "Entity registry 'incarnation_relationship_types' must be a mapping." }
  $relationshipTypes = [ordered]@{}
  foreach ($typeId in $rawTypes.Keys) {
    $context = "incarnation_relationship_types.$typeId"; Assert-EntityStableId $typeId $context
    Assert-EntityPackValue $SchemaPackRegistry "narrative.incarnation-relationship-type" $typeId $context
    $type = $rawTypes[$typeId]
    if ($type -isnot [System.Collections.IDictionary]) { throw "Entity registry '$context' must be a mapping." }
    $relationshipTypes[$typeId] = [pscustomobject]@{
      id=$typeId
      label=Get-RequiredEntityString $type "label" $context
      inverse_type=Get-RequiredEntityString $type "inverse_type" $context
      symmetric=Get-RequiredEntityBoolean $type "symmetric" $context
    }
  }
  foreach ($type in $relationshipTypes.Values) {
    if (-not $relationshipTypes.Contains($type.inverse_type)) { throw "Entity registry relationship type '$($type.id)' references unknown inverse '$($type.inverse_type)'." }
    $inverse = $relationshipTypes[$type.inverse_type]
    if ($inverse.inverse_type -ne $type.id) { throw "Entity registry relationship types '$($type.id)' and '$($inverse.id)' are not reciprocal inverses." }
    if ($type.symmetric -ne ($type.id -eq $type.inverse_type)) { throw "Entity registry relationship type '$($type.id)' has inconsistent symmetric and inverse settings." }
  }

  $rawRelationships = Get-ProjectMapValue $registry "incarnation_relationships"
  if ($null -eq $rawRelationships) { $rawRelationships = @() }
  if ($rawRelationships -is [string]) { throw "Entity registry 'incarnation_relationships' must be a list." }
  $rawRelationships = @($rawRelationships)
  $relationships = @()
  $relationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $relationshipShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for ($index = 0; $index -lt $rawRelationships.Count; $index += 1) {
    $context = "incarnation_relationships[$index]"; $relationship = $rawRelationships[$index]
    if ($relationship -isnot [System.Collections.IDictionary]) { throw "Entity registry '$context' must be a mapping." }
    $id = Get-RequiredEntityString $relationship "id" $context; Assert-EntityStableId $id "$context.id"
    if (-not $relationshipIds.Add($id)) { throw "Entity registry repeats relationship ID '$id'." }
    $sourceId = Get-RequiredEntityString $relationship "source_incarnation_id" $context
    $targetId = Get-RequiredEntityString $relationship "target_incarnation_id" $context
    if (-not $incarnations.Contains($sourceId) -or -not $incarnations.Contains($targetId)) { throw "Entity registry '$context' references an unknown incarnation endpoint." }
    if ($sourceId -eq $targetId) { throw "Entity registry '$context' cannot relate an incarnation to itself." }
    $typeId = Get-RequiredEntityString $relationship "relationship_type" $context
    if (-not $relationshipTypes.Contains($typeId)) { throw "Entity registry '$context.relationship_type' references unknown type '$typeId'." }
    $status = Get-RequiredEntityString $relationship "status" $context
    if ($allowedMembershipStatuses -notcontains $status) { throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs." }
    $scopeId = Get-OptionalEntityString $relationship "applicability_scope_id" $context
    if ($null -ne $scopeId -and -not $SourceRegistry.applicability_scopes.Contains($scopeId)) { throw "Entity registry '$context.applicability_scope_id' references unknown scope '$scopeId'." }
    $type = $relationshipTypes[$typeId]
    if ($type.symmetric) { $ends = @($sourceId, $targetId) | Sort-Object; $shape = "$($ends[0])|$typeId|$($ends[1])|$scopeId" } else { $shape = "$sourceId|$typeId|$targetId|$scopeId" }
    if (-not $relationshipShapes.Add($shape)) { throw "Entity registry '$context' duplicates an incarnation relationship." }
    $relationships += [pscustomobject]@{ id=$id; source_incarnation_id=$sourceId; relationship_type=$typeId; target_incarnation_id=$targetId; status=$status; applicability_scope_id=$scopeId }
  }

  return [pscustomobject]@{
    path=$registryPath
    schema_version=[int]$schemaVersion
    entities=$entities
    incarnations=$incarnations
    incarnation_bindings=@($bindings)
    incarnation_relationship_types=$relationshipTypes
    incarnation_relationships=@($relationships)
    entity_aliases=New-EntityAliasMap $entities "entity"
    incarnation_aliases=New-EntityAliasMap $incarnations "incarnation"
  }
}

function Resolve-KnowledgeEntityId {
  param([object]$EntityRegistry, [string]$Value)
  $normalized = $Value.Trim().ToLowerInvariant()
  foreach ($entityId in $EntityRegistry.entities.Keys) { if ($entityId.ToLowerInvariant() -eq $normalized) { return $entityId } }
  if ($EntityRegistry.entity_aliases.Contains($normalized)) { return $EntityRegistry.entity_aliases[$normalized] }
  return $null
}

function Resolve-KnowledgeIncarnationId {
  param([object]$EntityRegistry, [string]$Value)
  $normalized = $Value.Trim().ToLowerInvariant()
  foreach ($incarnationId in $EntityRegistry.incarnations.Keys) { if ($incarnationId.ToLowerInvariant() -eq $normalized) { return $incarnationId } }
  if ($EntityRegistry.incarnation_aliases.Contains($normalized)) { return $EntityRegistry.incarnation_aliases[$normalized] }
  return $null
}

function Get-KnowledgeEntityIncarnations {
  param([object]$EntityRegistry, [string]$EntityId)
  if (-not $EntityRegistry.entities.Contains($EntityId)) { throw "Unknown entity '$EntityId'." }
  return @($EntityRegistry.incarnations.Values | Where-Object entity_id -eq $EntityId)
}

function Get-KnowledgeIncarnationBindings {
  param([object]$EntityRegistry, [string]$IncarnationId)
  if (-not $EntityRegistry.incarnations.Contains($IncarnationId)) { throw "Unknown incarnation '$IncarnationId'." }
  return @($EntityRegistry.incarnation_bindings | Where-Object incarnation_id -eq $IncarnationId)
}

function Get-KnowledgeIncarnationRelationships {
  param([object]$EntityRegistry, [string]$IncarnationId)
  if (-not $EntityRegistry.incarnations.Contains($IncarnationId)) { throw "Unknown incarnation '$IncarnationId'." }
  return @($EntityRegistry.incarnation_relationships | Where-Object {
    $_.source_incarnation_id -eq $IncarnationId -or $_.target_incarnation_id -eq $IncarnationId
  })
}

function Get-KnowledgeEntityProvenanceTarget {
  param([object]$EntityRegistry, [string]$SubjectType, [string]$SubjectId)

  switch ($SubjectType) {
    "entity" {
      if ($EntityRegistry.entities.Contains($SubjectId)) { return $EntityRegistry.entities[$SubjectId] }
    }
    "entity-incarnation" {
      if ($EntityRegistry.incarnations.Contains($SubjectId)) { return $EntityRegistry.incarnations[$SubjectId] }
    }
    "incarnation-binding" {
      $target = @($EntityRegistry.incarnation_bindings | Where-Object id -eq $SubjectId)
      if ($target.Count -eq 1) { return $target[0] }
    }
    "incarnation-relationship" {
      $target = @($EntityRegistry.incarnation_relationships | Where-Object id -eq $SubjectId)
      if ($target.Count -eq 1) { return $target[0] }
    }
    default { throw "Unsupported entity-registry subject type '$SubjectType'." }
  }
  throw "Unknown $SubjectType '$SubjectId'."
}
