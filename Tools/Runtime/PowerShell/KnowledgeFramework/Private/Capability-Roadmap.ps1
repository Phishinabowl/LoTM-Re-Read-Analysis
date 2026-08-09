$script:SupportedCapabilityRoadmapSchemaVersion = 1
$script:CapabilityRoadmapRegistryId = 'capability-roadmap'
$script:CapabilityRoadmapStableIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'
$script:CapabilityRoadmapDeliveryTargetKinds = @('platform-phase')
$script:CapabilityRoadmapDispositions = @('accepted-deferral', 'scheduled')
$script:CapabilityRoadmapEvidenceKinds = @(
    'compatibility'
    'conformance'
    'contract'
    'documentation'
    'extraction'
    'runtime'
)

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
            @('kind', 'reference', 'provider_pack_id') `
                "Capability roadmap '$evidenceContext'"
            $evidenceKind = Get-RequiredCapabilityRoadmapString $evidenceRow 'kind' $evidenceContext
            if ($script:CapabilityRoadmapEvidenceKinds -cnotcontains $evidenceKind) {
                throw (
                    "Capability roadmap '$evidenceContext.kind' must be one of: " +
                    "$($script:CapabilityRoadmapEvidenceKinds -join ', ')."
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
            $evidenceKey = "$evidenceKind`0$reference`0$providerPackId"
            if (-not $evidenceKeys.Add($evidenceKey)) {
                throw "Capability roadmap '$context.implementation_evidence' contains duplicates."
            }
            $evidence += [ordered]@{
                kind = $evidenceKind
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
