$script:SupportedInterpretationSchemaVersion = 1
$script:InterpretationStableIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'

function Get-RequiredInterpretationString {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)) {
        throw "Structural interpretation registry '$Context.$Key' must be a non-empty string."
    }
    return $value.Trim()
}

function Get-OptionalInterpretationString {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        return $null
    }
    if ($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)) {
        throw "Structural interpretation registry '$Context.$Key' must be a non-empty string or null."
    }
    return $value.Trim()
}

function Get-RequiredInterpretationBoolean {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($value -isnot [bool]) {
        throw "Structural interpretation registry '$Context.$Key' must be true or false."
    }
    return [bool]$value
}

function Get-InterpretationStringList {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if (
        $null -eq $value -or
        $value -is [string] -or
        $value -is [System.Collections.IDictionary] -or
        $value -isnot [System.Collections.IEnumerable]
    ) {
        throw "Structural interpretation registry '$Context.$Key' must be a list."
    }
    $result = @()
    foreach ($entry in @($value)) {
        if ($entry -isnot [string] -or [string]::IsNullOrWhiteSpace($entry)) {
            throw "Structural interpretation registry '$Context.$Key' must contain non-empty strings."
        }
        $result += $entry.Trim()
    }
    return @($result)
}

function Assert-InterpretationMap {
    param([object]$Value, [string]$Context)

    if ($Value -isnot [System.Collections.IDictionary]) {
        throw "Structural interpretation registry '$Context' must be a mapping."
    }
}

function Assert-InterpretationList {
    param([object]$Value, [string]$Context)

    if ($Value -is [string] -or $Value -isnot [System.Collections.IList]) {
        throw "Structural interpretation registry '$Context' must be a list."
    }
}

function Assert-InterpretationStableId {
    param([string]$Value, [string]$Context)

    if ($Value -cnotmatch $script:InterpretationStableIdPattern) {
        throw "Structural interpretation registry '$Context' must be a lowercase kebab-case stable ID: $Value"
    }
}

function Assert-InterpretationPackValue {
    param([object]$Packs, [string]$Namespace, [string]$Value, [string]$Context)

    if (@(Get-SchemaPackAllowedValues $Packs $Namespace) -cnotcontains $Value) {
        throw "Structural interpretation registry '$Context' value '$Value' is not allowed by '$Namespace'."
    }
}

function New-KnowledgeInterpretationTargetProvider {
    param(
        [string]$ProviderId,
        [string[]]$TargetTypes,
        [scriptblock]$Resolver
    )

    return [pscustomobject]@{
        provider_id = $ProviderId
        target_types = @($TargetTypes)
        resolver = $Resolver
    }
}

