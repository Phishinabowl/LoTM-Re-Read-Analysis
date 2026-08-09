$script:SupportedCapabilityRoadmapSchemaVersion = 2
$script:CapabilityRoadmapRegistryId = 'capability-roadmap'
$script:CapabilityRoadmapStableIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'
$script:CapabilityRoadmapDeliveryTargetKinds = @('platform-phase')
$script:CapabilityRoadmapDispositions = @('accepted-deferral', 'scheduled')
$script:CapabilityRoadmapEvidenceCriteria = @(
    'compatibility-impact'
    'conformance-ambiguity'
    'conformance-boundary'
    'conformance-malformed'
    'conformance-positive'
    'conformance-scale'
    'consumer-regression'
    'contract'
    'documentation'
    'emergency-decision'
    'evolution'
    'extraction-review'
    'migration-guidance'
    'runtime-parity'
    'runtime-support'
)
$script:CapabilityRoadmapProviderScopedCriteria = @(
    'conformance-ambiguity'
    'conformance-boundary'
    'conformance-malformed'
    'conformance-positive'
    'conformance-scale'
    'contract'
    'runtime-parity'
    'runtime-support'
)
$script:CapabilityLifecycles = @('available', 'deprecated', 'planned')
$script:CapabilityTransitionTypes = [ordered]@{
    'planned|available' = 'promotion'
    'planned|' = 'withdrawal'
    'available|deprecated' = 'deprecation'
    'deprecated|available' = 'rescission'
    'deprecated|' = 'removal'
    'available|' = 'emergency-removal'
}
$script:CapabilityPromotionCriteria = @(
    'compatibility-impact'
    'conformance-ambiguity'
    'conformance-boundary'
    'conformance-malformed'
    'conformance-positive'
    'conformance-scale'
    'consumer-regression'
    'contract'
    'documentation'
    'evolution'
    'extraction-review'
    'runtime-support'
)
$script:CapabilityTransitionCriteria = [ordered]@{
    promotion = $script:CapabilityPromotionCriteria
    rescission = $script:CapabilityPromotionCriteria
    withdrawal = @('compatibility-impact', 'documentation', 'evolution')
    deprecation = @(
        'compatibility-impact'
        'consumer-regression'
        'documentation'
        'evolution'
        'migration-guidance'
    )
    removal = @(
        'compatibility-impact'
        'consumer-regression'
        'documentation'
        'evolution'
        'extraction-review'
        'migration-guidance'
    )
    'emergency-removal' = @(
        'compatibility-impact'
        'consumer-regression'
        'documentation'
        'emergency-decision'
        'evolution'
        'extraction-review'
        'migration-guidance'
    )
    'material-reshape' = @(
        'compatibility-impact'
        'conformance-boundary'
        'conformance-malformed'
        'conformance-positive'
        'consumer-regression'
        'contract'
        'documentation'
        'evolution'
        'extraction-review'
    )
}

function Get-RequiredCapabilityRoadmapString {
    param(
        [object]$Map,
        [string]$Key,
        [string]$Context
    )

    $value = $Map[$Key]
    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
        throw "Capability roadmap '$Context.$Key' must be a non-empty string."
    }
    return ([string]$value).Trim()
}

function Assert-CapabilityRoadmapStableId {
    param([string]$Value, [string]$Context)

    if ($Value -cnotmatch $script:CapabilityRoadmapStableIdPattern) {
        throw "Capability roadmap '$Context' must be a lowercase kebab-case stable ID: $Value"
    }
    return $Value
}

function Get-CapabilityRoadmapStringList {
    param(
        [object]$Map,
        [string]$Key,
        [string]$Context
    )

    if ($Map -isnot [System.Collections.IDictionary] -or -not $Map.Contains($Key)) {
        throw "Capability roadmap '$Context.$Key' must be a list of non-empty strings."
    }
    $value = $Map[$Key]
    if ($null -eq $value) {
        return @()
    }
    if ($value -is [string] -or $value -is [System.Collections.IDictionary]) {
        throw "Capability roadmap '$Context.$Key' must be a list of non-empty strings."
    }
    $items = @($value)
    $result = @()
    foreach ($item in $items) {
        if ($item -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$item)) {
            throw "Capability roadmap '$Context.$Key' must be a list of non-empty strings."
        }
        $result += ([string]$item).Trim()
    }
    if (@($result | Sort-Object -Unique).Count -ne $result.Count) {
        throw "Capability roadmap '$Context.$Key' contains duplicate values."
    }
    return @($result | Sort-Object -CaseSensitive)
}

