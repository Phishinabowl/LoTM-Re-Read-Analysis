$script:SupportedHostingSchemaVersion = 2

function Assert-HostingStableId {
    param([string]$Value, [string]$Context)

    if ($Value -cnotmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
        throw "Hosted identity registry '$Context' must be a lowercase kebab-case stable ID: $Value"
    }
}

function Get-RequiredHostingString {
    param([object]$Mapping, [string]$Key, [string]$Context)

    if (-not $Mapping.Contains($Key) -or $Mapping[$Key] -isnot [string] -or [string]::IsNullOrWhiteSpace($Mapping[$Key])) {
        throw "Hosted identity registry '$Context.$Key' must be a non-empty string."
    }
    return $Mapping[$Key].Trim()
}

function Get-OptionalHostingString {
    param([object]$Mapping, [string]$Key, [string]$Context)

    if (-not $Mapping.Contains($Key) -or $null -eq $Mapping[$Key]) {
        return $null
    }
    return Get-RequiredHostingString $Mapping $Key $Context
}

function Assert-HostingPackValue {
    param([object]$Packs, [string]$Namespace, [string]$Value, [string]$Context)

    $allowed = @(Get-SchemaPackAllowedValues $Packs $Namespace)
    if ($allowed -cnotcontains $Value) {
        throw "Hosted identity registry '$Context' value '$Value' is not allowed by '$Namespace'."
    }
}

function New-KnowledgeHostingIdentityProvider {
    param(
        [string]$ProviderId,
        [object]$IdentityTargets,
        [object]$ProvenanceTargets
    )

    return [pscustomobject]@{
        provider_id = $ProviderId
        identity_targets = $IdentityTargets
        provenance_targets = $ProvenanceTargets
    }
}

