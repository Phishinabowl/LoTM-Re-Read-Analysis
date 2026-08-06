$script:SupportedHostingSchemaVersion = 1

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

function Get-KnowledgeHostedIdentityRegistry {
    param(
        [object]$Project,
        [object]$Packs,
        [object]$Occurrences,
        [object[]]$IdentityProviders
    )

    if (-not (Test-SchemaPackCapabilityEnabled $Packs 'hosted-identity-embodiment')) {
        throw "Hosted identity registry requires enabled capability 'hosted-identity-embodiment'."
    }
    $root = ConvertFrom-KnowledgeYamlFile `
        $Project.hosting_registry `
        $script:SupportedHostingSchemaVersion `
        'hosted identity registry'
    Assert-KnowledgeMapKeys `
        $root `
    @('schema_version', 'carriers', 'occupancies', 'transitions') `
        'Hosted identity registry root'

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
        carriers = $carriers
        occupancies = $occupancies
        transitions = $transitions
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

function Get-KnowledgeHostingProvenanceTargets {
    param([object]$Registry)

    return [ordered]@{
        'host-carrier' = $Registry.carriers
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

    return [ordered]@{
        provider_id = 'hosting'
        targets = [ordered]@{ 'host-carrier' = $Registry.carriers }
        aliases = [ordered]@{ 'host-carrier' = @{} }
    }
}