function Resolve-CapabilityRoadmapPlanPath {
    param(
        [string]$FrameworkDirectory,
        [string]$Value,
        [string]$Context
    )

    if ($Value.Contains('\')) {
        throw "Capability roadmap '$Context' must use forward slashes: $Value"
    }
    $segments = @($Value.Split('/'))
    if (
        [System.IO.Path]::IsPathRooted($Value) -or
        $Value -match '^[A-Za-z]:/' -or
        $Value.StartsWith('//') -or
        @($segments | Where-Object { $_ -in @('', '.', '..') }).Count -gt 0
    ) {
        throw "Capability roadmap '$Context' must be a confined framework-relative path: $Value"
    }
    $root = [System.IO.Path]::GetFullPath($FrameworkDirectory)
    $resolved = [System.IO.Path]::GetFullPath((Join-Path $root ($segments -join [System.IO.Path]::DirectorySeparatorChar)))
    if (
        -not $resolved.StartsWith(
            $root + [System.IO.Path]::DirectorySeparatorChar,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -or
        -not (Test-Path -LiteralPath $resolved -PathType Leaf)
    ) {
        throw "Capability roadmap '$Context' file does not exist beneath Framework: $Value"
    }
    return ($segments -join '/')
}

function Visit-CapabilityRoadmapDependency {
    param(
        [string]$CapabilityId,
        [System.Collections.IDictionary]$Dependencies,
        [System.Collections.Generic.HashSet[string]]$Visiting,
        [System.Collections.Generic.HashSet[string]]$Visited
    )

    if ($Visited.Contains($CapabilityId)) {
        return
    }
    if (-not $Visiting.Add($CapabilityId)) {
        throw (
            'Capability roadmap domain-capability delivery dependencies contain a cycle at ' +
            "'$CapabilityId'."
        )
    }
    foreach ($dependencyId in @($Dependencies[$CapabilityId])) {
        if ($Dependencies.Contains($dependencyId)) {
            Visit-CapabilityRoadmapDependency $dependencyId $Dependencies $Visiting $Visited
        }
    }
    $null = $Visiting.Remove($CapabilityId)
    $null = $Visited.Add($CapabilityId)
}

function Assert-CapabilityRoadmapAcyclic {
    param([System.Collections.IDictionary]$Dependencies)

    $visiting = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $visited = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($capabilityId in @($Dependencies.Keys | Sort-Object -CaseSensitive)) {
        Visit-CapabilityRoadmapDependency $capabilityId $Dependencies $visiting $visited
    }
}

function ConvertTo-KnowledgeCapabilityRoadmap {
    param(
        [object]$Data,
        [object]$FrameworkConfig,
        [object]$FrameworkCatalog
    )

    Assert-KnowledgeMapKeys `
        $Data `
    @('schema_version', 'registry_id', 'delivery_targets', 'capabilities') `
        'Capability roadmap root'
    $registryId = Assert-CapabilityRoadmapStableId `
    (Get-RequiredCapabilityRoadmapString $Data 'registry_id' 'root') `
        'root.registry_id'
    if ($registryId -cne $script:CapabilityRoadmapRegistryId) {
        throw (
            "Capability roadmap 'root.registry_id' must be '$($script:CapabilityRoadmapRegistryId)': " +
            $registryId
        )
    }

    $targetMap = Get-ProjectMapValue $Data 'delivery_targets'
    if ($targetMap -isnot [System.Collections.IDictionary]) {
        throw "Capability roadmap 'delivery_targets' must be a mapping."
    }
    $targets = [ordered]@{}
    foreach ($targetId in @($targetMap.Keys | Sort-Object -CaseSensitive)) {
        $null = Assert-CapabilityRoadmapStableId $targetId "delivery_targets.$targetId"
        $context = "delivery_targets.$targetId"
        $target = $targetMap[$targetId]
        Assert-KnowledgeMapKeys `
            $target `
        @('kind', 'label', 'plan_path', 'plan_anchor') `
            "Capability roadmap '$context'"
        $kind = Get-RequiredCapabilityRoadmapString $target 'kind' $context
        if ($script:CapabilityRoadmapDeliveryTargetKinds -cnotcontains $kind) {
            throw (
                "Capability roadmap '$context.kind' must be one of: " +
                "$($script:CapabilityRoadmapDeliveryTargetKinds -join ', ')."
            )
        }
        $targets[$targetId] = [ordered]@{
            id = $targetId
            kind = $kind
            label = Get-RequiredCapabilityRoadmapString $target 'label' $context
            plan_path = Resolve-CapabilityRoadmapPlanPath `
                $FrameworkConfig.framework_directory `
            (Get-RequiredCapabilityRoadmapString $target 'plan_path' $context) `
                "$context.plan_path"
            plan_anchor = Assert-CapabilityRoadmapStableId `
            (Get-RequiredCapabilityRoadmapString $target 'plan_anchor' $context) `
                "$context.plan_anchor"
        }
    }

    if ($null -eq $FrameworkCatalog -or [string]$FrameworkCatalog.contract -cne 'framework-catalog') {
        throw 'Capability roadmap validation requires a validated FrameworkCatalog.'
    }
    $catalogCapabilities = [ordered]@{}
    foreach ($row in @($FrameworkCatalog.capabilities)) {
        $catalogCapabilities[[string]$row.id] = $row
    }
    $plannedIds = @(
        $FrameworkCatalog.capabilities |
            Where-Object planned |
            ForEach-Object { [string]$_.id } |
            Sort-Object -CaseSensitive
    )
    $capabilityMap = Get-ProjectMapValue $Data 'capabilities'
    if ($capabilityMap -isnot [System.Collections.IDictionary]) {
        throw "Capability roadmap 'capabilities' must be a mapping."
    }
    $authoredIds = @($capabilityMap.Keys | Sort-Object -CaseSensitive)
    $missing = @($plannedIds | Where-Object { $authoredIds -cnotcontains $_ })
    if ($missing.Count -gt 0) {
        throw "Capability roadmap is missing planned capability mapping(s): $($missing -join ', ')."
    }
    $stale = @($authoredIds | Where-Object { $plannedIds -cnotcontains $_ })
    if ($stale.Count -gt 0) {
        $unknown = @($stale | Where-Object { -not $catalogCapabilities.Contains($_) })
        if ($unknown.Count -gt 0) {
            throw "Capability roadmap references unknown capability ID(s): $($unknown -join ', ')."
        }
        throw "Capability roadmap contains non-planned capability mapping(s): $($stale -join ', ')."
    }

    $capabilities = [ordered]@{}
    $dependencyGraph = [ordered]@{}
    foreach ($capabilityId in $authoredIds) {
        $null = Assert-CapabilityRoadmapStableId $capabilityId "capabilities.$capabilityId"
        $context = "capabilities.$capabilityId"
        $entry = $capabilityMap[$capabilityId]
        $disposition = Get-RequiredCapabilityRoadmapString $entry 'disposition' $context
        if ($script:CapabilityRoadmapDispositions -cnotcontains $disposition) {
            throw (
                "Capability roadmap '$context.disposition' must be one of: " +
                "$($script:CapabilityRoadmapDispositions -join ', ')."
            )
        }
        $commonKeys = @(
            'disposition'
            'rationale'
            'platform_prerequisite_ids'
            'domain_capability_dependency_ids'
            'implementation_evidence'
        )
        if ($disposition -ceq 'scheduled') {
            Assert-KnowledgeMapKeys `
                $entry `
            ($commonKeys + 'delivery_target_id') `
                "Capability roadmap '$context'"
            $deliveryTargetId = Assert-CapabilityRoadmapStableId `
            (Get-RequiredCapabilityRoadmapString $entry 'delivery_target_id' $context) `
                "$context.delivery_target_id"
            if (-not $targets.Contains($deliveryTargetId)) {
                throw (
                    "Capability roadmap '$context.delivery_target_id' references unknown delivery target: " +
                    $deliveryTargetId
                )
            }
            $deferralId = $null
            $reviewTrigger = $null
        }
        else {
            Assert-KnowledgeMapKeys `
                $entry `
            ($commonKeys + @('deferral_id', 'review_trigger')) `
                "Capability roadmap '$context'"
            $deliveryTargetId = $null
            $deferralId = Assert-CapabilityRoadmapStableId `
            (Get-RequiredCapabilityRoadmapString $entry 'deferral_id' $context) `
                "$context.deferral_id"
            $reviewTrigger = Get-RequiredCapabilityRoadmapString $entry 'review_trigger' $context
        }

        $prerequisites = @(
            Get-CapabilityRoadmapStringList $entry 'platform_prerequisite_ids' $context
        )
        foreach ($prerequisiteId in $prerequisites) {
            $null = Assert-CapabilityRoadmapStableId `
                $prerequisiteId `
                "$context.platform_prerequisite_ids"
            if (-not $targets.Contains($prerequisiteId)) {
                throw (
                    "Capability roadmap '$context.platform_prerequisite_ids' references unknown " +
                    "delivery target: $prerequisiteId"
                )
            }
            if ($prerequisiteId -ceq $deliveryTargetId) {
                throw "Capability roadmap '$context' cannot depend on its own delivery target."
            }
        }

        $dependencies = @(
            Get-CapabilityRoadmapStringList $entry 'domain_capability_dependency_ids' $context
        )
        foreach ($dependencyId in $dependencies) {
            $null = Assert-CapabilityRoadmapStableId `
                $dependencyId `
                "$context.domain_capability_dependency_ids"
            if (-not $catalogCapabilities.Contains($dependencyId)) {
                throw (
                    "Capability roadmap '$context.domain_capability_dependency_ids' references " +
                    "unknown capability: $dependencyId"
                )
            }
            if ($dependencyId -ceq $capabilityId) {
                throw "Capability roadmap '$context' cannot depend on itself."
            }
        }

        $evidenceRows = $entry['implementation_evidence']
        if (-not $entry.Contains('implementation_evidence')) {
            throw "Capability roadmap '$context.implementation_evidence' must be a list."
        }
        if ($null -eq $evidenceRows) {
            $evidenceRows = @()
        }
        elseif ($evidenceRows -is [string] -or $evidenceRows -is [System.Collections.IDictionary]) {
            throw "Capability roadmap '$context.implementation_evidence' must be a list."
        }
        $providerIds = @($catalogCapabilities[$capabilityId].providers | ForEach-Object { [string]$_.pack_id })
        $evidence = @()
        $evidenceKeys = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
        $evidenceIndex = 0
        foreach ($evidenceRow in @($evidenceRows)) {
            $evidenceContext = "$context.implementation_evidence[$evidenceIndex]"
            Assert-KnowledgeMapKeys `
                $evidenceRow `
            @('criterion', 'reference', 'provider_pack_id') `
                "Capability roadmap '$evidenceContext'"
            $evidenceCriterion = Get-RequiredCapabilityRoadmapString `
                $evidenceRow `
                'criterion' `
                $evidenceContext
            if ($script:CapabilityRoadmapEvidenceCriteria -cnotcontains $evidenceCriterion) {
                throw (
                    "Capability roadmap '$evidenceContext.criterion' must be one of: " +
                    "$($script:CapabilityRoadmapEvidenceCriteria -join ', ')."
                )
            }
            $reference = Get-RequiredCapabilityRoadmapString $evidenceRow 'reference' $evidenceContext
            $providerPackId = Get-ProjectMapValue $evidenceRow 'provider_pack_id'
            if ($null -ne $providerPackId) {
                if ([string]::IsNullOrWhiteSpace([string]$providerPackId)) {
                    throw "Capability roadmap '$evidenceContext.provider_pack_id' must be a non-empty string."
                }
                $providerPackId = Assert-CapabilityRoadmapStableId `
                ([string]$providerPackId).Trim() `
                    "$evidenceContext.provider_pack_id"
                if ($providerIds -cnotcontains $providerPackId) {
                    throw (
                        "Capability roadmap '$evidenceContext.provider_pack_id' is not a provider of " +
                        "'$capabilityId': $providerPackId"
                    )
                }
            }
            if (
                $script:CapabilityRoadmapProviderScopedCriteria -ccontains $evidenceCriterion -and
                $null -eq $providerPackId
            ) {
                throw (
                    "Capability roadmap '$evidenceContext.provider_pack_id' is required for " +
                    "criterion '$evidenceCriterion'."
                )
            }
            $evidenceKey = "$evidenceCriterion`0$reference`0$providerPackId"
            if (-not $evidenceKeys.Add($evidenceKey)) {
                throw "Capability roadmap '$context.implementation_evidence' contains duplicates."
            }
            $evidence += [ordered]@{
                criterion = $evidenceCriterion
                reference = $reference
                provider_pack_id = $providerPackId
            }
            $evidenceIndex++
        }

        $capabilities[$capabilityId] = [ordered]@{
            capability_id = $capabilityId
            disposition = $disposition
            delivery_target_id = $deliveryTargetId
            deferral_id = $deferralId
            rationale = Get-RequiredCapabilityRoadmapString $entry 'rationale' $context
            review_trigger = $reviewTrigger
            platform_prerequisite_ids = @($prerequisites)
            domain_capability_dependency_ids = @($dependencies)
            implementation_evidence = @($evidence)
        }
        $dependencyGraph[$capabilityId] = @($dependencies)
    }

    Assert-CapabilityRoadmapAcyclic $dependencyGraph
    return [ordered]@{
        schema_version = $script:SupportedCapabilityRoadmapSchemaVersion
        registry_id = $registryId
        delivery_targets = @($targets.Values)
        capabilities = @($capabilities.Values)
    }
}

function New-KnowledgeCapabilityDeliveryTraceabilityMap {
    param([object]$CapabilityRoadmap)

    $targets = [ordered]@{}
    foreach ($target in @($CapabilityRoadmap.delivery_targets)) {
        $targets[[string]$target.id] = $target
    }
    $projections = [ordered]@{}
    foreach ($row in @($CapabilityRoadmap.capabilities)) {
        $target = if ($null -eq $row.delivery_target_id) {
            $null
        }
        else {
            $targets[[string]$row.delivery_target_id]
        }
        $projections[[string]$row.capability_id] = [ordered]@{
            disposition = [string]$row.disposition
            delivery_target = if ($null -eq $target) {
                $null
            }
            else {
                [ordered]@{
                    id = [string]$target.id
                    kind = [string]$target.kind
                    label = [string]$target.label
                    plan_path = [string]$target.plan_path
                    plan_anchor = [string]$target.plan_anchor
                }
            }
            deferral = if ($null -eq $row.deferral_id) {
                $null
            }
            else {
                [ordered]@{
                    id = [string]$row.deferral_id
                    review_trigger = [string]$row.review_trigger
                }
            }
            rationale = [string]$row.rationale
            platform_prerequisite_ids = @($row.platform_prerequisite_ids)
            domain_capability_dependency_ids = @($row.domain_capability_dependency_ids)
            implementation_evidence = @(
                $row.implementation_evidence | ForEach-Object {
                    [ordered]@{
                        criterion = [string]$_.criterion
                        reference = [string]$_.reference
                        provider_pack_id = $_.provider_pack_id
                    }
                }
            )
        }
    }
    return $projections
}

function Get-KnowledgeCapabilityLifecycleTransition {
    param(
        [string]$CapabilityId,
        [string]$ProviderPackId,
        [string]$BeforeLifecycle,
        [AllowNull()][object]$AfterLifecycle,
        [object]$Decision,
        [string[]]$KnownCapabilityIds = @()
    )

    $null = Assert-CapabilityRoadmapStableId $CapabilityId 'transition.capability_id'
    $null = Assert-CapabilityRoadmapStableId $ProviderPackId 'transition.provider_pack_id'
    if ($script:CapabilityLifecycles -cnotcontains $BeforeLifecycle) {
        throw "Capability lifecycle transition has unknown before lifecycle: $BeforeLifecycle"
    }
    if ($null -ne $AfterLifecycle -and $script:CapabilityLifecycles -cnotcontains [string]$AfterLifecycle) {
        throw "Capability lifecycle transition has unknown after lifecycle: $AfterLifecycle"
    }
    if ($Decision -isnot [System.Collections.IDictionary]) {
        throw 'Capability lifecycle transition decision must be a mapping.'
    }
    Assert-KnowledgeMapKeys `
        $Decision `
    @(
        'transition'
        'rationale'
        'replacement_capability_id'
        'roadmap_after_present'
        'roadmap_before_present'
        'runtime_behavior_changed'
        'runtime_parity_required'
        'evidence'
    ) `
        'Capability lifecycle transition decision'

    $afterValue = if ($null -eq $AfterLifecycle) {
        ''
    }
    else {
        [string]$AfterLifecycle
    }
    $expectedTransition = if ($BeforeLifecycle -ceq $afterValue) {
        'material-reshape'
    }
    else {
        Get-ProjectMapValue $script:CapabilityTransitionTypes "$BeforeLifecycle|$afterValue"
    }
    $transition = Get-RequiredCapabilityRoadmapString $Decision 'transition' 'transition'
    if ($null -eq $expectedTransition -or $transition -cne [string]$expectedTransition) {
        $displayAfter = if ($null -eq $AfterLifecycle) {
            'removed'
        }
        else {
            [string]$AfterLifecycle
        }
        throw (
            'Capability lifecycle transition is invalid: ' +
            "$BeforeLifecycle -> $displayAfter as '$transition'."
        )
    }
    $null = Get-RequiredCapabilityRoadmapString $Decision 'rationale' 'transition'

    $roadmapBeforePresent = Get-ProjectMapValue $Decision 'roadmap_before_present'
    $roadmapAfterPresent = Get-ProjectMapValue $Decision 'roadmap_after_present'
    if ($roadmapBeforePresent -isnot [bool] -or $roadmapAfterPresent -isnot [bool]) {
        throw (
            "Capability lifecycle transition 'roadmap_before_present' and " +
            "'roadmap_after_present' must be booleans."
        )
    }
    if ($roadmapBeforePresent -ne ($BeforeLifecycle -ceq 'planned')) {
        throw 'Capability lifecycle transition before state has roadmap/lifecycle drift.'
    }
    if ($roadmapAfterPresent -ne ($AfterLifecycle -ceq 'planned')) {
        throw 'Capability lifecycle transition after state has roadmap/lifecycle drift.'
    }

    $runtimeBehaviorChanged = Get-ProjectMapValue $Decision 'runtime_behavior_changed'
    $runtimeParityRequired = Get-ProjectMapValue $Decision 'runtime_parity_required'
    if ($runtimeBehaviorChanged -isnot [bool] -or $runtimeParityRequired -isnot [bool]) {
        throw (
            "Capability lifecycle transition 'runtime_behavior_changed' and " +
            "'runtime_parity_required' must be booleans."
        )
    }
    if ($transition -cin @('promotion', 'rescission') -and -not $runtimeBehaviorChanged) {
        throw "Capability lifecycle '$transition' must declare changed runtime behavior."
    }
    if ($runtimeParityRequired -and -not $runtimeBehaviorChanged) {
        throw 'Capability lifecycle transition cannot require parity without runtime impact.'
    }

    $replacementId = Get-ProjectMapValue $Decision 'replacement_capability_id'
    if ($null -ne $replacementId) {
        if ($replacementId -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$replacementId)) {
            throw 'Capability lifecycle transition replacement must be a stable capability ID or null.'
        }
        $replacementId = Assert-CapabilityRoadmapStableId `
        ([string]$replacementId).Trim() `
            'transition.replacement_capability_id'
        if ($replacementId -ceq $CapabilityId) {
            throw 'Capability lifecycle transition cannot replace a capability with itself.'
        }
        if ($KnownCapabilityIds -cnotcontains $replacementId) {
            throw "Capability lifecycle transition references unknown replacement: $replacementId"
        }
    }

    $evidenceRows = $Decision['evidence']
    if (
        $null -eq $evidenceRows -or
        $evidenceRows -is [string] -or
        $evidenceRows -is [System.Collections.IDictionary]
    ) {
        throw "Capability lifecycle transition 'evidence' must be a list."
    }
    $present = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    $index = 0
    foreach ($row in @($evidenceRows)) {
        $context = "transition.evidence[$index]"
        Assert-KnowledgeMapKeys $row @('criterion', 'reference', 'provider_pack_id') $context
        $criterion = Get-RequiredCapabilityRoadmapString $row 'criterion' $context
        if ($script:CapabilityRoadmapEvidenceCriteria -cnotcontains $criterion) {
            throw (
                "Capability lifecycle transition '$context.criterion' must be one of: " +
                "$($script:CapabilityRoadmapEvidenceCriteria -join ', ')."
            )
        }
        $reference = Get-RequiredCapabilityRoadmapString $row 'reference' $context
        $evidenceProvider = Get-ProjectMapValue $row 'provider_pack_id'
        if ($null -ne $evidenceProvider) {
            if ($evidenceProvider -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$evidenceProvider)) {
                throw "Capability lifecycle transition '$context.provider_pack_id' is invalid."
            }
            $evidenceProvider = Assert-CapabilityRoadmapStableId `
            ([string]$evidenceProvider).Trim() `
                "$context.provider_pack_id"
        }
        if (
            $script:CapabilityRoadmapProviderScopedCriteria -ccontains $criterion -and
            $evidenceProvider -cne $ProviderPackId
        ) {
            throw (
                "Capability lifecycle transition criterion '$criterion' must name provider " +
                "'$ProviderPackId'."
            )
        }
        if (-not $seen.Add("$criterion`0$reference`0$evidenceProvider")) {
            throw 'Capability lifecycle transition evidence contains duplicates.'
        }
        $null = $present.Add($criterion)
        $index++
    }

    $required = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($criterion in @($script:CapabilityTransitionCriteria[$transition])) {
        $null = $required.Add($criterion)
    }
    if ($runtimeBehaviorChanged) {
        $null = $required.Add('runtime-support')
    }
    if ($runtimeParityRequired) {
        $null = $required.Add('runtime-parity')
    }
    $requiredRows = @($required | Sort-Object -CaseSensitive)
    $presentRows = @($present | Sort-Object -CaseSensitive)
    $missingRows = @($requiredRows | Where-Object { -not $present.Contains($_) })
    return [ordered]@{
        capability_id = $CapabilityId
        provider_pack_id = $ProviderPackId
        transition = $transition
        before_lifecycle = $BeforeLifecycle
        after_lifecycle = $AfterLifecycle
        replacement_capability_id = $replacementId
        roadmap_before_present = $roadmapBeforePresent
        roadmap_after_present = $roadmapAfterPresent
        runtime_behavior_changed = $runtimeBehaviorChanged
        runtime_parity_required = $runtimeParityRequired
        required_criteria = $requiredRows
        present_criteria = $presentRows
        missing_criteria = $missingRows
        ready = $missingRows.Count -eq 0
    }
}

function Get-KnowledgeCapabilityRoadmapModel {
    param([string]$FrameworkRoot)

    $catalogModel = Get-KnowledgeFrameworkCatalogModel $FrameworkRoot
    $config = $catalogModel.config
    if ($null -eq $config.capability_roadmap_registry) {
        throw "Framework manifest schema 2 with 'registries.capability_roadmap' is required."
    }
    $data = ConvertFrom-KnowledgeYamlFile `
        $config.capability_roadmap_registry `
        $script:SupportedCapabilityRoadmapSchemaVersion `
        'capability roadmap'
    return [pscustomobject]@{
        config = $config
        registry_path = $config.capability_roadmap_registry
        document = ConvertTo-KnowledgeCapabilityRoadmap $data $config $catalogModel.document
    }
}

function Get-KnowledgeCapabilityRoadmap {
    param([string]$FrameworkRoot)

    return (Get-KnowledgeCapabilityRoadmapModel $FrameworkRoot).document
}