function New-KnowledgeHostingEntityProvider {
    param([object]$Registry)

    $entityRelationships = @{}
    foreach ($item in @($Registry.entity_relationships)) {
        $entityRelationships[$item.id] = $item
    }
    $incarnationRelationships = @{}
    foreach ($item in @($Registry.incarnation_relationships)) {
        $incarnationRelationships[$item.id] = $item
    }
    $phaseRelationships = @{}
    foreach ($item in @($Registry.identity_phase_relationships)) {
        $phaseRelationships[$item.id] = $item
    }
    return New-KnowledgeHostingIdentityProvider `
        'entity' `
    ([ordered]@{
            entity = $Registry.entities
            'entity-incarnation' = $Registry.incarnations
            'identity-phase' = $Registry.identity_phases
        }) `
    ([ordered]@{
            'entity-relationship' = $entityRelationships
            'incarnation-relationship' = $incarnationRelationships
            'identity-phase-relationship' = $phaseRelationships
        })
}

function Get-HostingProviderMaps {
    param([object[]]$Providers, [string]$Property, [string]$Label)

    $result = @{}
    foreach ($provider in $Providers) {
        $targets = $provider.$Property
        if ($null -eq $targets -or $targets -isnot [System.Collections.IDictionary]) {
            throw "Hosted identity $Label provider does not expose $Property."
        }
        foreach ($targetType in $targets.Keys) {
            if ($result.Contains($targetType)) {
                throw "Hosted identity $Label type '$targetType' has multiple providers."
            }
            $result[$targetType] = $targets[$targetType]
        }
    }
    return $result
}

function Get-HostingEntryIndex {
    param(
        [object]$Occurrences,
        [string]$TrackId,
        [string]$EntryId,
        [string]$Context
    )

    if (-not $Occurrences.tracks.Contains($TrackId)) {
        throw "$Context references unknown lifecycle track '$TrackId'."
    }
    if (-not $Occurrences.track_entries.Contains($EntryId)) {
        throw "$Context references unknown track entry '$EntryId'."
    }
    $entry = $Occurrences.track_entries[$EntryId]
    if ($entry.track_id -cne $TrackId) {
        throw "$Context track entry '$EntryId' does not belong to '$TrackId'."
    }
    return [array]::IndexOf(@($Occurrences.tracks[$TrackId].entry_ids), $EntryId)
}

function Get-HostingEntryOccurrenceId {
    param([object]$Occurrences, [string]$EntryId)

    $entry = $Occurrences.track_entries[$EntryId]
    return $Occurrences.occurrence_participations[$entry.participation_id].occurrence_id
}

function Assert-HostingBindingAcyclic {
    param([object]$Bindings)

    $parents = [ordered]@{}
    foreach ($binding in $Bindings.Values) {
        if (-not $parents.Contains($binding.child_carrier_id)) {
            $parents[$binding.child_carrier_id] = New-Object System.Collections.ArrayList
        }
        [void]$parents[$binding.child_carrier_id].Add($binding.parent_carrier_id)
    }
    foreach ($binding in $Bindings.Values) {
        $pending = New-Object System.Collections.Stack
        $pending.Push($binding.parent_carrier_id)
        $visited = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        while ($pending.Count -gt 0) {
            $current = [string]$pending.Pop()
            if ($current -ceq $binding.child_carrier_id) {
                throw "Host carrier bindings contain a cycle through '$current'."
            }
            if (-not $visited.Add($current) -or -not $parents.Contains($current)) {
                continue
            }
            foreach ($parentId in @($parents[$current])) {
                $pending.Push($parentId)
            }
        }
    }
}

function Get-KnowledgeHostedIdentityRegistry {
    param(
        [object]$Project,
        [object]$Packs,
        [object]$Occurrences,
        [object[]]$IdentityProviders
    )

    $root = ConvertFrom-KnowledgeYamlFile `
        $Project.hosting_registry `
        $script:SupportedHostingSchemaVersion `
        'hosted identity registry'
    Assert-KnowledgeMapKeys `
        $root `
    @('schema_version', 'carriers', 'bindings', 'occupancies', 'transitions') `
        'Hosted identity registry root'

    $registered = Test-SchemaPackCapabilityAvailable $Packs 'hosted-identity-embodiment'
    $enabled = Test-SchemaPackCapabilityEnabled $Packs 'hosted-identity-embodiment'
    if (-not $enabled) {
        $hasRecords = @($root.carriers.Keys).Count -gt 0 -or
        @($root.bindings).Count -gt 0 -or
        @($root.occupancies).Count -gt 0 -or
        @($root.transitions).Count -gt 0
        if ($hasRecords) {
            throw "Hosted identity records require enabled capability 'hosted-identity-embodiment'."
        }
        return [pscustomobject]@{
            path = $Project.hosting_registry
            schema_version = $script:SupportedHostingSchemaVersion
            registered = $registered
            enabled = $false
            carriers = [ordered]@{}
            occupancies = [ordered]@{}
            transitions = [ordered]@{}
            bindings = [ordered]@{}
            occurrences = $Occurrences
        }
    }

    $identityTargets = Get-HostingProviderMaps $IdentityProviders 'identity_targets' 'identity-target'
    $provenanceTargets = Get-HostingProviderMaps $IdentityProviders 'provenance_targets' 'relationship-target'

    $carriers = [ordered]@{}
    foreach ($carrierId in $root.carriers.Keys) {
        Assert-HostingStableId $carrierId "carriers.$carrierId"
        $context = "carriers.$carrierId"
        $item = $root.carriers[$carrierId]
        Assert-KnowledgeMapKeys `
            $item `
        @(
            'lifecycle'
            'carrier_kind'
            'label'
            'lifecycle_track_id'
            'activated_at_entry_id'
            'terminated_at_entry_id'
        ) `
            "Hosted identity registry '$context'"
        $lifecycle = Get-RequiredHostingString $item 'lifecycle' $context
        $carrierKind = Get-RequiredHostingString $item 'carrier_kind' $context
        Assert-HostingPackValue $Packs 'hosting.record-lifecycle' $lifecycle "$context.lifecycle"
        Assert-HostingPackValue $Packs 'hosting.carrier-kind' $carrierKind "$context.carrier_kind"
        $trackId = Get-RequiredHostingString $item 'lifecycle_track_id' $context
        $activatedId = Get-RequiredHostingString $item 'activated_at_entry_id' $context
        $terminatedId = Get-OptionalHostingString $item 'terminated_at_entry_id' $context
        $activated = Get-HostingEntryIndex $Occurrences $trackId $activatedId $context
        if ($null -ne $terminatedId) {
            $terminated = Get-HostingEntryIndex $Occurrences $trackId $terminatedId $context
            if ($terminated -le $activated) {
                throw "$context.terminated_at_entry_id must follow activation on the lifecycle track."
            }
        }
        $carriers[$carrierId] = [pscustomobject]@{
            id = $carrierId
            lifecycle = $lifecycle
            carrier_kind = $carrierKind
            label = Get-RequiredHostingString $item 'label' $context
            lifecycle_track_id = $trackId
            activated_at_entry_id = $activatedId
            terminated_at_entry_id = $terminatedId
        }
    }

    $bindings = [ordered]@{}
    $semanticBindings = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt @($root.bindings).Count; $index += 1) {
        $context = "bindings[$index]"
        $item = @($root.bindings)[$index]
        Assert-KnowledgeMapKeys `
            $item `
        @(
            'id'
            'child_carrier_id'
            'parent_carrier_id'
            'binding_kind'
            'child_activated_at_entry_id'
            'parent_activated_at_entry_id'
            'child_terminated_at_entry_id'
            'parent_terminated_at_entry_id'
        ) `
            "Hosted identity registry '$context'"
        $bindingId = Get-RequiredHostingString $item 'id' $context
        Assert-HostingStableId $bindingId "$context.id"
        if ($bindings.Contains($bindingId)) {
            throw "Host carrier binding ID '$bindingId' is duplicated."
        }
        $childId = Get-RequiredHostingString $item 'child_carrier_id' $context
        $parentId = Get-RequiredHostingString $item 'parent_carrier_id' $context
        if (
            $childId -ceq $parentId -or
            -not $carriers.Contains($childId) -or
            -not $carriers.Contains($parentId)
        ) {
            throw "$context must reference two distinct known carrier endpoints."
        }
        $kind = Get-RequiredHostingString $item 'binding_kind' $context
        Assert-HostingPackValue $Packs 'hosting.binding-kind' $kind "$context.binding_kind"
        $child = $carriers[$childId]
        $parent = $carriers[$parentId]
        $childActivatedId = Get-RequiredHostingString $item 'child_activated_at_entry_id' $context
        $parentActivatedId = Get-RequiredHostingString $item 'parent_activated_at_entry_id' $context
        $childTerminatedId = Get-OptionalHostingString $item 'child_terminated_at_entry_id' $context
        $parentTerminatedId = Get-OptionalHostingString $item 'parent_terminated_at_entry_id' $context
        if (($null -eq $childTerminatedId) -ne ($null -eq $parentTerminatedId)) {
            throw "$context child and parent termination boundaries must be supplied together."
        }
        $childActivated = Get-HostingEntryIndex `
            $Occurrences `
            $child.lifecycle_track_id `
            $childActivatedId `
            "$context.child_activated_at_entry_id"
        $parentActivated = Get-HostingEntryIndex `
            $Occurrences `
            $parent.lifecycle_track_id `
            $parentActivatedId `
            "$context.parent_activated_at_entry_id"
        $childTerminated = if ($null -ne $childTerminatedId) {
            Get-HostingEntryIndex `
                $Occurrences `
                $child.lifecycle_track_id `
                $childTerminatedId `
                "$context.child_terminated_at_entry_id"
        }
        else {
            $null
        }
        $parentTerminated = if ($null -ne $parentTerminatedId) {
            Get-HostingEntryIndex `
                $Occurrences `
                $parent.lifecycle_track_id `
                $parentTerminatedId `
                "$context.parent_terminated_at_entry_id"
        }
        else {
            $null
        }
        $childActivationOccurrence = Get-HostingEntryOccurrenceId $Occurrences $childActivatedId
        $parentActivationOccurrence = Get-HostingEntryOccurrenceId $Occurrences $parentActivatedId
        if ($childActivationOccurrence -cne $parentActivationOccurrence) {
            throw "$context activation boundaries must resolve to one occurrence."
        }
        if ($null -ne $childTerminatedId) {
            $childTerminationOccurrence = Get-HostingEntryOccurrenceId $Occurrences $childTerminatedId
            $parentTerminationOccurrence = Get-HostingEntryOccurrenceId $Occurrences $parentTerminatedId
            if ($childTerminationOccurrence -cne $parentTerminationOccurrence) {
                throw "$context termination boundaries must resolve to one occurrence."
            }
        }
        if ($null -ne $childTerminated -and $childTerminated -le $childActivated) {
            throw "$context child termination must follow activation."
        }
        if ($null -ne $parentTerminated -and $parentTerminated -le $parentActivated) {
            throw "$context parent termination must follow activation."
        }
        foreach ($boundary in @(
                [pscustomobject]@{ carrier = $child
                    activated = $childActivated
                    terminated = $childTerminated
                }
                [pscustomobject]@{ carrier = $parent
                    activated = $parentActivated
                    terminated = $parentTerminated
                }
            )) {
            $carrierStart = Get-HostingEntryIndex `
                $Occurrences `
                $boundary.carrier.lifecycle_track_id `
                $boundary.carrier.activated_at_entry_id `
                "carriers.$($boundary.carrier.id)"
            $carrierEnd = if ($null -ne $boundary.carrier.terminated_at_entry_id) {
                Get-HostingEntryIndex `
                    $Occurrences `
                    $boundary.carrier.lifecycle_track_id `
                    $boundary.carrier.terminated_at_entry_id `
                    "carriers.$($boundary.carrier.id)"
            }
            else {
                $null
            }
            if (
                $boundary.activated -lt $carrierStart -or
                ($null -ne $carrierEnd -and $boundary.activated -ge $carrierEnd)
            ) {
                throw "$context activates outside carrier '$($boundary.carrier.id)' lifecycle."
            }
            if (
                $null -ne $carrierEnd -and
                ($null -eq $boundary.terminated -or $boundary.terminated -gt $carrierEnd)
            ) {
                throw "$context extends beyond carrier '$($boundary.carrier.id)' lifecycle."
            }
        }
        $shape = @(
            $childId
            $parentId
            $kind
            $childActivated
            $parentActivated
            $childTerminated
            $parentTerminated
        ) -join "`0"
        if (-not $semanticBindings.Add($shape)) {
            throw "Host carrier binding '$bindingId' duplicates another binding."
        }
        $bindings[$bindingId] = [pscustomobject]@{
            id = $bindingId
            child_carrier_id = $childId
            parent_carrier_id = $parentId
            binding_kind = $kind
            child_activated_at_entry_id = $childActivatedId
            parent_activated_at_entry_id = $parentActivatedId
            child_terminated_at_entry_id = $childTerminatedId
            parent_terminated_at_entry_id = $parentTerminatedId
        }
    }
    Assert-HostingBindingAcyclic $bindings

    $occupancies = [ordered]@{}
    $semanticOccupancies = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt @($root.occupancies).Count; $index += 1) {
        $context = "occupancies[$index]"
        $item = @($root.occupancies)[$index]
        Assert-KnowledgeMapKeys `
            $item `
        @(
            'id'
            'subject_type'
            'subject_id'
            'carrier_id'
            'role'
            'activated_at_entry_id'
            'terminated_at_entry_id'
        ) `
            "Hosted identity registry '$context'"
        $occupancyId = Get-RequiredHostingString $item 'id' $context
        Assert-HostingStableId $occupancyId "$context.id"
        if ($occupancies.Contains($occupancyId)) {
            throw "Hosted identity occupancy ID '$occupancyId' is duplicated."
        }
        $subjectType = Get-RequiredHostingString $item 'subject_type' $context
        $subjectId = Get-RequiredHostingString $item 'subject_id' $context
        if (-not $identityTargets.Contains($subjectType)) {
            throw "$context.subject_type references unsupported identity type '$subjectType'."
        }
        if (-not $identityTargets[$subjectType].Contains($subjectId)) {
            throw "$context.subject_id references unknown $subjectType '$subjectId'."
        }
        $carrierId = Get-RequiredHostingString $item 'carrier_id' $context
        if (-not $carriers.Contains($carrierId)) {
            throw "$context.carrier_id references unknown carrier '$carrierId'."
        }
        $carrier = $carriers[$carrierId]
        $role = Get-RequiredHostingString $item 'role' $context
        Assert-HostingPackValue $Packs 'hosting.occupancy-role' $role "$context.role"
        $activatedId = Get-RequiredHostingString $item 'activated_at_entry_id' $context
        $terminatedId = Get-OptionalHostingString $item 'terminated_at_entry_id' $context
        $activated = Get-HostingEntryIndex $Occurrences $carrier.lifecycle_track_id $activatedId $context
        $terminated = if ($null -ne $terminatedId) {
            Get-HostingEntryIndex $Occurrences $carrier.lifecycle_track_id $terminatedId $context
        }
        else {
            $null
        }
        $carrierStart = Get-HostingEntryIndex `
            $Occurrences `
            $carrier.lifecycle_track_id `
            $carrier.activated_at_entry_id `
            "carriers.$carrierId"
        $carrierEnd = if ($null -ne $carrier.terminated_at_entry_id) {
            Get-HostingEntryIndex `
                $Occurrences `
                $carrier.lifecycle_track_id `
                $carrier.terminated_at_entry_id `
                "carriers.$carrierId"
        }
        else {
            $null
        }
        if ($activated -lt $carrierStart -or ($null -ne $carrierEnd -and $activated -ge $carrierEnd)) {
            throw "$context activates outside carrier '$carrierId' lifecycle."
        }
        if ($null -ne $terminated -and $terminated -le $activated) {
            throw "$context.terminated_at_entry_id must follow activation."
        }
        if ($null -ne $carrierEnd -and ($null -eq $terminated -or $terminated -gt $carrierEnd)) {
            throw "$context extends beyond carrier '$carrierId' lifecycle."
        }
        $shape = "$subjectType`0$subjectId`0$carrierId`0$role`0$activated`0$terminated"
        if (-not $semanticOccupancies.Add($shape)) {
            throw "Hosted identity occupancy '$occupancyId' duplicates another occupancy."
        }
        $occupancies[$occupancyId] = [pscustomobject]@{
            id = $occupancyId
            subject_type = $subjectType
            subject_id = $subjectId
            carrier_id = $carrierId
            role = $role
            activated_at_entry_id = $activatedId
            terminated_at_entry_id = $terminatedId
        }
    }

    $transitions = [ordered]@{}
    $semanticTransitions = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt @($root.transitions).Count; $index += 1) {
        $context = "transitions[$index]"
        $item = @($root.transitions)[$index]
        Assert-KnowledgeMapKeys `
            $item `
        @(
            'id'
            'transition_kind'
            'source_occupancy_id'
            'target_occupancy_id'
            'occurrence_id'
            'source_entry_id'
            'target_entry_id'
            'identity_relationship_type'
            'identity_relationship_id'
        ) `
            "Hosted identity registry '$context'"
        $transitionId = Get-RequiredHostingString $item 'id' $context
        Assert-HostingStableId $transitionId "$context.id"
        if ($transitions.Contains($transitionId)) {
            throw "Hosted identity transition ID '$transitionId' is duplicated."
        }
        $kind = Get-RequiredHostingString $item 'transition_kind' $context
        Assert-HostingPackValue $Packs 'hosting.transition-kind' $kind "$context.transition_kind"
        $sourceId = Get-RequiredHostingString $item 'source_occupancy_id' $context
        $targetId = Get-RequiredHostingString $item 'target_occupancy_id' $context
        if ($sourceId -ceq $targetId -or -not $occupancies.Contains($sourceId) -or -not $occupancies.Contains($targetId)) {
            throw "$context must reference two distinct known occupancy endpoints."
        }
        $source = $occupancies[$sourceId]
        $target = $occupancies[$targetId]
        $occurrenceId = Get-RequiredHostingString $item 'occurrence_id' $context
        if (-not $Occurrences.occurrences.Contains($occurrenceId)) {
            throw "$context.occurrence_id references unknown occurrence '$occurrenceId'."
        }
        $sourceEntryId = Get-RequiredHostingString $item 'source_entry_id' $context
        $targetEntryId = Get-RequiredHostingString $item 'target_entry_id' $context
        $sourceCarrier = $carriers[$source.carrier_id]
        $targetCarrier = $carriers[$target.carrier_id]
        [void](Get-HostingEntryIndex $Occurrences $sourceCarrier.lifecycle_track_id $sourceEntryId $context)
        [void](Get-HostingEntryIndex $Occurrences $targetCarrier.lifecycle_track_id $targetEntryId $context)
        $sourceEntry = $Occurrences.track_entries[$sourceEntryId]
        $targetEntry = $Occurrences.track_entries[$targetEntryId]
        $sourceOccurrence = $Occurrences.occurrence_participations[$sourceEntry.participation_id].occurrence_id
        $targetOccurrence = $Occurrences.occurrence_participations[$targetEntry.participation_id].occurrence_id
        if ($sourceOccurrence -cne $occurrenceId -or $targetOccurrence -cne $occurrenceId) {
            throw "$context boundary entries must resolve to occurrence '$occurrenceId'."
        }
        if ($target.activated_at_entry_id -cne $targetEntryId) {
            throw "$context.target_entry_id must activate the target occupancy."
        }
        $relationshipType = Get-OptionalHostingString $item 'identity_relationship_type' $context
        $relationshipId = Get-OptionalHostingString $item 'identity_relationship_id' $context
        if (($null -eq $relationshipType) -ne ($null -eq $relationshipId)) {
            throw "$context identity relationship type and ID must be supplied together."
        }
        $sameSubject = (
            $source.subject_type -ceq $target.subject_type -and
            $source.subject_id -ceq $target.subject_id
        )
        switch ($kind) {
            'move' {
                if (
                    -not $sameSubject -or
                    $source.carrier_id -ceq $target.carrier_id -or
                    $null -ne $relationshipType -or
                    $source.terminated_at_entry_id -cne $sourceEntryId
                ) {
                    throw "$context move requires one unchanged subject crossing distinct carriers."
                }
            }
            'copy' {
                if ($sameSubject -or $source.carrier_id -ceq $target.carrier_id -or $null -eq $relationshipType) {
                    throw "$context copy requires distinct subjects, carriers, and an identity relationship."
                }
                Assert-HostingPackValue `
                    $Packs `
                    'hosting.identity-relationship-target-type' `
                    $relationshipType `
                    "$context.identity_relationship_type"
                if (
                    -not $provenanceTargets.Contains($relationshipType) -or
                    -not $provenanceTargets[$relationshipType].Contains($relationshipId)
                ) {
                    throw "$context references unknown identity relationship '$relationshipType`:$relationshipId'."
                }
                $sourceActivated = Get-HostingEntryIndex `
                    $Occurrences `
                    $sourceCarrier.lifecycle_track_id `
                    $source.activated_at_entry_id `
                    $context
                $sourceTerminated = if ($null -ne $source.terminated_at_entry_id) {
                    Get-HostingEntryIndex `
                        $Occurrences `
                        $sourceCarrier.lifecycle_track_id `
                        $source.terminated_at_entry_id `
                        $context
                }
                else {
                    $null
                }
                $sourceBoundary = Get-HostingEntryIndex `
                    $Occurrences `
                    $sourceCarrier.lifecycle_track_id `
                    $sourceEntryId `
                    $context
                if (
                    $sourceBoundary -lt $sourceActivated -or
                    ($null -ne $sourceTerminated -and $sourceBoundary -ge $sourceTerminated)
                ) {
                    throw "$context copy source is not active at its boundary entry."
                }
            }
            'control-handoff' {
                if (
                    $source.carrier_id -cne $target.carrier_id -or
                    $source.role -cne 'controlling' -or
                    $target.role -cne 'controlling' -or
                    $sameSubject -or
                    $null -ne $relationshipType -or
                    $source.terminated_at_entry_id -cne $sourceEntryId
                ) {
                    throw "$context control handoff requires distinct controlling subjects on one carrier."
                }
            }
            default {
                throw "Unsupported hosted identity transition kind '$kind'."
            }
        }
        $shape = "$kind`0$sourceId`0$targetId`0$occurrenceId"
        if (-not $semanticTransitions.Add($shape)) {
            throw "Hosted identity transition '$transitionId' duplicates another transition."
        }
        $transitions[$transitionId] = [pscustomobject]@{
            id = $transitionId
            transition_kind = $kind
            source_occupancy_id = $sourceId
            target_occupancy_id = $targetId
            occurrence_id = $occurrenceId
            source_entry_id = $sourceEntryId
            target_entry_id = $targetEntryId
            identity_relationship_type = $relationshipType
            identity_relationship_id = $relationshipId
        }
    }

    return [pscustomobject]@{
        path = $Project.hosting_registry
        schema_version = $script:SupportedHostingSchemaVersion
        registered = $true
        enabled = $true
        carriers = $carriers
        occupancies = $occupancies
        transitions = $transitions
        bindings = $bindings
        occurrences = $Occurrences
    }
}