function Get-KnowledgeInterpretationProjectTargetProviders {
    param(
        [object]$Sources,
        [object]$Entities,
        [object]$Reconciliation,
        [object]$Chronology,
        [object]$Occurrences
    )

    $sourceResolver = { param($Type, $Id) Get-KnowledgeSourceProvenanceTarget $Sources $Type $Id }.GetNewClosure()
    $entityResolver = { param($Type, $Id) Get-KnowledgeEntityProvenanceTarget $Entities $Type $Id }.GetNewClosure()
    $reconciliationResolver = {
        param($Type, $Id)
        Get-KnowledgeReconciliationProvenanceTarget $Reconciliation $Type $Id
    }.GetNewClosure()
    $chronologyTargets = Get-KnowledgeChronologyProvenanceTargets $Chronology
    $chronologyResolver = {
        param($Type, $Id)
        if (-not $chronologyTargets.Contains($Type) -or -not $chronologyTargets[$Type].Contains($Id)) {
            throw "Unknown fixture target '$Type`:$Id'."
        }
        return $chronologyTargets[$Type][$Id]
    }.GetNewClosure()
    $occurrenceTargets = Get-KnowledgeOccurrenceProvenanceTargets $Occurrences
    $occurrenceResolver = {
        param($Type, $Id)
        if (-not $occurrenceTargets.Contains($Type) -or -not $occurrenceTargets[$Type].Contains($Id)) {
            throw "Unknown fixture target '$Type`:$Id'."
        }
        return $occurrenceTargets[$Type][$Id]
    }.GetNewClosure()

    return @(
        (New-KnowledgeInterpretationTargetProvider `
            'source' `
        (Get-KnowledgeSourceProvenanceSubjectTypes) `
            $sourceResolver)
        (New-KnowledgeInterpretationTargetProvider `
            'entity' `
        (Get-KnowledgeEntityProvenanceSubjectTypes) `
            $entityResolver)
        (New-KnowledgeInterpretationTargetProvider `
            'reconciliation' `
        (Get-KnowledgeReconciliationProvenanceSubjectTypes) `
            $reconciliationResolver)
        (New-KnowledgeInterpretationTargetProvider `
            'chronology' `
        @($chronologyTargets.Keys) `
            $chronologyResolver)
        (New-KnowledgeInterpretationTargetProvider `
            'occurrence' `
        @($occurrenceTargets.Keys) `
            $occurrenceResolver)
    )
}

function Get-CanonicalInterpretationRelationShape {
    param([object]$Relation, [object]$RelationTypes)

    $type = $RelationTypes[$Relation.relationship_type]
    $sourceId = [string]$Relation.source_member_id
    $targetId = [string]$Relation.target_member_id
    $typeId = [string]$Relation.relationship_type
    if ($type.symmetric) {
        $ordered = @($sourceId, $targetId) | Sort-Object
        $sourceId = $ordered[0]
        $targetId = $ordered[1]
    }
    elseif (-not $type.canonical_direction) {
        $temporary = $sourceId
        $sourceId = $targetId
        $targetId = $temporary
        $typeId = [string]$type.inverse_type
    }
    return "$($Relation.interpretation_id)|$sourceId|$typeId|$targetId"
}

function Assert-InterpretationRelationTypes {
    param([object]$RelationTypes)

    foreach ($type in $RelationTypes.Values) {
        if (-not $RelationTypes.Contains($type.inverse_type)) {
            throw "Structural interpretation relation type '$($type.id)' references unknown inverse '$($type.inverse_type)'."
        }
        $inverse = $RelationTypes[$type.inverse_type]
        if ($inverse.inverse_type -cne $type.id) {
            throw "Structural interpretation relation type '$($type.id)' has a nonreciprocal inverse."
        }
        if ($type.symmetric) {
            if ($type.inverse_type -cne $type.id) {
                throw "Symmetric structural interpretation relation type '$($type.id)' must be self-inverse."
            }
            if ($type.canonical_direction) {
                throw "Symmetric structural interpretation relation type '$($type.id)' cannot declare canonical direction."
            }
            if ($null -ne $type.acyclic_group) {
                throw "Symmetric structural interpretation relation type '$($type.id)' cannot enter an acyclic group."
            }
        }
        else {
            if ($inverse.symmetric) {
                throw "Structural interpretation relation type '$($type.id)' has a symmetric inverse."
            }
            if ($type.canonical_direction -eq $inverse.canonical_direction) {
                throw "Structural interpretation inverse pair '$($type.id)' and '$($inverse.id)' must define exactly one canonical direction."
            }
            if ($type.acyclic_group -cne $inverse.acyclic_group) {
                throw "Structural interpretation inverse pair '$($type.id)' and '$($inverse.id)' must share one acyclic group."
            }
        }
    }
}

function Assert-InterpretationRelationsAcyclic {
    param([object[]]$Relations, [object]$RelationTypes)

    $graph = @{}
    foreach ($relation in $Relations) {
        $type = $RelationTypes[$relation.relationship_type]
        if ($null -eq $type.acyclic_group) {
            continue
        }
        $shape = (Get-CanonicalInterpretationRelationShape $relation $RelationTypes).Split('|')
        $node = "$($shape[0])|$($type.acyclic_group)|$($shape[1])"
        if (-not $graph.Contains($node)) {
            $graph[$node] = @()
        }
        $graph[$node] = @($graph[$node]) + @($shape[3])
    }

    $visiting = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $visited = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    function Visit-InterpretationRelation([string]$Node) {
        if ($visiting.Contains($Node)) {
            $parts = $Node.Split('|')
            throw "Structural interpretation registry contains an interpretation-local relationship cycle in '$($parts[0])' group '$($parts[1])' involving '$($parts[2])'."
        }
        if ($visited.Contains($Node)) {
            return
        }
        $null = $visiting.Add($Node)
        $parts = $Node.Split('|')
        if ($graph.Contains($Node)) {
            foreach ($targetId in @($graph[$Node])) {
                Visit-InterpretationRelation "$($parts[0])|$($parts[1])|$targetId"
            }
        }
        $null = $visiting.Remove($Node)
        $null = $visited.Add($Node)
    }
    foreach ($node in @($graph.Keys)) {
        Visit-InterpretationRelation $node
    }
}

function Get-KnowledgeInterpretationRegistry {
    param(
        [object]$Project,
        [object]$SchemaPackRegistry,
        [object[]]$TargetProviders
    )

    if (-not (Test-SchemaPackCapabilityEnabled $SchemaPackRegistry 'structural-interpretation-modeling')) {
        throw "Structural interpretation registry requires enabled capability 'structural-interpretation-modeling'."
    }
    $path = $Project.interpretations_registry
    $root = ConvertFrom-KnowledgeYamlFile `
        $path `
        $script:SupportedInterpretationSchemaVersion `
        'structural interpretation registry'
    Assert-InterpretationMap $root 'root'
    Assert-KnowledgeMapKeys `
        $root `
    @('schema_version', 'relation_types', 'interpretations', 'members', 'relations', 'comparison_sets') `
        'Structural interpretation registry root'

    $relationTypes = @{}
    $rawRelationTypes = Get-ProjectMapValue $root 'relation_types'
    Assert-InterpretationMap $rawRelationTypes 'relation_types'
    foreach ($typeId in $rawRelationTypes.Keys) {
        Assert-InterpretationStableId $typeId "relation_types.$typeId"
        Assert-InterpretationPackValue `
            $SchemaPackRegistry `
            'interpretation.relation-type' `
            $typeId `
            "relation_types.$typeId"
        $context = "relation_types.$typeId"
        $item = $rawRelationTypes[$typeId]
        Assert-InterpretationMap $item $context
        Assert-KnowledgeMapKeys `
            $item `
        @('label', 'inverse_type', 'symmetric', 'canonical_direction', 'acyclic_group') `
            "Structural interpretation registry '$context'"
        $group = Get-OptionalInterpretationString $item 'acyclic_group' $context
        if ($null -ne $group) {
            Assert-InterpretationStableId $group "$context.acyclic_group"
        }
        $relationTypes[$typeId] = [pscustomobject]@{
            id = $typeId
            label = Get-RequiredInterpretationString $item 'label' $context
            inverse_type = Get-RequiredInterpretationString $item 'inverse_type' $context
            symmetric = Get-RequiredInterpretationBoolean $item 'symmetric' $context
            canonical_direction = Get-RequiredInterpretationBoolean $item 'canonical_direction' $context
            acyclic_group = $group
        }
    }
    Assert-InterpretationRelationTypes $relationTypes

    $interpretations = @{}
    $rawInterpretations = Get-ProjectMapValue $root 'interpretations'
    Assert-InterpretationMap $rawInterpretations 'interpretations'
    foreach ($id in $rawInterpretations.Keys) {
        Assert-InterpretationStableId $id "interpretations.$id"
        $context = "interpretations.$id"
        $item = $rawInterpretations[$id]
        Assert-InterpretationMap $item $context
        Assert-KnowledgeMapKeys `
            $item `
        @('lifecycle', 'label', 'description') `
            "Structural interpretation registry '$context'"
        $lifecycle = Get-RequiredInterpretationString $item 'lifecycle' $context
        Assert-InterpretationPackValue `
            $SchemaPackRegistry `
            'interpretation.lifecycle' `
            $lifecycle `
            "$context.lifecycle"
        $interpretations[$id] = [pscustomobject]@{
            id = $id
            lifecycle = $lifecycle
            label = Get-RequiredInterpretationString $item 'label' $context
            description = Get-OptionalInterpretationString $item 'description' $context
        }
    }

    $providerByType = @{}
    foreach ($provider in $TargetProviders) {
        foreach ($targetType in @($provider.target_types)) {
            if ($providerByType.Contains($targetType)) {
                throw "Structural interpretation target type '$targetType' has multiple providers."
            }
            $providerByType[$targetType] = $provider
        }
    }
    $prohibitedTargets = @(
        'structural-interpretation'
        'structural-interpretation-member'
        'structural-interpretation-relation'
        'structural-interpretation-set'
    )
    $members = @()
    $memberIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $semanticMembers = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawMembers = $root['members']
    Assert-InterpretationList $rawMembers 'members'
    for ($index = 0; $index -lt $rawMembers.Count; $index += 1) {
        $context = "members[$index]"
        $item = $rawMembers[$index]
        Assert-InterpretationMap $item $context
        Assert-KnowledgeMapKeys `
            $item `
        @('id', 'interpretation_id', 'target_type', 'target_id') `
            "Structural interpretation registry '$context'"
        $id = Get-RequiredInterpretationString $item 'id' $context
        Assert-InterpretationStableId $id "$context.id"
        if (-not $memberIds.Add($id)) {
            throw "Structural interpretation member ID '$id' is duplicated."
        }
        $interpretationId = Get-RequiredInterpretationString $item 'interpretation_id' $context
        if (-not $interpretations.Contains($interpretationId)) {
            throw "$context.interpretation_id references unknown interpretation '$interpretationId'."
        }
        $targetType = Get-RequiredInterpretationString $item 'target_type' $context
        $targetId = Get-RequiredInterpretationString $item 'target_id' $context
        if ($prohibitedTargets -ccontains $targetType) {
            throw "$context.target_type cannot recursively reference '$targetType'."
        }
        if ($targetType -cne 'provenance-claim') {
            if (-not $providerByType.Contains($targetType)) {
                throw "$context.target_type references unsupported target type '$targetType'."
            }
            $null = & $providerByType[$targetType].resolver $targetType $targetId
        }
        $shape = "$interpretationId|$targetType|$targetId"
        if (-not $semanticMembers.Add($shape)) {
            throw "Structural interpretation '$interpretationId' repeats target '$targetType`:$targetId'."
        }
        $members += [pscustomobject]@{
            id = $id
            interpretation_id = $interpretationId
            target_type = $targetType
            target_id = $targetId
        }
    }

    $memberMap = @{}
    foreach ($member in $members) {
        $memberMap[$member.id] = $member
    }
    $relations = @()
    $relationIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $semanticRelations = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawRelations = $root['relations']
    Assert-InterpretationList $rawRelations 'relations'
    for ($index = 0; $index -lt $rawRelations.Count; $index += 1) {
        $context = "relations[$index]"
        $item = $rawRelations[$index]
        Assert-InterpretationMap $item $context
        Assert-KnowledgeMapKeys `
            $item `
        @('id', 'interpretation_id', 'source_member_id', 'relationship_type', 'target_member_id') `
            "Structural interpretation registry '$context'"
        $id = Get-RequiredInterpretationString $item 'id' $context
        Assert-InterpretationStableId $id "$context.id"
        if (-not $relationIds.Add($id)) {
            throw "Structural interpretation relation ID '$id' is duplicated."
        }
        $interpretationId = Get-RequiredInterpretationString $item 'interpretation_id' $context
        if (-not $interpretations.Contains($interpretationId)) {
            throw "$context.interpretation_id references unknown interpretation '$interpretationId'."
        }
        $sourceId = Get-RequiredInterpretationString $item 'source_member_id' $context
        $targetId = Get-RequiredInterpretationString $item 'target_member_id' $context
        if ($sourceId -ceq $targetId) {
            throw "Structural interpretation relation '$id' cannot relate a member to itself."
        }
        if (-not $memberMap.Contains($sourceId) -or -not $memberMap.Contains($targetId)) {
            throw "Structural interpretation relation '$id' references an unknown member endpoint."
        }
        if (
            $memberMap[$sourceId].interpretation_id -cne $interpretationId -or
            $memberMap[$targetId].interpretation_id -cne $interpretationId
        ) {
            throw "Structural interpretation relation '$id' endpoints must belong to '$interpretationId'."
        }
        $typeId = Get-RequiredInterpretationString $item 'relationship_type' $context
        if (-not $relationTypes.Contains($typeId)) {
            throw "$context.relationship_type references unknown relation type '$typeId'."
        }
        $relation = [pscustomobject]@{
            id = $id
            interpretation_id = $interpretationId
            source_member_id = $sourceId
            relationship_type = $typeId
            target_member_id = $targetId
        }
        $shape = Get-CanonicalInterpretationRelationShape $relation $relationTypes
        if (-not $semanticRelations.Add($shape)) {
            throw "Structural interpretation relation '$id' duplicates a relation or its inverse."
        }
        $relations += $relation
    }
    Assert-InterpretationRelationsAcyclic $relations $relationTypes

    $comparisonSets = @{}
    $semanticSets = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawSets = Get-ProjectMapValue $root 'comparison_sets'
    Assert-InterpretationMap $rawSets 'comparison_sets'
    foreach ($id in $rawSets.Keys) {
        Assert-InterpretationStableId $id "comparison_sets.$id"
        $context = "comparison_sets.$id"
        $item = $rawSets[$id]
        Assert-InterpretationMap $item $context
        Assert-KnowledgeMapKeys `
            $item `
        @('label', 'comparison_mode', 'interpretation_ids') `
            "Structural interpretation registry '$context'"
        $mode = Get-RequiredInterpretationString $item 'comparison_mode' $context
        Assert-InterpretationPackValue `
            $SchemaPackRegistry `
            'interpretation.comparison-mode' `
            $mode `
            "$context.comparison_mode"
        $interpretationIds = @(Get-InterpretationStringList $item 'interpretation_ids' $context)
        if ($interpretationIds.Count -lt 2) {
            throw "Structural interpretation comparison set '$id' requires at least two interpretations."
        }
        $uniqueIds = @($interpretationIds | Sort-Object -Unique)
        if ($uniqueIds.Count -ne $interpretationIds.Count) {
            throw "Structural interpretation comparison set '$id' repeats an interpretation."
        }
        $unknown = @($interpretationIds | Where-Object { -not $interpretations.Contains($_) })
        if ($unknown.Count -gt 0) {
            throw "Structural interpretation comparison set '$id' references unknown interpretations: $($unknown -join ', ')."
        }
        $shape = "$mode|$(@($interpretationIds | Sort-Object) -join ',')"
        if (-not $semanticSets.Add($shape)) {
            throw "Structural interpretation comparison set '$id' duplicates another set."
        }
        $comparisonSets[$id] = [pscustomobject]@{
            id = $id
            label = Get-RequiredInterpretationString $item 'label' $context
            comparison_mode = $mode
            interpretation_ids = @($interpretationIds)
        }
    }

    return [pscustomobject]@{
        path = $path
        schema_version = $script:SupportedInterpretationSchemaVersion
        relation_types = $relationTypes
        interpretations = $interpretations
        members = @($members)
        relations = @($relations)
        comparison_sets = $comparisonSets
    }
}

function Get-KnowledgeInterpretationMembers {
    param([object]$Registry, [string]$InterpretationId)

    if (-not $Registry.interpretations.Contains($InterpretationId)) {
        throw "Unknown structural interpretation '$InterpretationId'."
    }
    return @($Registry.members | Where-Object { $_.interpretation_id -ceq $InterpretationId })
}

function Get-KnowledgeInterpretationRelations {
    param([object]$Registry, [string]$InterpretationId)

    if (-not $Registry.interpretations.Contains($InterpretationId)) {
        throw "Unknown structural interpretation '$InterpretationId'."
    }
    return @($Registry.relations | Where-Object { $_.interpretation_id -ceq $InterpretationId })
}

function Get-KnowledgeInterpretationComparisonSets {
    param([object]$Registry, [string]$InterpretationId)

    if (-not $Registry.interpretations.Contains($InterpretationId)) {
        throw "Unknown structural interpretation '$InterpretationId'."
    }
    return @(
        $Registry.comparison_sets.Values |
            Where-Object { @($_.interpretation_ids) -ccontains $InterpretationId } |
            Sort-Object -Property id
    )
}

function Get-KnowledgeInterpretationStructure {
    param([object]$Registry, [string]$InterpretationId)

    if (-not $Registry.interpretations.Contains($InterpretationId)) {
        throw "Unknown structural interpretation '$InterpretationId'."
    }
    return [pscustomobject]@{
        interpretation = $Registry.interpretations[$InterpretationId]
        members = @(Get-KnowledgeInterpretationMembers $Registry $InterpretationId)
        relations = @(Get-KnowledgeInterpretationRelations $Registry $InterpretationId)
    }
}

function Get-KnowledgeInterpretationSetDecision {
    param([object]$Registry, [string]$SetId)

    if (-not $Registry.comparison_sets.Contains($SetId)) {
        throw "Unknown structural interpretation set '$SetId'."
    }
    $set = $Registry.comparison_sets[$SetId]
    $compatible = $set.comparison_mode -ceq 'compatible'
    return [pscustomobject]@{
        set_id = $SetId
        comparison_mode = $set.comparison_mode
        disposition = if ($compatible) {
            'compatible'
        }
        else {
            'unresolved'
        }
        candidate_interpretation_ids = @($set.interpretation_ids)
        selected_interpretation_ids = @()
        reason = if ($compatible) {
            'Compatible interpretations may coexist; structural membership does not select or endorse them.'
        }
        else {
            'Evidence and authority resolution remain provenance-owned.'
        }
    }
}

function Get-KnowledgeInterpretationProvenanceTargets {
    param([object]$Registry)

    $members = @{}
    foreach ($item in $Registry.members) {
        $members[$item.id] = $item
    }
    $relations = @{}
    foreach ($item in $Registry.relations) {
        $relations[$item.id] = $item
    }
    return @{
        'structural-interpretation' = $Registry.interpretations
        'structural-interpretation-member' = $members
        'structural-interpretation-relation' = $relations
        'structural-interpretation-set' = $Registry.comparison_sets
    }
}

function Get-KnowledgeInterpretationProvenanceTarget {
    param([object]$Registry, [string]$SubjectType, [string]$SubjectId)

    $targets = Get-KnowledgeInterpretationProvenanceTargets $Registry
    if (-not $targets.Contains($SubjectType)) {
        throw "Unsupported structural interpretation provenance subject type '$SubjectType'."
    }
    if (-not $targets[$SubjectType].Contains($SubjectId)) {
        throw "Unknown $SubjectType '$SubjectId'."
    }
    return $targets[$SubjectType][$SubjectId]
}

function Assert-KnowledgeInterpretationClaimTargets {
    param([object]$Registry, [string[]]$ClaimKeys)

    $known = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($claimKey in @($ClaimKeys)) {
        $null = $known.Add($claimKey)
    }
    foreach ($member in $Registry.members) {
        if ($member.target_type -ceq 'provenance-claim' -and -not $known.Contains($member.target_id)) {
            throw "Structural interpretation member '$($member.id)' references unknown provenance claim '$($member.target_id)'."
        }
    }
}
