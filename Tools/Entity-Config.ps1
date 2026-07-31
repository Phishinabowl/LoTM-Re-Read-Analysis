$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) {
  . $projectConfigHelper
}
$schemaPackConfigHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-KnowledgeSchemaPackRegistry -ErrorAction SilentlyContinue)) {
  . $schemaPackConfigHelper
}

$script:SupportedEntitySchemaVersion = 3
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
      $owners = if ($aliases.Contains($normalized)) { @($aliases[$normalized]) } else { @() }
      if ($owners -notcontains $record.id) { $aliases[$normalized] = @(@($owners) + @($record.id)) }
    }
  }
  return $aliases
}

function Assert-EntityRelationshipTypeInverses {
  param([object]$RelationshipTypes, [string]$Label)

  foreach ($type in $RelationshipTypes.Values) {
    if (-not $RelationshipTypes.Contains($type.inverse_type)) {
      throw "Entity registry $Label relationship type '$($type.id)' references unknown inverse '$($type.inverse_type)'."
    }
    $inverse = $RelationshipTypes[$type.inverse_type]
    if ($inverse.inverse_type -ne $type.id) {
      throw "Entity registry $Label relationship types '$($type.id)' and '$($inverse.id)' are not reciprocal inverses."
    }
    if ($type.symmetric -ne ($type.id -eq $type.inverse_type)) {
      throw "Entity registry $Label relationship type '$($type.id)' has inconsistent symmetric and inverse settings."
    }
    if ($type.symmetric) {
      if (-not $type.canonical_direction) {
        throw "Entity registry $Label symmetric relationship type '$($type.id)' must be its canonical direction."
      }
      if ($null -ne $type.acyclic_group) {
        throw "Entity registry $Label symmetric relationship type '$($type.id)' cannot declare an acyclic group."
      }
    } else {
      if ($type.canonical_direction -eq $inverse.canonical_direction) {
        throw "Entity registry $Label relationship types '$($type.id)' and '$($inverse.id)' must declare exactly one canonical direction."
      }
      if ($type.acyclic_group -ne $inverse.acyclic_group) {
        throw "Entity registry $Label relationship types '$($type.id)' and '$($inverse.id)' must use the same acyclic group."
      }
    }
  }
}

function Get-CanonicalEntityRelationshipParts {
  param(
    [string]$SourceId,
    [string]$TypeId,
    [string]$TargetId,
    [AllowNull()][object]$ScopeId,
    [object]$RelationshipTypes
  )

  $type = $RelationshipTypes[$TypeId]
  if ($type.symmetric) {
    $ends = @($SourceId, $TargetId) | Sort-Object
    return [pscustomobject]@{ source_id=$ends[0]; type_id=$TypeId; target_id=$ends[1]; scope_id=$ScopeId }
  }
  if ($type.canonical_direction) {
    return [pscustomobject]@{ source_id=$SourceId; type_id=$TypeId; target_id=$TargetId; scope_id=$ScopeId }
  }
  return [pscustomobject]@{ source_id=$TargetId; type_id=$type.inverse_type; target_id=$SourceId; scope_id=$ScopeId }
}

function Get-CanonicalEntityRelationshipShape {
  param(
    [string]$SourceId,
    [string]$TypeId,
    [string]$TargetId,
    [AllowNull()][object]$ScopeId,
    [object]$RelationshipTypes
  )

  $parts = Get-CanonicalEntityRelationshipParts $SourceId $TypeId $TargetId $ScopeId $RelationshipTypes
  return "$($parts.source_id)|$($parts.type_id)|$($parts.target_id)|$($parts.scope_id)"
}