function Get-KnowledgeHostCarrierOccupancies {
    param([object]$Registry, [string]$CarrierId)

    if (-not $Registry.carriers.Contains($CarrierId)) {
        throw "Unknown host carrier '$CarrierId'."
    }
    return @($Registry.occupancies.Values | Where-Object { $_.carrier_id -ceq $CarrierId })
}

function Get-KnowledgeHostedIdentityOccupancies {
    param([object]$Registry, [string]$SubjectType, [string]$SubjectId)

    $matches = @(
        $Registry.occupancies.Values |
            Where-Object { $_.subject_type -ceq $SubjectType -and $_.subject_id -ceq $SubjectId }
    )
    if ($matches.Count -eq 0) {
        throw "Unknown hosted identity subject '$SubjectType`:$SubjectId'."
    }
    return $matches
}

function Test-KnowledgeHostCarrierActiveAt {
    param([object]$Registry, [string]$CarrierId, [string]$EntryId)

    if (-not $Registry.carriers.Contains($CarrierId)) {
        throw "Unknown host carrier '$CarrierId'."
    }
    $carrier = $Registry.carriers[$CarrierId]
    $boundary = Get-HostingEntryIndex $Registry.occurrences $carrier.lifecycle_track_id $EntryId 'carrier query'
    $activated = Get-HostingEntryIndex `
        $Registry.occurrences `
        $carrier.lifecycle_track_id `
        $carrier.activated_at_entry_id `
        'carrier query'
    if ($boundary -lt $activated) {
        return $false
    }
    if ($null -eq $carrier.terminated_at_entry_id) {
        return $true
    }
    $terminated = Get-HostingEntryIndex `
        $Registry.occurrences `
        $carrier.lifecycle_track_id `
        $carrier.terminated_at_entry_id `
        'carrier query'
    return $boundary -lt $terminated
}

