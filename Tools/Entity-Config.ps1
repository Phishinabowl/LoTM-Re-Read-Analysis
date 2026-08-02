$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) {
    . $projectConfigHelper
}
$schemaPackConfigHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-KnowledgeSchemaPackRegistry -ErrorAction SilentlyContinue)) {
    . $schemaPackConfigHelper
}
$lookupKeyConfigHelper = Join-Path $PSScriptRoot "Lookup-Key-Config.ps1"
if (-not (Get-Command Get-KnowledgeLookupKeyConfig -ErrorAction SilentlyContinue)) {
    . $lookupKeyConfigHelper
}

$script:SupportedEntitySchemaVersion = 4
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
    if ($null -eq $value) {
        return $null
    }
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

    if (-not $Map.Contains($Key)) {
        throw "Entity registry '$Context.$Key' must be a list."
    }
    $raw = Get-ProjectMapValue $Map $Key
    if ($null -eq $raw) {
        return @()
    }
    if ($raw -is [System.Collections.IDictionary]) {
        throw "Entity registry '$Context.$Key' must be a list."
    }
    $raw = @($raw)
    $values = @()
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
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

    if ($Value -cnotmatch $script:EntityStableIdPattern) {
        throw "Entity registry '$Context' must be a lowercase kebab-case stable ID: $Value"
    }
}

function Assert-EntityPackValue {
    param([object]$SchemaPackRegistry, [string]$Namespace, [string]$Value, [string]$Context)

    $allowed = @(Get-SchemaPackAllowedValues $SchemaPackRegistry $Namespace)
    if ($allowed.Count -eq 0) {
        throw "Selected schema packs do not provide controlled namespace '$Namespace'."
    }
    if ($allowed -cnotcontains $Value) {
        throw "Entity registry '$Context' value '$Value' is not supplied by selected schema packs."
    }
}