function Assert-AcyclicEntityRelationships {
  param(
    [object[]]$Relationships,
    [object]$RelationshipTypes,
    [string]$Label,
    [string]$SourceProperty,
    [string]$TargetProperty
  )

  $normalized = @()
  foreach ($relationship in $Relationships) {
    $type = $RelationshipTypes[$relationship.relationship_type]
    if ($null -eq $type.acyclic_group) { continue }
    $parts = Get-CanonicalEntityRelationshipParts $relationship.$SourceProperty $relationship.relationship_type $relationship.$TargetProperty $relationship.applicability_scope_id $RelationshipTypes
    $normalized += [pscustomobject]@{ group=$type.acyclic_group; source_id=$parts.source_id; target_id=$parts.target_id; scope_id=$parts.scope_id }
  }

  foreach ($group in @($normalized.group | Sort-Object -Unique)) {
    $groupEdges = @($normalized | Where-Object group -eq $group)
    $scopeIds = @($groupEdges | Where-Object { $null -ne $_.scope_id } | ForEach-Object scope_id | Sort-Object -Unique)
    foreach ($scopeToken in (@("__unscoped__") + @($scopeIds))) {
      $isUnscoped = $scopeToken -eq "__unscoped__"
      $scopeId = if ($isUnscoped) { $null } else { $scopeToken }
      $edges = if ($isUnscoped) {
        @($groupEdges | Where-Object { $null -eq $_.scope_id })
      } else {
        @($groupEdges | Where-Object { $null -eq $_.scope_id -or $_.scope_id -eq $scopeId })
      }
      $nodes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
      $indegree = @{}
      $adjacency = @{}
      foreach ($edge in $edges) {
        [void]$nodes.Add($edge.source_id); [void]$nodes.Add($edge.target_id)
        if (-not $indegree.ContainsKey($edge.source_id)) { $indegree[$edge.source_id] = 0 }
        if (-not $indegree.ContainsKey($edge.target_id)) { $indegree[$edge.target_id] = 0 }
        if (-not $adjacency.ContainsKey($edge.source_id)) { $adjacency[$edge.source_id] = @() }
        if ($adjacency[$edge.source_id] -notcontains $edge.target_id) {
          $adjacency[$edge.source_id] = @($adjacency[$edge.source_id]) + $edge.target_id
          $indegree[$edge.target_id] += 1
        }
      }
      $queue = New-Object 'System.Collections.Generic.Queue[string]'
      foreach ($nodeId in $nodes) { if ($indegree[$nodeId] -eq 0) { $queue.Enqueue($nodeId) } }
      $processed = 0
      while ($queue.Count -gt 0) {
        $nodeId = $queue.Dequeue(); $processed += 1
        if ($adjacency.ContainsKey($nodeId)) {
          foreach ($targetId in @($adjacency[$nodeId])) {
            $indegree[$targetId] -= 1
            if ($indegree[$targetId] -eq 0) { $queue.Enqueue($targetId) }
          }
        }
      }
      if ($processed -ne $nodes.Count) {
        $scopeDescription = "unscoped relationships"
        if (-not $isUnscoped) { $scopeDescription = [string]$scopeId }
        throw "Entity registry contains a cycle among $Label relationships in acyclic group '$group' for '$scopeDescription'."
      }
    }
  }
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
    $primaryCategoryId = Get-RequiredEntityString $entity "primary_category_id" $context
    $categoryIds = @(Get-EntityStringList $entity "category_ids" $context)
    if ($categoryIds.Count -eq 0) { throw "Entity registry '$context.category_ids' cannot be empty." }
    foreach ($categoryId in $categoryIds) {
      if (-not $TaxonomyConfig.categories.Contains($categoryId)) { throw "Entity registry '$context.category_ids' references unknown category '$categoryId'." }
    }
    if ($categoryIds -notcontains $primaryCategoryId) { throw "Entity registry '$context.primary_category_id' must appear in category_ids." }
    $entities[$entityId] = [pscustomobject]@{
      id = $entityId
      lifecycle = $lifecycle
      primary_category_id = $primaryCategoryId
      category_ids = @($categoryIds)
      label = Get-RequiredEntityString $entity "label" $context
      aliases = @(Get-EntityStringList $entity "aliases" $context)
    }
  }

  $allowedMembershipStatuses = @(Get-SchemaPackAllowedValues $SchemaPackRegistry "source.membership-status")
  if ($allowedMembershipStatuses.Count -eq 0) { throw "Selected schema packs do not provide controlled namespace 'source.membership-status'." }

  $rawEntityTypes = Get-ProjectMapValue $registry "entity_relationship_types"
  if ($null -eq $rawEntityTypes -or $rawEntityTypes -isnot [System.Collections.IDictionary]) { throw "Entity registry 'entity_relationship_types' must be a mapping." }
  $entityRelationshipTypes = [ordered]@{}
  foreach ($typeId in $rawEntityTypes.Keys) {
    $context = "entity_relationship_types.$typeId"; Assert-EntityStableId $typeId $context
    Assert-EntityPackValue $SchemaPackRegistry "narrative.entity-relationship-type" $typeId $context
    $type = $rawEntityTypes[$typeId]
    if ($type -isnot [System.Collections.IDictionary]) { throw "Entity registry '$context' must be a mapping." }
    $entityRelationshipTypes[$typeId] = [pscustomobject]@{
      id=$typeId
      label=Get-RequiredEntityString $type "label" $context
      inverse_type=Get-RequiredEntityString $type "inverse_type" $context
      symmetric=Get-RequiredEntityBoolean $type "symmetric" $context
      canonical_direction=Get-RequiredEntityBoolean $type "canonical_direction" $context
      acyclic_group=Get-OptionalEntityString $type "acyclic_group" $context
    }
    if ($null -ne $entityRelationshipTypes[$typeId].acyclic_group) { Assert-EntityStableId $entityRelationshipTypes[$typeId].acyclic_group "$context.acyclic_group" }
  }
  Assert-EntityRelationshipTypeInverses $entityRelationshipTypes "entity"

  $rawEntityRelationships = Get-ProjectMapValue $registry "entity_relationships"
  if ($null -eq $rawEntityRelationships) { $rawEntityRelationships = @() }
  if ($rawEntityRelationships -is [string]) { throw "Entity registry 'entity_relationships' must be a list." }
  $rawEntityRelationships = @($rawEntityRelationships)
  $entityRelationships = @()
  $entityRelationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $entityRelationshipShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $lineageRoleTypes = @("derived-from", "composite-of", "inspired-by")
  for ($index = 0; $index -lt $rawEntityRelationships.Count; $index += 1) {
    $context = "entity_relationships[$index]"; $relationship = $rawEntityRelationships[$index]
    if ($relationship -isnot [System.Collections.IDictionary]) { throw "Entity registry '$context' must be a mapping." }
    $id = Get-RequiredEntityString $relationship "id" $context; Assert-EntityStableId $id "$context.id"
    if (-not $entityRelationshipIds.Add($id)) { throw "Entity registry repeats entity relationship ID '$id'." }
    $sourceId = Get-RequiredEntityString $relationship "source_entity_id" $context
    $targetId = Get-RequiredEntityString $relationship "target_entity_id" $context
    if (-not $entities.Contains($sourceId) -or -not $entities.Contains($targetId)) { throw "Entity registry '$context' references an unknown entity endpoint." }
    if ($sourceId -eq $targetId) { throw "Entity registry '$context' cannot relate an entity to itself." }
    $typeId = Get-RequiredEntityString $relationship "relationship_type" $context
    if (-not $entityRelationshipTypes.Contains($typeId)) { throw "Entity registry '$context.relationship_type' references unknown type '$typeId'." }
    $status = Get-RequiredEntityString $relationship "status" $context
    if ($allowedMembershipStatuses -notcontains $status) { throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs." }
    $scopeId = Get-OptionalEntityString $relationship "applicability_scope_id" $context
    if ($null -ne $scopeId -and -not $SourceRegistry.applicability_scopes.Contains($scopeId)) { throw "Entity registry '$context.applicability_scope_id' references unknown scope '$scopeId'." }
    $basisRoles = if ($relationship.Contains("basis_roles")) { @(Get-EntityStringList $relationship "basis_roles" $context) } else { @() }
    foreach ($basisRole in $basisRoles) { Assert-EntityPackValue $SchemaPackRegistry "narrative.entity-relationship-basis-role" $basisRole "$context.basis_roles" }
    if ($basisRoles.Count -gt 0 -and $lineageRoleTypes -notcontains $typeId) { throw "Entity registry '$context.basis_roles' is only valid for derived-from, composite-of, or inspired-by relationships." }
    $shape = Get-CanonicalEntityRelationshipShape $sourceId $typeId $targetId $scopeId $entityRelationshipTypes
    if (-not $entityRelationshipShapes.Add($shape)) { throw "Entity registry '$context' duplicates an entity relationship or its inverse." }
    $entityRelationships += [pscustomobject]@{ id=$id; source_entity_id=$sourceId; relationship_type=$typeId; target_entity_id=$targetId; status=$status; applicability_scope_id=$scopeId; basis_roles=@($basisRoles) }
  }
  Assert-AcyclicEntityRelationships $entityRelationships $entityRelationshipTypes "entity" "source_entity_id" "target_entity_id"

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
      canonical_direction=Get-RequiredEntityBoolean $type "canonical_direction" $context
      acyclic_group=Get-OptionalEntityString $type "acyclic_group" $context
    }
    if ($null -ne $relationshipTypes[$typeId].acyclic_group) { Assert-EntityStableId $relationshipTypes[$typeId].acyclic_group "$context.acyclic_group" }
  }
  Assert-EntityRelationshipTypeInverses $relationshipTypes "incarnation"

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
    $shape = Get-CanonicalEntityRelationshipShape $sourceId $typeId $targetId $scopeId $relationshipTypes
    if (-not $relationshipShapes.Add($shape)) { throw "Entity registry '$context' duplicates an incarnation relationship or its inverse." }
    $relationships += [pscustomobject]@{ id=$id; source_incarnation_id=$sourceId; relationship_type=$typeId; target_incarnation_id=$targetId; status=$status; applicability_scope_id=$scopeId }
  }
  Assert-AcyclicEntityRelationships $relationships $relationshipTypes "incarnation" "source_incarnation_id" "target_incarnation_id"

  return [pscustomobject]@{
    path=$registryPath
    schema_version=[int]$schemaVersion
    entities=$entities
    entity_relationship_types=$entityRelationshipTypes
    entity_relationships=@($entityRelationships)
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
  $matches = @(Resolve-KnowledgeEntityIds $EntityRegistry $Value)
  if ($matches.Count -gt 1) { throw "Ambiguous entity name '$Value' matches: $($matches -join ', ')." }
  return $(if ($matches.Count -eq 1) { $matches[0] } else { $null })
}