function Get-KnowledgeHostCarrierOccupanciesAt {
    param([object]$Registry, [string]$CarrierId, [string]$EntryId)

    if (-not (Test-KnowledgeHostCarrierActiveAt $Registry $CarrierId $EntryId)) {
        return @()
    }
    $carrier = $Registry.carriers[$CarrierId]
    $boundary = Get-HostingEntryIndex $Registry.occurrences $carrier.lifecycle_track_id $EntryId 'occupancy query'
    return @(
        Get-KnowledgeHostCarrierOccupancies $Registry $CarrierId |
            Where-Object {
                $activated = Get-HostingEntryIndex `
                    $Registry.occurrences `
                    $carrier.lifecycle_track_id `
                    $_.activated_at_entry_id `
                    'occupancy query'
                $terminated = if ($null -ne $_.terminated_at_entry_id) {
                    Get-HostingEntryIndex `
                        $Registry.occurrences `
                        $carrier.lifecycle_track_id `
                        $_.terminated_at_entry_id `
                        'occupancy query'
                }
                else {
                    $null
                }
                $activated -le $boundary -and ($null -eq $terminated -or $boundary -lt $terminated)
            } |
            Sort-Object id
    )
}

function Get-KnowledgeHostCarrierControllersAt {
    param([object]$Registry, [string]$CarrierId, [string]$EntryId)

    return @(
        Get-KnowledgeHostCarrierOccupanciesAt $Registry $CarrierId $EntryId |
            Where-Object { $_.role -ceq 'controlling' }
    )
}