function New-EntityAliasMap {
    param([object]$Records, [string]$Label, [object]$LookupKeyConfig)

    $aliases = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
    $ids = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    foreach ($recordId in $Records.Keys) {
        $ids[$(ConvertTo-KnowledgeLookupKey $recordId $LookupKeyConfig)] = $recordId
    }
    foreach ($record in $Records.Values) {
        $recordAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        foreach ($alias in @($record.aliases)) {
            $aliasKey = ConvertTo-KnowledgeLookupKey ([string]$alias) $LookupKeyConfig
            if (-not $recordAliasKeys.Add($aliasKey)) {
                throw "Entity registry $Label '$($record.id)' contains duplicate aliases."
            }
        }
        foreach ($alias in @($record.label) + @($record.aliases)) {
            $normalized = ConvertTo-KnowledgeLookupKey ([string]$alias) $LookupKeyConfig
            if ($ids.ContainsKey($normalized) -and $ids[$normalized] -ne $record.id) {
                throw "Entity registry $Label alias '$alias' conflicts with ID '$($ids[$normalized])'."
            }
            $owners = if ($aliases.ContainsKey($normalized)) {
                @($aliases[$normalized])
            }
            else {
                @()
            }
            if ($owners -cnotcontains $record.id) {
                $aliases[$normalized] = @(@($owners) + @($record.id))
            }
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
        }
        else {
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
        return [pscustomobject]@{ source_id=$ends[0]
            type_id=$TypeId
            target_id=$ends[1]
            scope_id=$ScopeId
        }
    }
    if ($type.canonical_direction) {
        return [pscustomobject]@{ source_id=$SourceId
            type_id=$TypeId
            target_id=$TargetId
            scope_id=$ScopeId
        }
    }
    return [pscustomobject]@{ source_id=$TargetId
        type_id=$type.inverse_type
        target_id=$SourceId
        scope_id=$ScopeId
    }
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
        if ($null -eq $type.acyclic_group) {
            continue
        }
        $relationshipArguments = @(
            $relationship.$SourceProperty
            $relationship.relationship_type
            $relationship.$TargetProperty
            $relationship.applicability_scope_id
            $RelationshipTypes
        )
        $parts = Get-CanonicalEntityRelationshipParts @relationshipArguments
        $normalized += [pscustomobject]@{ group=$type.acyclic_group
            source_id=$parts.source_id
            target_id=$parts.target_id
            scope_id=$parts.scope_id
        }
    }

    foreach ($group in @($normalized.group | Sort-Object -Unique)) {
        $groupEdges = @($normalized | Where-Object group -eq $group)
        $scopeIds = @($groupEdges | Where-Object { $null -ne $_.scope_id } | ForEach-Object scope_id | Sort-Object -Unique)
        foreach ($scopeToken in (@("__unscoped__") + @($scopeIds))) {
            $isUnscoped = $scopeToken -eq "__unscoped__"
            $scopeId = if ($isUnscoped) {
                $null
            }
            else {
                $scopeToken
            }
            $edges = if ($isUnscoped) {
                @($groupEdges | Where-Object { $null -eq $_.scope_id })
            }
            else {
                @($groupEdges | Where-Object { $null -eq $_.scope_id -or $_.scope_id -eq $scopeId })
            }
            $nodes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
            $indegree = @{}
            $adjacency = @{}
            foreach ($edge in $edges) {
                [void]$nodes.Add($edge.source_id)
                [void]$nodes.Add($edge.target_id)
                if (-not $indegree.ContainsKey($edge.source_id)) {
                    $indegree[$edge.source_id] = 0
                }
                if (-not $indegree.ContainsKey($edge.target_id)) {
                    $indegree[$edge.target_id] = 0
                }
                if (-not $adjacency.ContainsKey($edge.source_id)) {
                    $adjacency[$edge.source_id] = @()
                }
                if ($adjacency[$edge.source_id] -cnotcontains $edge.target_id) {
                    $adjacency[$edge.source_id] = @($adjacency[$edge.source_id]) + $edge.target_id
                    $indegree[$edge.target_id] += 1
                }
            }
            $queue = New-Object 'System.Collections.Generic.Queue[string]'
            foreach ($nodeId in $nodes) {
                if ($indegree[$nodeId] -eq 0) {
                    $queue.Enqueue($nodeId)
                }
            }
            $processed = 0
            while ($queue.Count -gt 0) {
                $nodeId = $queue.Dequeue()
                $processed += 1
                if ($adjacency.ContainsKey($nodeId)) {
                    foreach ($targetId in @($adjacency[$nodeId])) {
                        $indegree[$targetId] -= 1
                        if ($indegree[$targetId] -eq 0) {
                            $queue.Enqueue($targetId)
                        }
                    }
                }
            }
            if ($processed -ne $nodes.Count) {
                $scopeDescription = "unscoped relationships"
                if (-not $isUnscoped) {
                    $scopeDescription = [string]$scopeId
                }
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
    $lookupKeys = Get-KnowledgeLookupKeyConfig $ProjectConfig

    $registryPath = $ProjectConfig.entities_registry
    $registry = ConvertFrom-KnowledgeYamlFile $registryPath $script:SupportedEntitySchemaVersion "entity registry"
    if ($null -eq $registry -or $registry -isnot [System.Collections.IDictionary]) {
        throw "Entity registry root must be a mapping: $registryPath"
    }
    $rootKeys = @(
        "schema_version"
        "entities"
        "entity_relationship_types"
        "entity_relationships"
        "incarnations"
        "incarnation_bindings"
        "incarnation_relationship_types"
        "incarnation_relationships"
        "identity_phases"
        "identity_phase_bindings"
        "identity_phase_relationship_types"
        "identity_phase_relationships"
    )
    Assert-KnowledgeMapKeys $registry $rootKeys "Entity registry root"
    $schemaVersion = Get-ProjectMapValue $registry "schema_version"
    if ($schemaVersion -isnot [int] -or $schemaVersion -ne $script:SupportedEntitySchemaVersion) {
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
        if ($entity -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $entity @("lifecycle", "primary_category_id", "category_ids", "label", "aliases") "Entity registry '$context'"
        $lifecycle = Get-RequiredEntityString $entity "lifecycle" $context
        if ($script:EntityLifecycles -cnotcontains $lifecycle) {
            throw "Entity registry '$context.lifecycle' must be one of: $($script:EntityLifecycles -join ', ')."
        }
        $primaryCategoryId = Get-RequiredEntityString $entity "primary_category_id" $context
        $categoryIds = @(Get-EntityStringList $entity "category_ids" $context)
        if ($categoryIds.Count -eq 0) {
            throw "Entity registry '$context.category_ids' cannot be empty."
        }
        foreach ($categoryId in $categoryIds) {
            if (-not $TaxonomyConfig.categories.Contains($categoryId)) {
                throw "Entity registry '$context.category_ids' references unknown category '$categoryId'."
            }
        }
        if ($categoryIds -cnotcontains $primaryCategoryId) {
            throw "Entity registry '$context.primary_category_id' must appear in category_ids."
        }
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
    if ($allowedMembershipStatuses.Count -eq 0) {
        throw "Selected schema packs do not provide controlled namespace 'source.membership-status'."
    }

    $rawEntityTypes = Get-ProjectMapValue $registry "entity_relationship_types"
    if ($null -eq $rawEntityTypes -or $rawEntityTypes -isnot [System.Collections.IDictionary]) {
        throw "Entity registry 'entity_relationship_types' must be a mapping."
    }
    $entityRelationshipTypes = [ordered]@{}
    foreach ($typeId in $rawEntityTypes.Keys) {
        $context = "entity_relationship_types.$typeId"
        Assert-EntityStableId $typeId $context
        Assert-EntityPackValue $SchemaPackRegistry "narrative.entity-relationship-type" $typeId $context
        $type = $rawEntityTypes[$typeId]
        if ($type -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $type @("label", "inverse_type", "symmetric", "canonical_direction", "acyclic_group") "Entity registry '$context'"
        $entityRelationshipTypes[$typeId] = [pscustomobject]@{
            id=$typeId
            label=Get-RequiredEntityString $type "label" $context
            inverse_type=Get-RequiredEntityString $type "inverse_type" $context
            symmetric=Get-RequiredEntityBoolean $type "symmetric" $context
            canonical_direction=Get-RequiredEntityBoolean $type "canonical_direction" $context
            acyclic_group=Get-OptionalEntityString $type "acyclic_group" $context
        }
        if ($null -ne $entityRelationshipTypes[$typeId].acyclic_group) {
            Assert-EntityStableId $entityRelationshipTypes[$typeId].acyclic_group "$context.acyclic_group"
        }
    }
    Assert-EntityRelationshipTypeInverses $entityRelationshipTypes "entity"

    $rawEntityRelationships = Get-ProjectMapValue $registry "entity_relationships"
    if ($null -eq $rawEntityRelationships) {
        $rawEntityRelationships = @()
    }
    if ($rawEntityRelationships -is [string]) {
        throw "Entity registry 'entity_relationships' must be a list."
    }
    $rawEntityRelationships = @($rawEntityRelationships)
    $entityRelationships = @()
    $entityRelationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $entityRelationshipShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $lineageRoleTypes = @("derived-from", "composite-of", "inspired-by")
    for ($index = 0; $index -lt $rawEntityRelationships.Count; $index += 1) {
        $context = "entity_relationships[$index]"
        $relationship = $rawEntityRelationships[$index]
        if ($relationship -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $relationship @("id", "source_entity_id", "target_entity_id", "relationship_type", "status", "applicability_scope_id", "basis_roles") "Entity registry '$context'"
        $id = Get-RequiredEntityString $relationship "id" $context
        Assert-EntityStableId $id "$context.id"
        if (-not $entityRelationshipIds.Add($id)) {
            throw "Entity registry repeats entity relationship ID '$id'."
        }
        $sourceId = Get-RequiredEntityString $relationship "source_entity_id" $context
        $targetId = Get-RequiredEntityString $relationship "target_entity_id" $context
        if (-not $entities.Contains($sourceId) -or -not $entities.Contains($targetId)) {
            throw "Entity registry '$context' references an unknown entity endpoint."
        }
        if ($sourceId -eq $targetId) {
            throw "Entity registry '$context' cannot relate an entity to itself."
        }
        $typeId = Get-RequiredEntityString $relationship "relationship_type" $context
        if (-not $entityRelationshipTypes.Contains($typeId)) {
            throw "Entity registry '$context.relationship_type' references unknown type '$typeId'."
        }
        $status = Get-RequiredEntityString $relationship "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs."
        }
        $scopeId = Get-OptionalEntityString $relationship "applicability_scope_id" $context
        if ($null -ne $scopeId -and -not $SourceRegistry.applicability_scopes.Contains($scopeId)) {
            throw "Entity registry '$context.applicability_scope_id' references unknown scope '$scopeId'."
        }
        $basisRoles = if ($relationship.Contains("basis_roles")) {
            @(Get-EntityStringList $relationship "basis_roles" $context)
        }
        else {
            @()
        }
        foreach ($basisRole in $basisRoles) {
            Assert-EntityPackValue $SchemaPackRegistry "narrative.entity-relationship-basis-role" $basisRole "$context.basis_roles"
        }
        if ($basisRoles.Count -gt 0 -and $lineageRoleTypes -cnotcontains $typeId) {
            throw "Entity registry '$context.basis_roles' is only valid for derived-from, composite-of, or inspired-by relationships."
        }
        $shape = Get-CanonicalEntityRelationshipShape $sourceId $typeId $targetId $scopeId $entityRelationshipTypes
        if (-not $entityRelationshipShapes.Add($shape)) {
            throw "Entity registry '$context' duplicates an entity relationship or its inverse."
        }
        $entityRelationships += [pscustomobject]@{ id=$id
            source_entity_id=$sourceId
            relationship_type=$typeId
            target_entity_id=$targetId
            status=$status
            applicability_scope_id=$scopeId
            basis_roles=@($basisRoles)
        }
    }
    Assert-AcyclicEntityRelationships $entityRelationships $entityRelationshipTypes "entity" "source_entity_id" "target_entity_id"

    $rawIncarnations = Get-ProjectMapValue $registry "incarnations"
    if ($null -eq $rawIncarnations -or $rawIncarnations -isnot [System.Collections.IDictionary]) {
        throw "Entity registry 'incarnations' must be a mapping."
    }
    $incarnations = [ordered]@{}
    foreach ($incarnationId in $rawIncarnations.Keys) {
        Assert-EntityStableId $incarnationId "incarnations.$incarnationId"
        $context = "incarnations.$incarnationId"
        $incarnation = $rawIncarnations[$incarnationId]
        if ($incarnation -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $incarnation @("lifecycle", "entity_id", "label", "aliases", "primary_continuity_id", "continuity_memberships") "Entity registry '$context'"
        $lifecycle = Get-RequiredEntityString $incarnation "lifecycle" $context
        if ($script:EntityLifecycles -cnotcontains $lifecycle) {
            throw "Entity registry '$context.lifecycle' must be one of: $($script:EntityLifecycles -join ', ')."
        }
        $entityId = Get-RequiredEntityString $incarnation "entity_id" $context
        if (-not $entities.Contains($entityId)) {
            throw "Entity registry '$context.entity_id' references unknown entity '$entityId'."
        }
        $primaryContinuityId = Get-RequiredEntityString $incarnation "primary_continuity_id" $context
        if (-not $SourceRegistry.continuities.Contains($primaryContinuityId)) {
            throw "Entity registry '$context.primary_continuity_id' references unknown continuity '$primaryContinuityId'."
        }
        $rawMemberships = Get-ProjectMapValue $incarnation "continuity_memberships"
        if ($null -eq $rawMemberships -or $rawMemberships -is [string]) {
            throw "Entity registry '$context.continuity_memberships' must be a non-empty list."
        }
        $rawMemberships = @($rawMemberships)
        if ($rawMemberships.Count -eq 0) {
            throw "Entity registry '$context.continuity_memberships' must be a non-empty list."
        }
        $memberships = @()
        $seenContinuities = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        for ($index = 0; $index -lt $rawMemberships.Count; $index += 1) {
            $membershipContext = "$context.continuity_memberships[$index]"
            $membership = $rawMemberships[$index]
            if ($membership -isnot [System.Collections.IDictionary]) {
                throw "Entity registry '$membershipContext' must be a mapping."
            }
            Assert-KnowledgeMapKeys $membership @("continuity_id", "status") "Entity registry '$membershipContext'"
            $continuityId = Get-RequiredEntityString $membership "continuity_id" $membershipContext
            if (-not $SourceRegistry.continuities.Contains($continuityId)) {
                throw "Entity registry '$membershipContext.continuity_id' references unknown continuity '$continuityId'."
            }
            if (-not $seenContinuities.Add($continuityId)) {
                throw "Entity registry '$context.continuity_memberships' repeats '$continuityId'."
            }
            $status = Get-RequiredEntityString $membership "status" $membershipContext
            if ($allowedMembershipStatuses -cnotcontains $status) {
                throw "Entity registry '$membershipContext.status' value '$status' is not supplied by selected schema packs."
            }
            $memberships += [pscustomobject]@{ continuity_id = $continuityId
                status = $status
            }
        }
        if (-not $seenContinuities.Contains($primaryContinuityId)) {
            throw "Entity registry '$context.primary_continuity_id' must appear in continuity_memberships."
        }
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
    if ($null -eq $rawBindings) {
        $rawBindings = @()
    }
    if ($rawBindings -is [string]) {
        throw "Entity registry 'incarnation_bindings' must be a list."
    }
    $rawBindings = @($rawBindings)
    $bindings = @()
    $bindingIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $bindingShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawBindings.Count; $index += 1) {
        $context = "incarnation_bindings[$index]"
        $binding = $rawBindings[$index]
        if ($binding -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $binding @("id", "incarnation_id", "applicability_scope_id", "binding_type", "status") "Entity registry '$context'"
        $id = Get-RequiredEntityString $binding "id" $context
        Assert-EntityStableId $id "$context.id"
        if (-not $bindingIds.Add($id)) {
            throw "Entity registry repeats binding ID '$id'."
        }
        $incarnationId = Get-RequiredEntityString $binding "incarnation_id" $context
        if (-not $incarnations.Contains($incarnationId)) {
            throw "Entity registry '$context.incarnation_id' references unknown incarnation '$incarnationId'."
        }
        $scopeId = Get-RequiredEntityString $binding "applicability_scope_id" $context
        if (-not $SourceRegistry.applicability_scopes.Contains($scopeId)) {
            throw "Entity registry '$context.applicability_scope_id' references unknown scope '$scopeId'."
        }
        $bindingType = Get-RequiredEntityString $binding "binding_type" $context
        Assert-EntityPackValue $SchemaPackRegistry "narrative.incarnation-binding-type" $bindingType "$context.binding_type"
        $status = Get-RequiredEntityString $binding "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs."
        }
        if (-not $bindingShapes.Add("$incarnationId|$scopeId|$bindingType")) {
            throw "Entity registry '$context' duplicates an incarnation binding."
        }
        $bindings += [pscustomobject]@{ id=$id
            incarnation_id=$incarnationId
            applicability_scope_id=$scopeId
            binding_type=$bindingType
            status=$status
        }
    }

    $rawTypes = Get-ProjectMapValue $registry "incarnation_relationship_types"
    if ($null -eq $rawTypes -or $rawTypes -isnot [System.Collections.IDictionary]) {
        throw "Entity registry 'incarnation_relationship_types' must be a mapping."
    }
    $relationshipTypes = [ordered]@{}
    foreach ($typeId in $rawTypes.Keys) {
        $context = "incarnation_relationship_types.$typeId"
        Assert-EntityStableId $typeId $context
        Assert-EntityPackValue $SchemaPackRegistry "narrative.incarnation-relationship-type" $typeId $context
        $type = $rawTypes[$typeId]
        if ($type -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $type @("label", "inverse_type", "symmetric", "canonical_direction", "acyclic_group") "Entity registry '$context'"
        $relationshipTypes[$typeId] = [pscustomobject]@{
            id=$typeId
            label=Get-RequiredEntityString $type "label" $context
            inverse_type=Get-RequiredEntityString $type "inverse_type" $context
            symmetric=Get-RequiredEntityBoolean $type "symmetric" $context
            canonical_direction=Get-RequiredEntityBoolean $type "canonical_direction" $context
            acyclic_group=Get-OptionalEntityString $type "acyclic_group" $context
        }
        if ($null -ne $relationshipTypes[$typeId].acyclic_group) {
            Assert-EntityStableId $relationshipTypes[$typeId].acyclic_group "$context.acyclic_group"
        }
    }
    Assert-EntityRelationshipTypeInverses $relationshipTypes "incarnation"

    $rawRelationships = Get-ProjectMapValue $registry "incarnation_relationships"
    if ($null -eq $rawRelationships) {
        $rawRelationships = @()
    }
    if ($rawRelationships -is [string]) {
        throw "Entity registry 'incarnation_relationships' must be a list."
    }
    $rawRelationships = @($rawRelationships)
    $relationships = @()
    $relationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $relationshipShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawRelationships.Count; $index += 1) {
        $context = "incarnation_relationships[$index]"
        $relationship = $rawRelationships[$index]
        if ($relationship -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $relationship @("id", "source_incarnation_id", "target_incarnation_id", "relationship_type", "status", "applicability_scope_id") "Entity registry '$context'"
        $id = Get-RequiredEntityString $relationship "id" $context
        Assert-EntityStableId $id "$context.id"
        if (-not $relationshipIds.Add($id)) {
            throw "Entity registry repeats relationship ID '$id'."
        }
        $sourceId = Get-RequiredEntityString $relationship "source_incarnation_id" $context
        $targetId = Get-RequiredEntityString $relationship "target_incarnation_id" $context
        if (-not $incarnations.Contains($sourceId) -or -not $incarnations.Contains($targetId)) {
            throw "Entity registry '$context' references an unknown incarnation endpoint."
        }
        if ($sourceId -eq $targetId) {
            throw "Entity registry '$context' cannot relate an incarnation to itself."
        }
        $typeId = Get-RequiredEntityString $relationship "relationship_type" $context
        if (-not $relationshipTypes.Contains($typeId)) {
            throw "Entity registry '$context.relationship_type' references unknown type '$typeId'."
        }
        $status = Get-RequiredEntityString $relationship "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs."
        }
        $scopeId = Get-OptionalEntityString $relationship "applicability_scope_id" $context
        if ($null -ne $scopeId -and -not $SourceRegistry.applicability_scopes.Contains($scopeId)) {
            throw "Entity registry '$context.applicability_scope_id' references unknown scope '$scopeId'."
        }
        $shape = Get-CanonicalEntityRelationshipShape $sourceId $typeId $targetId $scopeId $relationshipTypes
        if (-not $relationshipShapes.Add($shape)) {
            throw "Entity registry '$context' duplicates an incarnation relationship or its inverse."
        }
        $relationships += [pscustomobject]@{ id=$id
            source_incarnation_id=$sourceId
            relationship_type=$typeId
            target_incarnation_id=$targetId
            status=$status
            applicability_scope_id=$scopeId
        }
    }
    Assert-AcyclicEntityRelationships $relationships $relationshipTypes "incarnation" "source_incarnation_id" "target_incarnation_id"

    if (-not (Test-SchemaPackCapabilityEnabled $SchemaPackRegistry "entity-identity-phases")) {
        throw "Entity registry schema 4 requires enabled schema capability 'entity-identity-phases'."
    }

    $rawIdentityPhases = Get-ProjectMapValue $registry "identity_phases"
    if ($null -eq $rawIdentityPhases -or $rawIdentityPhases -isnot [System.Collections.IDictionary]) {
        throw "Entity registry 'identity_phases' must be a mapping."
    }
    $identityPhases = [ordered]@{}
    foreach ($phaseId in $rawIdentityPhases.Keys) {
        $context = "identity_phases.$phaseId"
        Assert-EntityStableId $phaseId $context
        $phase = $rawIdentityPhases[$phaseId]
        if ($phase -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $phase @("lifecycle", "subject_type", "subject_id", "continuity_id", "phase_type", "label", "aliases") "Entity registry '$context'"
        $lifecycle = Get-RequiredEntityString $phase "lifecycle" $context
        if ($script:EntityLifecycles -cnotcontains $lifecycle) {
            throw "Entity registry '$context.lifecycle' must be one of: $($script:EntityLifecycles -join ', ')."
        }
        $subjectType = Get-RequiredEntityString $phase "subject_type" $context
        Assert-EntityPackValue $SchemaPackRegistry "identity.phase-subject-type" $subjectType "$context.subject_type"
        $subjectId = Get-RequiredEntityString $phase "subject_id" $context
        if ($subjectType -eq "entity") {
            if (-not $entities.Contains($subjectId)) {
                throw "Entity registry '$context.subject_id' references unknown entity '$subjectId'."
            }
        }
        elseif ($subjectType -eq "entity-incarnation") {
            if (-not $incarnations.Contains($subjectId)) {
                throw "Entity registry '$context.subject_id' references unknown entity-incarnation '$subjectId'."
            }
        }
        else {
            throw "Entity registry '$context.subject_type' has no installed identity provider."
        }
        $continuityId = Get-RequiredEntityString $phase "continuity_id" $context
        if (-not $SourceRegistry.continuities.Contains($continuityId)) {
            throw "Entity registry '$context.continuity_id' references unknown continuity '$continuityId'."
        }
        if ($subjectType -eq "entity-incarnation" -and @($incarnations[$subjectId].continuity_memberships.continuity_id) -cnotcontains $continuityId) {
            throw "Entity registry '$context.continuity_id' is not a continuity membership of incarnation '$subjectId'."
        }
        $phaseType = Get-RequiredEntityString $phase "phase_type" $context
        Assert-EntityPackValue $SchemaPackRegistry "identity.phase-type" $phaseType "$context.phase_type"
        $identityPhases[$phaseId] = [pscustomobject]@{
            id=$phaseId
            lifecycle=$lifecycle
            subject_type=$subjectType
            subject_id=$subjectId
            continuity_id=$continuityId
            phase_type=$phaseType
            label=Get-RequiredEntityString $phase "label" $context
            aliases=@(Get-EntityStringList $phase "aliases" $context)
        }
    }

    $rawPhaseBindings = Get-ProjectMapValue $registry "identity_phase_bindings"
    if ($null -eq $rawPhaseBindings) {
        $rawPhaseBindings = @()
    }
    if ($rawPhaseBindings -is [string]) {
        throw "Entity registry 'identity_phase_bindings' must be a list."
    }
    $rawPhaseBindings = @($rawPhaseBindings)
    $phaseBindings = @()
    $phaseBindingIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $phaseBindingShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawPhaseBindings.Count; $index += 1) {
        $context = "identity_phase_bindings[$index]"
        $binding = $rawPhaseBindings[$index]
        if ($binding -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $binding @("id", "identity_phase_id", "applicability_scope_id", "binding_type", "status") "Entity registry '$context'"
        $id = Get-RequiredEntityString $binding "id" $context
        Assert-EntityStableId $id "$context.id"
        if (-not $phaseBindingIds.Add($id)) {
            throw "Entity registry repeats identity-phase binding ID '$id'."
        }
        $phaseId = Get-RequiredEntityString $binding "identity_phase_id" $context
        if (-not $identityPhases.Contains($phaseId)) {
            throw "Entity registry '$context.identity_phase_id' references unknown identity phase '$phaseId'."
        }
        $scopeId = Get-RequiredEntityString $binding "applicability_scope_id" $context
        if (-not $SourceRegistry.applicability_scopes.Contains($scopeId)) {
            throw "Entity registry '$context.applicability_scope_id' references unknown scope '$scopeId'."
        }
        $scope = $SourceRegistry.applicability_scopes[$scopeId]
        $workIds = @(Get-KnowledgeApplicabilityTargetWorkIds $SourceRegistry $scope.target_type $scope.target_id)
        if ($workIds.Count -eq 0) {
            throw "Entity registry '$context.applicability_scope_id' must resolve to source material with a canonical work."
        }
        $phaseContinuityId = $identityPhases[$phaseId].continuity_id
        foreach ($workId in $workIds) {
            if (@($SourceRegistry.works[$workId].continuity_memberships.continuity_id) -cnotcontains $phaseContinuityId) {
                throw "Entity registry '$context.applicability_scope_id' resolves outside phase continuity '$phaseContinuityId'."
            }
        }
        $bindingType = Get-RequiredEntityString $binding "binding_type" $context
        Assert-EntityPackValue $SchemaPackRegistry "identity.phase-binding-type" $bindingType "$context.binding_type"
        $status = Get-RequiredEntityString $binding "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs."
        }
        if (-not $phaseBindingShapes.Add("$phaseId|$scopeId|$bindingType")) {
            throw "Entity registry '$context' duplicates an identity-phase binding."
        }
        $phaseBindings += [pscustomobject]@{ id=$id
            identity_phase_id=$phaseId
            applicability_scope_id=$scopeId
            binding_type=$bindingType
            status=$status
        }
    }

    $rawPhaseTypes = Get-ProjectMapValue $registry "identity_phase_relationship_types"
    if ($null -eq $rawPhaseTypes -or $rawPhaseTypes -isnot [System.Collections.IDictionary]) {
        throw "Entity registry 'identity_phase_relationship_types' must be a mapping."
    }
    $phaseRelationshipTypes = [ordered]@{}
    foreach ($typeId in $rawPhaseTypes.Keys) {
        $context = "identity_phase_relationship_types.$typeId"
        Assert-EntityStableId $typeId $context
        Assert-EntityPackValue $SchemaPackRegistry "identity.phase-relationship-type" $typeId $context
        $type = $rawPhaseTypes[$typeId]
        if ($type -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $type @("label", "inverse_type", "symmetric", "canonical_direction", "acyclic_group") "Entity registry '$context'"
        $phaseRelationshipTypes[$typeId] = [pscustomobject]@{
            id=$typeId
            label=Get-RequiredEntityString $type "label" $context
            inverse_type=Get-RequiredEntityString $type "inverse_type" $context
            symmetric=Get-RequiredEntityBoolean $type "symmetric" $context
            canonical_direction=Get-RequiredEntityBoolean $type "canonical_direction" $context
            acyclic_group=Get-OptionalEntityString $type "acyclic_group" $context
        }
        if ($null -ne $phaseRelationshipTypes[$typeId].acyclic_group) {
            Assert-EntityStableId $phaseRelationshipTypes[$typeId].acyclic_group "$context.acyclic_group"
        }
    }
    Assert-EntityRelationshipTypeInverses $phaseRelationshipTypes "identity-phase"

    $rawPhaseRelationships = Get-ProjectMapValue $registry "identity_phase_relationships"
    if ($null -eq $rawPhaseRelationships) {
        $rawPhaseRelationships = @()
    }
    if ($rawPhaseRelationships -is [string]) {
        throw "Entity registry 'identity_phase_relationships' must be a list."
    }
    $rawPhaseRelationships = @($rawPhaseRelationships)
    $phaseRelationships = @()
    $phaseRelationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $phaseRelationshipShapes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawPhaseRelationships.Count; $index += 1) {
        $context = "identity_phase_relationships[$index]"
        $relationship = $rawPhaseRelationships[$index]
        if ($relationship -isnot [System.Collections.IDictionary]) {
            throw "Entity registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $relationship @("id", "source_identity_phase_id", "target_identity_phase_id", "relationship_type", "status") "Entity registry '$context'"
        $id = Get-RequiredEntityString $relationship "id" $context
        Assert-EntityStableId $id "$context.id"
        if (-not $phaseRelationshipIds.Add($id)) {
            throw "Entity registry repeats identity-phase relationship ID '$id'."
        }
        $sourceId = Get-RequiredEntityString $relationship "source_identity_phase_id" $context
        $targetId = Get-RequiredEntityString $relationship "target_identity_phase_id" $context
        if (-not $identityPhases.Contains($sourceId) -or -not $identityPhases.Contains($targetId)) {
            throw "Entity registry '$context' references an unknown identity-phase endpoint."
        }
        if ($sourceId -eq $targetId) {
            throw "Entity registry '$context' cannot relate an identity phase to itself."
        }
        $sourcePhase = $identityPhases[$sourceId]
        $targetPhase = $identityPhases[$targetId]
        if ($sourcePhase.subject_type -ne $targetPhase.subject_type -or $sourcePhase.subject_id -ne $targetPhase.subject_id -or $sourcePhase.continuity_id -ne $targetPhase.continuity_id) {
            throw "Entity registry '$context' must relate phases of the same identity subject and continuity."
        }
        $typeId = Get-RequiredEntityString $relationship "relationship_type" $context
        if (-not $phaseRelationshipTypes.Contains($typeId)) {
            throw "Entity registry '$context.relationship_type' references unknown type '$typeId'."
        }
        $status = Get-RequiredEntityString $relationship "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Entity registry '$context.status' value '$status' is not supplied by selected schema packs."
        }
        $shape = Get-CanonicalEntityRelationshipShape $sourceId $typeId $targetId $null $phaseRelationshipTypes
        if (-not $phaseRelationshipShapes.Add($shape)) {
            throw "Entity registry '$context' duplicates an identity-phase relationship or its inverse."
        }
        $phaseRelationships += [pscustomobject]@{ id=$id
            source_identity_phase_id=$sourceId
            relationship_type=$typeId
            target_identity_phase_id=$targetId
            status=$status
        }
    }
    Assert-AcyclicEntityRelationships $phaseRelationships $phaseRelationshipTypes "identity-phase" "source_identity_phase_id" "target_identity_phase_id"

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
        identity_phases=$identityPhases
        identity_phase_bindings=@($phaseBindings)
        identity_phase_relationship_types=$phaseRelationshipTypes
        identity_phase_relationships=@($phaseRelationships)
        lookup_keys=$lookupKeys
        entity_aliases=New-EntityAliasMap $entities "entity" $lookupKeys
        incarnation_aliases=New-EntityAliasMap $incarnations "incarnation" $lookupKeys
        identity_phase_aliases=New-EntityAliasMap $identityPhases "identity phase" $lookupKeys
    }
}

function Resolve-KnowledgeEntityId {
    param([object]$EntityRegistry, [string]$Value)
    $matches = @(Resolve-KnowledgeEntityIds $EntityRegistry $Value)
    if ($matches.Count -gt 1) {
        throw "Ambiguous entity name '$Value' matches: $($matches -join ', ')."
    }
    return $(if ($matches.Count -eq 1) {
            $matches[0]
        }
        else {
            $null
        })
}

function Resolve-KnowledgeEntityIds {
    param([object]$EntityRegistry, [string]$Value)
    $normalized = ConvertTo-KnowledgeLookupKey $Value $EntityRegistry.lookup_keys
    foreach ($entityId in $EntityRegistry.entities.Keys) {
        if (Test-KnowledgeLookupKeysEqual (ConvertTo-KnowledgeLookupKey $entityId $EntityRegistry.lookup_keys) $normalized) {
            return @($entityId)
        }
    }
    if ($EntityRegistry.entity_aliases.ContainsKey($normalized)) {
        return @($EntityRegistry.entity_aliases[$normalized])
    }
    return @()
}

function Resolve-KnowledgeIncarnationId {
    param([object]$EntityRegistry, [string]$Value)
    $matches = @(Resolve-KnowledgeIncarnationIds $EntityRegistry $Value)
    if ($matches.Count -gt 1) {
        throw "Ambiguous incarnation name '$Value' matches: $($matches -join ', ')."
    }
    return $(if ($matches.Count -eq 1) {
            $matches[0]
        }
        else {
            $null
        })
}

function Resolve-KnowledgeIncarnationIds {
    param([object]$EntityRegistry, [string]$Value)
    $normalized = ConvertTo-KnowledgeLookupKey $Value $EntityRegistry.lookup_keys
    foreach ($incarnationId in $EntityRegistry.incarnations.Keys) {
        if (Test-KnowledgeLookupKeysEqual (ConvertTo-KnowledgeLookupKey $incarnationId $EntityRegistry.lookup_keys) $normalized) {
            return @($incarnationId)
        }
    }
    if ($EntityRegistry.incarnation_aliases.ContainsKey($normalized)) {
        return @($EntityRegistry.incarnation_aliases[$normalized])
    }
    return @()
}

function Get-KnowledgeEntityIncarnations {
    param([object]$EntityRegistry, [string]$EntityId)
    if (-not $EntityRegistry.entities.Contains($EntityId)) {
        throw "Unknown entity '$EntityId'."
    }
    return @($EntityRegistry.incarnations.Values | Where-Object entity_id -eq $EntityId)
}

function Get-KnowledgeEntityRelationships {
    param([object]$EntityRegistry, [string]$EntityId)
    if (-not $EntityRegistry.entities.Contains($EntityId)) {
        throw "Unknown entity '$EntityId'."
    }
    return @($EntityRegistry.entity_relationships | Where-Object {
            $_.source_entity_id -eq $EntityId -or $_.target_entity_id -eq $EntityId
        })
}

function Get-KnowledgeIncarnationBindings {
    param([object]$EntityRegistry, [string]$IncarnationId)
    if (-not $EntityRegistry.incarnations.Contains($IncarnationId)) {
        throw "Unknown incarnation '$IncarnationId'."
    }
    return @($EntityRegistry.incarnation_bindings | Where-Object incarnation_id -eq $IncarnationId)
}

function Get-KnowledgeIncarnationRelationships {
    param([object]$EntityRegistry, [string]$IncarnationId)
    if (-not $EntityRegistry.incarnations.Contains($IncarnationId)) {
        throw "Unknown incarnation '$IncarnationId'."
    }
    return @($EntityRegistry.incarnation_relationships | Where-Object {
            $_.source_incarnation_id -eq $IncarnationId -or $_.target_incarnation_id -eq $IncarnationId
        })
}

function Resolve-KnowledgeIdentityPhaseIds {
    param([object]$EntityRegistry, [string]$Value)
    $normalized = ConvertTo-KnowledgeLookupKey $Value $EntityRegistry.lookup_keys
    foreach ($phaseId in $EntityRegistry.identity_phases.Keys) {
        if (Test-KnowledgeLookupKeysEqual (ConvertTo-KnowledgeLookupKey $phaseId $EntityRegistry.lookup_keys) $normalized) {
            return @($phaseId)
        }
    }
    if ($EntityRegistry.identity_phase_aliases.ContainsKey($normalized)) {
        return @($EntityRegistry.identity_phase_aliases[$normalized])
    }
    return @()
}

function Resolve-KnowledgeIdentityPhaseId {
    param([object]$EntityRegistry, [string]$Value)
    $matches = @(Resolve-KnowledgeIdentityPhaseIds $EntityRegistry $Value)
    if ($matches.Count -gt 1) {
        throw "Ambiguous identity-phase name '$Value' matches: $($matches -join ', ')."
    }
    return $(if ($matches.Count -eq 1) {
            $matches[0]
        }
        else {
            $null
        })
}

function Get-KnowledgeIdentitySubjectTypes {
    return @("entity", "entity-incarnation")
}

function Get-KnowledgeIdentityTargetTypes {
    return @("entity", "entity-incarnation", "identity-phase")
}

function Get-KnowledgeEntityReconciliationTargetTypes {
    return @(Get-KnowledgeIdentityTargetTypes)
}

function Get-KnowledgeEntityReconciliationTargets {
    param([object]$EntityRegistry)
    return [ordered]@{entity=$EntityRegistry.entities
        "entity-incarnation"=$EntityRegistry.incarnations
        "identity-phase"=$EntityRegistry.identity_phases
    }
}

function Get-KnowledgeEntityReconciliationProvider {
    param([object]$EntityRegistry)
    return [pscustomobject]@{
        provider_id="entity"
        targets=(Get-KnowledgeEntityReconciliationTargets $EntityRegistry)
        aliases=[ordered]@{entity=$EntityRegistry.entity_aliases
            "entity-incarnation"=$EntityRegistry.incarnation_aliases
            "identity-phase"=$EntityRegistry.identity_phase_aliases
        }
    }
}

function Get-KnowledgeEntityReconciliationTarget {
    param([object]$EntityRegistry, [string]$TargetType, [string]$TargetId)
    return Get-KnowledgeIdentityTarget $EntityRegistry $TargetType $TargetId
}

function Get-KnowledgeIdentitySubjectTarget {
    param([object]$EntityRegistry, [string]$SubjectType, [string]$SubjectId)
    if (@(Get-KnowledgeIdentitySubjectTypes) -cnotcontains $SubjectType) {
        throw "Unsupported identity subject type '$SubjectType'."
    }
    return Get-KnowledgeIdentityTarget $EntityRegistry $SubjectType $SubjectId
}

function Get-KnowledgeIdentityTarget {
    param([object]$EntityRegistry, [string]$SubjectType, [string]$SubjectId)
    switch ($SubjectType) {
        "entity" {
            if ($EntityRegistry.entities.Contains($SubjectId)) {
                return $EntityRegistry.entities[$SubjectId]
            }
        }
        "entity-incarnation" {
            if ($EntityRegistry.incarnations.Contains($SubjectId)) {
                return $EntityRegistry.incarnations[$SubjectId]
            }
        }
        "identity-phase" {
            if ($EntityRegistry.identity_phases.Contains($SubjectId)) {
                return $EntityRegistry.identity_phases[$SubjectId]
            }
        }
        default {
            throw "Unsupported identity target type '$SubjectType'."
        }
    }
    throw "Unknown $SubjectType '$SubjectId'."
}

function Get-KnowledgeIdentityPhases {
    param([object]$EntityRegistry, [string]$SubjectType, [string]$SubjectId)
    $null = Get-KnowledgeIdentityTarget $EntityRegistry $SubjectType $SubjectId
    if ($SubjectType -eq "identity-phase") {
        throw "Identity phases cannot own nested identity phases."
    }
    return @($EntityRegistry.identity_phases.Values | Where-Object { $_.subject_type -eq $SubjectType -and $_.subject_id -eq $SubjectId })
}

function Get-KnowledgeIdentityPhaseBindings {
    param([object]$EntityRegistry, [string]$IdentityPhaseId)
    if (-not $EntityRegistry.identity_phases.Contains($IdentityPhaseId)) {
        throw "Unknown identity-phase '$IdentityPhaseId'."
    }
    return @($EntityRegistry.identity_phase_bindings | Where-Object identity_phase_id -eq $IdentityPhaseId)
}

function Get-KnowledgeIdentityPhaseRelationships {
    param([object]$EntityRegistry, [string]$IdentityPhaseId)
    if (-not $EntityRegistry.identity_phases.Contains($IdentityPhaseId)) {
        throw "Unknown identity-phase '$IdentityPhaseId'."
    }
    return @($EntityRegistry.identity_phase_relationships | Where-Object { $_.source_identity_phase_id -eq $IdentityPhaseId -or $_.target_identity_phase_id -eq $IdentityPhaseId })
}

function Get-KnowledgeEntityProvenanceSubjectTypes {
    return @("entity", "entity-relationship", "entity-incarnation", "incarnation-binding", "incarnation-relationship", "identity-phase", "identity-phase-binding", "identity-phase-relationship")
}

function Get-KnowledgeEntityProvenanceTarget {
    param([object]$EntityRegistry, [string]$SubjectType, [string]$SubjectId)

    switch ($SubjectType) {
        "entity" {
            if ($EntityRegistry.entities.Contains($SubjectId)) {
                return $EntityRegistry.entities[$SubjectId]
            }
        }
        "entity-relationship" {
            $target = @($EntityRegistry.entity_relationships | Where-Object id -eq $SubjectId)
            if ($target.Count -eq 1) {
                return $target[0]
            }
        }
        "entity-incarnation" {
            if ($EntityRegistry.incarnations.Contains($SubjectId)) {
                return $EntityRegistry.incarnations[$SubjectId]
            }
        }
        "incarnation-binding" {
            $target = @($EntityRegistry.incarnation_bindings | Where-Object id -eq $SubjectId)
            if ($target.Count -eq 1) {
                return $target[0]
            }
        }
        "incarnation-relationship" {
            $target = @($EntityRegistry.incarnation_relationships | Where-Object id -eq $SubjectId)
            if ($target.Count -eq 1) {
                return $target[0]
            }
        }
        "identity-phase" {
            if ($EntityRegistry.identity_phases.Contains($SubjectId)) {
                return $EntityRegistry.identity_phases[$SubjectId]
            }
        }
        "identity-phase-binding" {
            $target = @($EntityRegistry.identity_phase_bindings | Where-Object id -eq $SubjectId)
            if ($target.Count -eq 1) {
                return $target[0]
            }
        }
        "identity-phase-relationship" {
            $target = @($EntityRegistry.identity_phase_relationships | Where-Object id -eq $SubjectId)
            if ($target.Count -eq 1) {
                return $target[0]
            }
        }
        default {
            throw "Unsupported entity-registry subject type '$SubjectType'."
        }
    }
    throw "Unknown $SubjectType '$SubjectId'."
}