function Resolve-KnowledgeEntityIds {
  param([object]$EntityRegistry, [string]$Value)
  $normalized = $Value.Trim().ToLowerInvariant()
  foreach ($entityId in $EntityRegistry.entities.Keys) { if ($entityId.ToLowerInvariant() -eq $normalized) { return @($entityId) } }
  if ($EntityRegistry.entity_aliases.Contains($normalized)) { return @($EntityRegistry.entity_aliases[$normalized]) }
  return @()
}

function Resolve-KnowledgeIncarnationId {
  param([object]$EntityRegistry, [string]$Value)
  $matches = @(Resolve-KnowledgeIncarnationIds $EntityRegistry $Value)
  if ($matches.Count -gt 1) { throw "Ambiguous incarnation name '$Value' matches: $($matches -join ', ')." }
  return $(if ($matches.Count -eq 1) { $matches[0] } else { $null })
}

function Resolve-KnowledgeIncarnationIds {
  param([object]$EntityRegistry, [string]$Value)
  $normalized = $Value.Trim().ToLowerInvariant()
  foreach ($incarnationId in $EntityRegistry.incarnations.Keys) { if ($incarnationId.ToLowerInvariant() -eq $normalized) { return @($incarnationId) } }
  if ($EntityRegistry.incarnation_aliases.Contains($normalized)) { return @($EntityRegistry.incarnation_aliases[$normalized]) }
  return @()
}

function Get-KnowledgeEntityIncarnations {
  param([object]$EntityRegistry, [string]$EntityId)
  if (-not $EntityRegistry.entities.Contains($EntityId)) { throw "Unknown entity '$EntityId'." }
  return @($EntityRegistry.incarnations.Values | Where-Object entity_id -eq $EntityId)
}

function Get-KnowledgeEntityRelationships {
  param([object]$EntityRegistry, [string]$EntityId)
  if (-not $EntityRegistry.entities.Contains($EntityId)) { throw "Unknown entity '$EntityId'." }
  return @($EntityRegistry.entity_relationships | Where-Object {
    $_.source_entity_id -eq $EntityId -or $_.target_entity_id -eq $EntityId
  })
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
    "entity-relationship" {
      $target = @($EntityRegistry.entity_relationships | Where-Object id -eq $SubjectId)
      if ($target.Count -eq 1) { return $target[0] }
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