function Get-KnowledgeHostCarrierBindingsForChild {
    param([object]$Registry, [string]$CarrierId)

    if (-not $Registry.carriers.Contains($CarrierId)) {
        throw "Unknown host carrier '$CarrierId'."
    }
    return @($Registry.bindings.Values | Where-Object { $_.child_carrier_id -ceq $CarrierId })
}

function Get-KnowledgeHostCarrierBindingsForParent {
    param([object]$Registry, [string]$CarrierId)

    if (-not $Registry.carriers.Contains($CarrierId)) {
        throw "Unknown host carrier '$CarrierId'."
    }
    return @($Registry.bindings.Values | Where-Object { $_.parent_carrier_id -ceq $CarrierId })
}

function Get-HostingBoundaryEntry {
    param([object]$Registry, [object]$BoundaryEntries, [string]$TrackId)

    if ($BoundaryEntries -isnot [System.Collections.IDictionary] -or -not $BoundaryEntries.Contains($TrackId)) {
        throw "Host carrier boundary entries are missing lifecycle track '$TrackId'."
    }
    $entryId = $BoundaryEntries[$TrackId]
    if ($entryId -isnot [string] -or [string]::IsNullOrWhiteSpace($entryId)) {
        throw "Host carrier boundary entry for lifecycle track '$TrackId' must be a non-empty string."
    }
    [void](Get-HostingEntryIndex $Registry.occurrences $TrackId $entryId 'carrier binding query')
    return $entryId
}

function Test-KnowledgeHostCarrierBindingActiveAt {
    param([object]$Registry, [string]$BindingId, [object]$BoundaryEntries)

    if (-not $Registry.bindings.Contains($BindingId)) {
        throw "Unknown host carrier binding '$BindingId'."
    }
    $binding = $Registry.bindings[$BindingId]
    foreach ($side in @('child', 'parent')) {
        $carrierId = $binding."${side}_carrier_id"
        $carrier = $Registry.carriers[$carrierId]
        $entryId = Get-HostingBoundaryEntry $Registry $BoundaryEntries $carrier.lifecycle_track_id
        $boundary = Get-HostingEntryIndex `
            $Registry.occurrences `
            $carrier.lifecycle_track_id `
            $entryId `
            'carrier binding query'
        $activated = Get-HostingEntryIndex `
            $Registry.occurrences `
            $carrier.lifecycle_track_id `
            $binding."${side}_activated_at_entry_id" `
            'carrier binding query'
        $terminatedId = $binding."${side}_terminated_at_entry_id"
        $terminated = if ($null -ne $terminatedId) {
            Get-HostingEntryIndex `
                $Registry.occurrences `
                $carrier.lifecycle_track_id `
                $terminatedId `
                'carrier binding query'
        }
        else {
            $null
        }
        if ($boundary -lt $activated -or ($null -ne $terminated -and $boundary -ge $terminated)) {
            return $false
        }
    }
    return $true
}

function Get-KnowledgeHostCarrierParentsAt {
    param([object]$Registry, [string]$CarrierId, [object]$BoundaryEntries)

    return @(
        Get-KnowledgeHostCarrierBindingsForChild $Registry $CarrierId |
            Where-Object { Test-KnowledgeHostCarrierBindingActiveAt $Registry $_.id $BoundaryEntries }
    )
}

function Get-KnowledgeHostCarrierChildrenAt {
    param([object]$Registry, [string]$CarrierId, [object]$BoundaryEntries)

    return @(
        Get-KnowledgeHostCarrierBindingsForParent $Registry $CarrierId |
            Where-Object { Test-KnowledgeHostCarrierBindingActiveAt $Registry $_.id $BoundaryEntries }
    )
}

function Get-HostingCarrierPathsAt {
    param(
        [object]$Registry,
        [string]$CarrierId,
        [object]$BoundaryEntries,
        [ValidateSet('parent', 'child')][string]$Direction
    )

    if (-not $Registry.carriers.Contains($CarrierId)) {
        throw "Unknown host carrier '$CarrierId'."
    }
    $pending = New-Object System.Collections.Queue
    $pending.Enqueue([pscustomobject]@{ carrier_id = $CarrierId
            binding_ids = @()
        })
    $result = New-Object System.Collections.ArrayList
    while ($pending.Count -gt 0) {
        $current = $pending.Dequeue()
        $bindings = if ($Direction -ceq 'parent') {
            Get-KnowledgeHostCarrierParentsAt $Registry $current.carrier_id $BoundaryEntries
        }
        else {
            Get-KnowledgeHostCarrierChildrenAt $Registry $current.carrier_id $BoundaryEntries
        }
        foreach ($binding in $bindings) {
            $nextId = if ($Direction -ceq 'parent') {
                $binding.parent_carrier_id
            }
            else {
                $binding.child_carrier_id
            }
            $path = [pscustomobject]@{
                carrier_id = $nextId
                binding_ids = @($current.binding_ids) + @($binding.id)
            }
            [void]$result.Add($path)
            $pending.Enqueue($path)
        }
    }
    return @(
        $result | Sort-Object `
        @{ Expression = { @($_.binding_ids).Count } }, `
            carrier_id, `
        @{ Expression = { @($_.binding_ids) -join "`0" } }
    )
}

function Get-KnowledgeHostCarrierAncestorsAt {
    param([object]$Registry, [string]$CarrierId, [object]$BoundaryEntries)

    return @(Get-HostingCarrierPathsAt $Registry $CarrierId $BoundaryEntries 'parent')
}

function Get-KnowledgeHostCarrierDescendantsAt {
    param([object]$Registry, [string]$CarrierId, [object]$BoundaryEntries)

    return @(Get-HostingCarrierPathsAt $Registry $CarrierId $BoundaryEntries 'child')
}

function Get-KnowledgeHostCarrierReachableOccupanciesAt {
    param([object]$Registry, [string]$CarrierId, [object]$BoundaryEntries)

    if (-not $Registry.carriers.Contains($CarrierId)) {
        throw "Unknown host carrier '$CarrierId'."
    }
    $paths = @(
        [pscustomobject]@{ carrier_id = $CarrierId
            binding_ids = @()
        }
        Get-KnowledgeHostCarrierDescendantsAt $Registry $CarrierId $BoundaryEntries
    )
    $result = New-Object System.Collections.ArrayList
    foreach ($path in $paths) {
        $carrier = $Registry.carriers[$path.carrier_id]
        $entryId = Get-HostingBoundaryEntry $Registry $BoundaryEntries $carrier.lifecycle_track_id
        foreach ($occupancy in @(Get-KnowledgeHostCarrierOccupanciesAt $Registry $path.carrier_id $entryId)) {
            [void]$result.Add([pscustomobject]@{
                    occupancy = $occupancy
                    carrier_path = $path
                })
        }
    }
    return @(
        $result | Sort-Object `
        @{ Expression = { @($_.carrier_path.binding_ids).Count } }, `
        @{ Expression = { @($_.carrier_path.binding_ids) -join "`0" } }, `
        @{ Expression = { $_.occupancy.id } }
    )
}

function Get-KnowledgeHostingProvenanceTargets {
    param([object]$Registry)

    if (-not $Registry.registered) {
        return [ordered]@{}
    }
    return [ordered]@{
        'host-carrier' = $Registry.carriers
        'host-carrier-binding' = $Registry.bindings
        'hosted-identity-occupancy' = $Registry.occupancies
        'hosted-identity-transition' = $Registry.transitions
    }
}

function Get-KnowledgeHostingProvenanceTarget {
    param([object]$Registry, [string]$SubjectType, [string]$SubjectId)

    $targets = Get-KnowledgeHostingProvenanceTargets $Registry
    if (-not $targets.Contains($SubjectType)) {
        throw "Unsupported hosted-identity provenance subject type '$SubjectType'."
    }
    if (-not $targets[$SubjectType].Contains($SubjectId)) {
        throw "Unknown $SubjectType '$SubjectId'."
    }
    return $targets[$SubjectType][$SubjectId]
}

function Get-KnowledgeHostingReconciliationProvider {
    param([object]$Registry)

    if (-not $Registry.registered) {
        return [ordered]@{
            provider_id = 'hosting'
            targets = [ordered]@{}
            aliases = [ordered]@{}
        }
    }
    return [ordered]@{
        provider_id = 'hosting'
        targets = [ordered]@{ 'host-carrier' = $Registry.carriers }
        aliases = [ordered]@{ 'host-carrier' = @{} }
    }
}
