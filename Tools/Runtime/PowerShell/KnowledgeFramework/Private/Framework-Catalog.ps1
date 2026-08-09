$script:FrameworkCatalogContractVersion = 3
$script:FrameworkCatalogSelectionContractVersion = 3
$script:FrameworkCatalogProjectViewContractVersion = 3
$script:FrameworkCatalogProjectViewSelectionContractVersion = 3

function New-FrameworkCatalogClassifiedException {
    param([string]$Classification, [string]$Message, [System.Exception]$InnerException)

    $exception = [System.InvalidOperationException]::new($Message, $InnerException)
    $exception.Data['FrameworkCatalogClassification'] = $Classification
    return $exception
}

function Get-FrameworkCatalogOrdinalStrings {
    param([object[]]$Values)

    $normalized = @()
    foreach ($value in @($Values)) {
        if ($value -is [string] -or $value -isnot [System.Collections.IEnumerable]) {
            $normalized += [string]$value
            continue
        }
        foreach ($nestedValue in $value) {
            $normalized += [string]$nestedValue
        }
    }
    $items = [string[]]$normalized
    [Array]::Sort($items, [System.StringComparer]::Ordinal)
    return @($items)
}

function Get-FrameworkCatalogRelativePath {
    param([string]$Path, [string]$Root)

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $prefix = $resolvedRoot + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Framework catalog path escapes the framework root: $resolved"
    }
    return $resolved.Substring($prefix.Length).Replace('\', '/')
}

function ConvertTo-FrameworkCatalogPresentationEntry {
    param([object]$Entry)

    return [ordered]@{
        id = [string]$Entry.id
        label = [string]$Entry.label
        description = [string]$Entry.description
    }
}

function ConvertTo-FrameworkCatalogClassification {
    param([AllowNull()][object]$Classification)

    if ($null -eq $Classification) {
        return $null
    }
    return [ordered]@{
        family = [string]$Classification.family
        role = [string]$Classification.role
        scope = [string]$Classification.scope
        domains = @($Classification.domains)
        bridge_pack_ids = @($Classification.bridge_pack_ids)
    }
}

function ConvertTo-FrameworkCatalogPackPresentation {
    param([AllowNull()][object]$Presentation)

    if ($null -eq $Presentation) {
        return $null
    }
    $visual = if ($null -eq $Presentation.visual) {
        $null
    }
    else {
        [ordered]@{
            icon_id = $Presentation.visual.icon_id
            accent_token = $Presentation.visual.accent_token
        }
    }
    return [ordered]@{
        localization_key = [string]$Presentation.localization_key
        default_locale = [string]$Presentation.default_locale
        label = [string]$Presentation.label
        short_description = [string]$Presentation.short_description
        long_description = [string]$Presentation.long_description
        maturity = [string]$Presentation.maturity
        intended_audiences = @(
            $Presentation.intended_audiences | ForEach-Object {
                ConvertTo-FrameworkCatalogPresentationEntry $_
            }
        )
        use_cases = @(
            $Presentation.use_cases | ForEach-Object {
                ConvertTo-FrameworkCatalogPresentationEntry $_
            }
        )
        examples = @(
            $Presentation.examples | ForEach-Object {
                ConvertTo-FrameworkCatalogPresentationEntry $_
            }
        )
        prerequisites = @(
            $Presentation.prerequisites | ForEach-Object {
                ConvertTo-FrameworkCatalogPresentationEntry $_
            }
        )
        provided_behaviors = @(
            $Presentation.provided_behaviors | ForEach-Object {
                ConvertTo-FrameworkCatalogPresentationEntry $_
            }
        )
        exclusions = @(
            $Presentation.exclusions | ForEach-Object {
                ConvertTo-FrameworkCatalogPresentationEntry $_
            }
        )
        documentation = @(
            $Presentation.documentation | ForEach-Object {
                [ordered]@{
                    id = [string]$_.id
                    label = [string]$_.label
                    target_kind = [string]$_.target_kind
                    target = [string]$_.target
                }
            }
        )
        search_keywords = @($Presentation.search_keywords)
        visual = $visual
    }
}

function ConvertTo-FrameworkCatalogCapabilityPresentation {
    param([AllowNull()][object]$Presentation)

    if ($null -eq $Presentation) {
        return $null
    }
    return [ordered]@{
        localization_key = [string]$Presentation.localization_key
        label = [string]$Presentation.label
        description = [string]$Presentation.description
    }
}

function Assert-FrameworkCatalogDependencies {
    param([System.Collections.IDictionary]$Packs)

    $packIds = @(Get-FrameworkCatalogOrdinalStrings $Packs.Keys)
    $indegree = @{}
    $dependents = @{}
    foreach ($packId in $packIds) {
        $indegree[$packId] = @($Packs[$packId].dependencies).Count
        $dependents[$packId] = @()
    }
    foreach ($packId in $packIds) {
        foreach ($dependency in @($Packs[$packId].dependencies)) {
            if (-not $Packs.Contains($dependency.pack_id)) {
                throw "Installed schema pack '$packId' requires missing pack '$($dependency.pack_id)'."
            }
            $installed = $Packs[$dependency.pack_id]
            if ([int]$installed.pack_version -lt [int]$dependency.minimum_version) {
                throw (
                    "Installed schema pack '$packId' requires '$($dependency.pack_id)' version " +
                    "$($dependency.minimum_version) or newer; installed version is $($installed.pack_version)."
                )
            }
            $dependents[$dependency.pack_id] = @($dependents[$dependency.pack_id]) + $packId
        }
    }

    $ready = @($packIds | Where-Object { [int]$indegree[$_] -eq 0 })
    $processed = 0
    while ($ready.Count -gt 0) {
        $ready = @(Get-FrameworkCatalogOrdinalStrings $ready)
        $current = $ready[0]
        $ready = @($ready | Select-Object -Skip 1)
        $processed++
        foreach ($dependent in @(Get-FrameworkCatalogOrdinalStrings $dependents[$current])) {
            $indegree[$dependent] = [int]$indegree[$dependent] - 1
            if ([int]$indegree[$dependent] -eq 0) {
                $ready += $dependent
            }
        }
    }
    if ($processed -ne $packIds.Count) {
        $cycleMembers = @($packIds | Where-Object { [int]$indegree[$_] -gt 0 })
        throw "Installed schema-pack dependency graph contains a cycle: $($cycleMembers -join ', ')."
    }
}

function Get-FrameworkCatalogPackConfigs {
    param([object]$FrameworkConfig)

    $candidates = @()
    $directoryKeys = New-Object 'System.Collections.Generic.Dictionary[string,string]' (
        [System.StringComparer]::OrdinalIgnoreCase
    )
    $resolvedFiles = New-Object 'System.Collections.Generic.Dictionary[string,string]' (
        [System.StringComparer]::OrdinalIgnoreCase
    )
    try {
        foreach ($directory in @(Get-ChildItem -LiteralPath $FrameworkConfig.packs_root -Directory)) {
            $packPath = Join-Path $directory.FullName 'pack.yaml'
            if (-not (Test-Path -LiteralPath $packPath -PathType Leaf)) {
                continue
            }
            $packId = $directory.Name
            if ($directoryKeys.ContainsKey($packId)) {
                throw "Installed schema-pack directories collide by case: $($directoryKeys[$packId]), $packId."
            }
            $directoryKeys[$packId] = $packId
            Assert-SchemaPackStableId $packId 'installed pack directory'
            $resolvedFile = [System.IO.Path]::GetFullPath($packPath)
            if ($resolvedFiles.ContainsKey($resolvedFile)) {
                throw "Installed schema packs '$($resolvedFiles[$resolvedFile])' and '$packId' resolve to the same pack file."
            }
            $resolvedFiles[$resolvedFile] = $packId
            $candidates += [pscustomobject]@{ id = $packId
                path = $resolvedFile
            }
        }
    }
    catch {
        throw (New-FrameworkCatalogClassifiedException 'installed-pack-discovery' $_.Exception.Message $_.Exception)
    }

    $packs = [ordered]@{}
    foreach ($packId in @(Get-FrameworkCatalogOrdinalStrings ($candidates | ForEach-Object id))) {
        $candidate = @($candidates | Where-Object { $_.id -ceq $packId })[0]
        try {
            $packs[$packId] = ConvertTo-SchemaPackConfig $candidate.path $packId
        }
        catch {
            throw (New-FrameworkCatalogClassifiedException 'pack-parsing' $_.Exception.Message $_.Exception)
        }
    }
    try {
        Assert-FrameworkCatalogDependencies $packs
        Assert-SchemaPackPresentationComposition $packs @(Get-FrameworkCatalogOrdinalStrings $packs.Keys)
    }
    catch {
        throw (New-FrameworkCatalogClassifiedException 'catalog-composition' $_.Exception.Message $_.Exception)
    }
    return $packs
}

function ConvertTo-FrameworkCatalogControlledNamespaces {
    param([object]$Pack)

    $rows = @()
    foreach ($namespace in @(Get-FrameworkCatalogOrdinalStrings $Pack.controlled_values.Keys)) {
        $definitions = $Pack.controlled_value_definitions[$namespace]
        $values = @()
        foreach ($valueId in @($Pack.controlled_values[$namespace])) {
            $definition = $definitions[$valueId]
            $values += [ordered]@{
                id = [string]$valueId
                label = $definition.label
                description = $definition.description
                broader_value = $definition.broader_value
            }
        }
        $rows += [ordered]@{ id = [string]$namespace
            values = @($values)
        }
    }
    return @($rows)
}

function New-KnowledgeFrameworkCatalog {
    param(
        [object]$FrameworkConfig,
        [System.Collections.IDictionary]$PackConfigs,
        [object]$CapabilityRoadmap
    )

    $deliveryTraceability = if ($null -eq $CapabilityRoadmap) {
        [ordered]@{}
    }
    else {
        New-KnowledgeCapabilityDeliveryTraceabilityMap $CapabilityRoadmap
    }

    $packRows = @()
    $capabilityProviders = [ordered]@{}
    $capabilityGroupDefinitions = [ordered]@{}
    $capabilityGroupContributions = [ordered]@{}
    $capabilityGroupIdsByCapability = [ordered]@{}
    foreach ($packId in @(Get-FrameworkCatalogOrdinalStrings $PackConfigs.Keys)) {
        $pack = $PackConfigs[$packId]
        $dependencies = @(
            $pack.dependencies | ForEach-Object {
                [ordered]@{
                    pack_id = [string]$_.pack_id
                    minimum_version = [int]$_.minimum_version
                    installed_version = [int]$PackConfigs[$_.pack_id].pack_version
                    status = 'satisfied'
                }
            }
        )
        $packRows += [ordered]@{
            id = [string]$pack.id
            record_id = "framework-catalog:pack:$($pack.id)"
            path = Get-FrameworkCatalogRelativePath $pack.path $FrameworkConfig.root
            schema_version = [int]$pack.schema_version
            pack_version = [int]$pack.pack_version
            lifecycle = [string]$pack.lifecycle
            kind = [string]$pack.kind
            classification = ConvertTo-FrameworkCatalogClassification $pack.classification
            presentation = ConvertTo-FrameworkCatalogPackPresentation $pack.presentation
            dependencies = @($dependencies)
            capability_ids = @($pack.capabilities)
            capability_group_ids = @($pack.capability_groups | ForEach-Object id)
            capability_group_contribution_ids = @($pack.capability_group_memberships | ForEach-Object group_id)
            controlled_value_namespaces = @(ConvertTo-FrameworkCatalogControlledNamespaces $pack)
            discoverability = [ordered]@{
                installed = $true
                selectable = $pack.lifecycle -ceq 'active'
            }
        }
        foreach ($capabilityId in @($pack.capabilities)) {
            if (-not $capabilityProviders.Contains($capabilityId)) {
                $capabilityProviders[$capabilityId] = @()
            }
            $capabilityProviders[$capabilityId] = @($capabilityProviders[$capabilityId]) + [pscustomobject]@{
                pack_id = $packId
                definition = $pack.capability_definitions[$capabilityId]
            }
        }
        foreach ($group in @($pack.capability_groups)) {
            $capabilityGroupDefinitions[$group.id] = [pscustomobject]@{
                owner_pack_id = $packId
                definition = $group
            }
        }
        foreach ($membership in @($pack.capability_group_memberships)) {
            if (-not $capabilityGroupContributions.Contains($membership.group_id)) {
                $capabilityGroupContributions[$membership.group_id] = @()
            }
            $capabilityGroupContributions[$membership.group_id] = @(
                $capabilityGroupContributions[$membership.group_id]
            ) + [ordered]@{
                provider_pack_id = $packId
                order = [int]$membership.order
                capability_ids = @($membership.capability_ids)
            }
            foreach ($capabilityId in @($membership.capability_ids)) {
                if (-not $capabilityGroupIdsByCapability.Contains($capabilityId)) {
                    $capabilityGroupIdsByCapability[$capabilityId] = @()
                }
                if (@($capabilityGroupIdsByCapability[$capabilityId]) -cnotcontains $membership.group_id) {
                    $capabilityGroupIdsByCapability[$capabilityId] = @(
                        $capabilityGroupIdsByCapability[$capabilityId]
                    ) + $membership.group_id
                }
            }
        }
    }

    $capabilityGroupRows = @()
    foreach ($entry in @($capabilityGroupDefinitions.GetEnumerator() | Sort-Object { $_.Value.definition.order }, Key)) {
        $groupId = [string]$entry.Key
        $definition = $entry.Value.definition
        $contributions = @(
            @($capabilityGroupContributions[$groupId]) |
                Sort-Object @{ Expression = 'order'
                    Ascending = $true
                },
                @{ Expression = 'provider_pack_id'
                    Ascending = $true
                }
        )
        $capabilityIds = @()
        foreach ($contribution in $contributions) {
            foreach ($capabilityId in @($contribution.capability_ids)) {
                if ($capabilityIds -cnotcontains $capabilityId) {
                    $capabilityIds += $capabilityId
                }
            }
        }
        $capabilityGroupRows += [ordered]@{
            id = $groupId
            record_id = "framework-catalog:capability-group:$groupId"
            order = [int]$definition.order
            presentation = ConvertTo-FrameworkCatalogCapabilityPresentation $definition.presentation
            owner_pack_id = [string]$entry.Value.owner_pack_id
            contributions = @($contributions)
            capability_ids = @($capabilityIds)
        }
    }

    $capabilityRows = @()
    foreach ($capabilityId in @(Get-FrameworkCatalogOrdinalStrings $capabilityProviders.Keys)) {
        $providers = @($capabilityProviders[$capabilityId])
        $lifecycles = @($providers | ForEach-Object { $_.definition.lifecycle })
        $effectiveLifecycle = if ($lifecycles -ccontains 'available') {
            'available'
        }
        elseif ($lifecycles -ccontains 'deprecated') {
            'deprecated'
        }
        else {
            'planned'
        }
        $capabilityRows += [ordered]@{
            id = [string]$capabilityId
            record_id = "framework-catalog:capability:$capabilityId"
            presentation = ConvertTo-FrameworkCatalogCapabilityPresentation $providers[0].definition.presentation
            effective_lifecycle = $effectiveLifecycle
            available = $effectiveLifecycle -ceq 'available'
            deprecated = $effectiveLifecycle -ceq 'deprecated'
            planned = $effectiveLifecycle -ceq 'planned'
            delivery_traceability = if ($deliveryTraceability.Contains($capabilityId)) {
                $deliveryTraceability[$capabilityId]
            }
            else {
                $null
            }
            group_ids = @($capabilityGroupIdsByCapability[$capabilityId])
            relationships = [ordered]@{
                requires = @($providers[0].definition.relationships.requires)
                recommends = @($providers[0].definition.relationships.recommends)
                conflicts_with = @($providers[0].definition.relationships.conflicts_with)
            }
            providers = @(
                $providers | ForEach-Object {
                    [ordered]@{
                        pack_id = [string]$_.pack_id
                        lifecycle = [string]$_.definition.lifecycle
                        presentation = ConvertTo-FrameworkCatalogCapabilityPresentation $_.definition.presentation
                        pack_dependencies = @($PackConfigs[$_.pack_id].dependencies | ForEach-Object pack_id)
                        controlled_value_namespace_ids = @(
                            Get-FrameworkCatalogOrdinalStrings $PackConfigs[$_.pack_id].controlled_values.Keys
                        )
                    }
                }
            )
        }
    }

    return [pscustomobject][ordered]@{
        contract = 'framework-catalog'
        contract_version = $script:FrameworkCatalogContractVersion
        framework = [ordered]@{
            id = [string]$FrameworkConfig.framework_id
            manifest_path = Get-FrameworkCatalogRelativePath $FrameworkConfig.manifest_path $FrameworkConfig.root
            packs_root = Get-FrameworkCatalogRelativePath $FrameworkConfig.packs_root $FrameworkConfig.root
            lookup_registry = Get-FrameworkCatalogRelativePath `
                $FrameworkConfig.lookup_keys_registry `
                $FrameworkConfig.root
            lookup_algorithm = [string]$FrameworkConfig.lookup_keys.algorithm
            unicode_version = [string]$FrameworkConfig.lookup_keys.unicode_version
            capability_roadmap_registry = if ($null -eq $FrameworkConfig.capability_roadmap_registry) {
                $null
            }
            else {
                Get-FrameworkCatalogRelativePath $FrameworkConfig.capability_roadmap_registry $FrameworkConfig.root
            }
            capability_roadmap_schema_version = if ($null -eq $CapabilityRoadmap) {
                $null
            }
            else {
                [int]$CapabilityRoadmap.schema_version
            }
        }
        summary = [ordered]@{
            pack_count = $packRows.Count
            capability_group_count = $capabilityGroupRows.Count
            capability_count = $capabilityRows.Count
            available_capability_count = @($capabilityRows | Where-Object available).Count
            deprecated_capability_count = @($capabilityRows | Where-Object deprecated).Count
            planned_capability_count = @($capabilityRows | Where-Object planned).Count
            scheduled_capability_count = @(
                $capabilityRows | Where-Object {
                    $null -ne $_.delivery_traceability -and
                    $_.delivery_traceability.disposition -ceq 'scheduled'
                }
            ).Count
            deferred_capability_count = @(
                $capabilityRows | Where-Object {
                    $null -ne $_.delivery_traceability -and
                    $_.delivery_traceability.disposition -ceq 'accepted-deferral'
                }
            ).Count
        }
        packs = @($packRows)
        capability_groups = @($capabilityGroupRows)
        capabilities = @($capabilityRows)
    }
}

function Get-KnowledgeFrameworkCatalogModel {
    param([string]$Root)

    try {
        $config = Get-KnowledgeFrameworkConfig $Root
    }
    catch {
        $classification = if ($_.Exception.Message.IndexOf(
                'lookup-key registry',
                [System.StringComparison]::OrdinalIgnoreCase
            ) -ge 0) {
            'lookup-registry'
        }
        else {
            'installation-manifest'
        }
        throw (New-FrameworkCatalogClassifiedException $classification $_.Exception.Message $_.Exception)
    }
    $packs = Get-FrameworkCatalogPackConfigs $config
    try {
        $baseDocument = New-KnowledgeFrameworkCatalog $config $packs $null
        $roadmap = $null
        if ($null -ne $config.capability_roadmap_registry) {
            $roadmapData = ConvertFrom-KnowledgeYamlFile `
                $config.capability_roadmap_registry `
                $script:SupportedCapabilityRoadmapSchemaVersion `
                'capability roadmap'
            $roadmap = ConvertTo-KnowledgeCapabilityRoadmap $roadmapData $config $baseDocument
        }
        return [pscustomobject]@{
            config = $config
            pack_configs = $packs
            capability_roadmap = $roadmap
            document = New-KnowledgeFrameworkCatalog $config $packs $roadmap
        }
    }
    catch {
        throw (New-FrameworkCatalogClassifiedException 'catalog-composition' $_.Exception.Message $_.Exception)
    }
}

function Get-KnowledgeFrameworkCatalog {
    param([string]$Root)

    return (Get-KnowledgeFrameworkCatalogModel $Root).document
}

function Resolve-KnowledgeFrameworkCatalogRow {
    param(
        [object[]]$Rows,
        [string]$Value,
        [string]$RecordName,
        [object]$LookupKeys
    )

    $exact = @($Rows | Where-Object { $_.id -ceq $Value })
    if ($exact.Count -gt 0) {
        return $exact[0]
    }
    $normalized = ConvertTo-KnowledgeLookupKey $Value $LookupKeys
    $matches = @(
        $Rows | Where-Object {
            (ConvertTo-KnowledgeLookupKey ([string]$_.id) $LookupKeys) -ceq $normalized
        }
    )
    if ($matches.Count -eq 0) {
        throw "Unknown framework-catalog $RecordName ID ``$Value``."
    }
    if ($matches.Count -gt 1) {
        $matchIds = @($matches | ForEach-Object id) -join ', '
        throw "Ambiguous framework-catalog $RecordName ID ``$Value``; matches: $matchIds."
    }
    return $matches[0]
}

function Select-FrameworkCatalogCapabilities {
    param(
        [object[]]$Rows,
        [string[]]$ProviderPackIds,
        [string[]]$Lifecycles,
        [string[]]$Availability,
        [string[]]$Activation,
        [string[]]$Usage,
        [bool]$ProjectView
    )

    $allowed = @{
        lifecycle = @('available', 'deprecated', 'planned')
        availability = @('available', 'unavailable')
        activation = @('enabled', 'disabled')
        'project usage' = @('used', 'unused')
    }
    foreach ($specification in @(
            [pscustomobject]@{ label = 'lifecycle'
                values = @($Lifecycles)
            },
            [pscustomobject]@{ label = 'availability'
                values = @($Availability)
            },
            [pscustomobject]@{ label = 'activation'
                values = @($Activation)
            },
            [pscustomobject]@{ label = 'project usage'
                values = @($Usage)
            }
        )) {
        $unknown = @($specification.values | Where-Object { $allowed[$specification.label] -cnotcontains $_ })
        if ($unknown.Count -gt 0) {
            throw "Unknown capability $($specification.label) filter(s): $($unknown -join ', ')."
        }
    }
    if (-not $ProjectView -and (@($Activation).Count -gt 0 -or @($Usage).Count -gt 0)) {
        throw 'Capability activation and project-usage filters require a catalog project view.'
    }
    $filtered = @($Rows)
    if (@($ProviderPackIds).Count -gt 0) {
        $filtered = @($filtered | Where-Object {
                @($_.providers | Where-Object { $ProviderPackIds -ccontains $_.pack_id }).Count -gt 0
            })
    }
    if (@($Lifecycles).Count -gt 0) {
        $filtered = @($filtered | Where-Object { $Lifecycles -ccontains $_.effective_lifecycle })
    }
    if (@($Availability).Count -gt 0) {
        $filtered = @($filtered | Where-Object {
                $state = if ($_.available) {
                    'available'
                }
                else {
                    'unavailable'
                }
                $Availability -ccontains $state
            })
    }
    if (@($Activation).Count -gt 0) {
        $filtered = @($filtered | Where-Object {
                $state = if ($_.project_state.enabled) {
                    'enabled'
                }
                else {
                    'disabled'
                }
                $Activation -ccontains $state
            })
    }
    if (@($Usage).Count -gt 0) {
        $filtered = @($filtered | Where-Object {
                $state = if ($_.project_state.used_by_project) {
                    'used'
                }
                else {
                    'unused'
                }
                $Usage -ccontains $state
            })
    }
    return @($filtered)
}

function New-KnowledgeFrameworkCatalogSelection {
    param(
        [object]$Catalog,
        [object]$LookupKeys,
        [string]$PackId,
        [string]$GroupId,
        [string]$CapabilityId,
        [string[]]$ProviderPackIds = @(),
        [string[]]$Lifecycles = @(),
        [string[]]$Availability = @(),
        [string[]]$Activation = @(),
        [string[]]$Usage = @()
    )

    if (
        [string]::IsNullOrWhiteSpace($PackId) -and
        [string]::IsNullOrWhiteSpace($GroupId) -and
        [string]::IsNullOrWhiteSpace($CapabilityId) -and
        @($ProviderPackIds).Count -eq 0 -and
        @($Lifecycles).Count -eq 0 -and
        @($Availability).Count -eq 0 -and
        @($Activation).Count -eq 0 -and
        @($Usage).Count -eq 0
    ) {
        throw 'Framework-catalog selection requires an ID or capability filter.'
    }
    $selectedGroups = if ([string]::IsNullOrWhiteSpace($GroupId)) {
        @()
    }
    else {
        @(Resolve-KnowledgeFrameworkCatalogRow @($Catalog.capability_groups) $GroupId 'capability group' $LookupKeys)
    }
    $selectedGroups = @($selectedGroups)
    $selectedPacks = if ([string]::IsNullOrWhiteSpace($PackId)) {
        @()
    }
    else {
        @(Resolve-KnowledgeFrameworkCatalogRow @($Catalog.packs) $PackId 'pack' $LookupKeys)
    }
    $selectedPacks = @($selectedPacks)
    $normalizedProviderIds = @(
        $ProviderPackIds | ForEach-Object {
            (Resolve-KnowledgeFrameworkCatalogRow @($Catalog.packs) $_ 'pack' $LookupKeys).id
        }
    )
    $capabilityQueryRequested = (
        -not [string]::IsNullOrWhiteSpace($GroupId) -or
        -not [string]::IsNullOrWhiteSpace($CapabilityId) -or
        @($ProviderPackIds).Count -gt 0 -or @($Lifecycles).Count -gt 0 -or
        @($Availability).Count -gt 0 -or @($Activation).Count -gt 0 -or @($Usage).Count -gt 0
    )
    $selectedCapabilities = if ([string]::IsNullOrWhiteSpace($CapabilityId)) {
        if ($capabilityQueryRequested) {
            @($Catalog.capabilities)
        }
        else {
            @()
        }
    }
    else {
        @(
            Resolve-KnowledgeFrameworkCatalogRow `
            @($Catalog.capabilities) `
                $CapabilityId `
                'capability' `
                $LookupKeys
        )
    }
    $selectedCapabilities = @($selectedCapabilities)
    if ($selectedGroups.Count -gt 0) {
        $groupCapabilityIds = @($selectedGroups[0].capability_ids)
        $selectedCapabilities = @($selectedCapabilities | Where-Object { $groupCapabilityIds -ccontains $_.id })
    }
    $selectedCapabilities = @(
        Select-FrameworkCatalogCapabilities `
            -Rows $selectedCapabilities `
            -ProviderPackIds $normalizedProviderIds `
            -Lifecycles $Lifecycles `
            -Availability $Availability `
            -Activation $Activation `
            -Usage $Usage `
            -ProjectView $false
    )
    if ([string]::IsNullOrWhiteSpace($GroupId) -and (
            -not [string]::IsNullOrWhiteSpace($CapabilityId) -or
            @($ProviderPackIds).Count -gt 0 -or
            @($Lifecycles).Count -gt 0 -or
            @($Availability).Count -gt 0 -or
            @($Activation).Count -gt 0 -or
            @($Usage).Count -gt 0
        )) {
        $capabilityIds = @($selectedCapabilities | ForEach-Object id)
        $selectedGroups = @($Catalog.capability_groups | Where-Object {
                @($_.capability_ids | Where-Object { $capabilityIds -ccontains $_ }).Count -gt 0
            })
    }
    return [ordered]@{
        contract = 'framework-catalog-selection'
        contract_version = $script:FrameworkCatalogSelectionContractVersion
        catalog_contract_version = [int]$Catalog.contract_version
        requested = [ordered]@{
            pack = if ([string]::IsNullOrWhiteSpace($PackId)) {
                $null
            }
            else {
                $PackId
            }
            capability_group = if ([string]::IsNullOrWhiteSpace($GroupId)) {
                $null
            }
            else {
                $GroupId
            }
            capability = if ([string]::IsNullOrWhiteSpace($CapabilityId)) {
                $null
            }
            else {
                $CapabilityId
            }
            filters = [ordered]@{
                provider_pack_ids = @($normalizedProviderIds)
                lifecycles = @($Lifecycles)
                availability = @($Availability)
                activation = @($Activation)
                usage = @($Usage)
            }
        }
        packs = @($selectedPacks)
        capability_groups = @($selectedGroups)
        capabilities = @($selectedCapabilities)
    }
}

function Copy-FrameworkCatalogRow {
    param([object]$Row)

    $copy = [ordered]@{}
    if ($Row -is [System.Collections.IDictionary]) {
        foreach ($key in $Row.Keys) {
            $copy[[string]$key] = $Row[$key]
        }
    }
    else {
        foreach ($property in $Row.PSObject.Properties) {
            $copy[$property.Name] = $property.Value
        }
    }
    return $copy
}

function New-KnowledgeFrameworkCatalogProjectView {
    param(
        [object]$Catalog,
        [object]$EffectiveSchema
    )

    if ($EffectiveSchema.contract -cne 'effective-project-schema') {
        throw 'Framework catalog project view requires a validated EffectiveProjectSchema.'
    }
    if ($EffectiveSchema.project.framework_id -cne $Catalog.framework.id) {
        throw (
            "Project framework '$($EffectiveSchema.project.framework_id)' does not match catalog framework " +
            "'$($Catalog.framework.id)'."
        )
    }

    $selectedPacks = @{}
    foreach ($row in @($EffectiveSchema.packs)) {
        $selectedPacks[[string]$row.id] = $row
    }
    $selectedCapabilities = @{}
    foreach ($row in @($EffectiveSchema.capabilities)) {
        $selectedCapabilities[[string]$row.id] = $row
    }
    $selectedGroups = @{}
    foreach ($row in @($EffectiveSchema.capability_groups)) {
        $selectedGroups[[string]$row.id] = $row
    }
    $catalogPackIds = @($Catalog.packs | ForEach-Object id)
    $catalogGroupIds = @($Catalog.capability_groups | ForEach-Object id)
    $catalogCapabilityIds = @($Catalog.capabilities | ForEach-Object id)
    $missingPacks = @($selectedPacks.Keys | Where-Object { $catalogPackIds -cnotcontains $_ } | Sort-Object)
    if ($missingPacks.Count -gt 0) {
        throw "Effective schema selects pack(s) absent from the framework catalog: $($missingPacks -join ', ')."
    }
    $missingCapabilities = @(
        $selectedCapabilities.Keys |
            Where-Object { $catalogCapabilityIds -cnotcontains $_ } |
            Sort-Object
    )
    if ($missingCapabilities.Count -gt 0) {
        throw (
            'Effective schema declares capability or capabilities absent from the framework catalog: ' +
            "$($missingCapabilities -join ', ')."
        )
    }
    $missingGroups = @($selectedGroups.Keys | Where-Object { $catalogGroupIds -cnotcontains $_ } | Sort-Object)
    if ($missingGroups.Count -gt 0) {
        throw "Effective schema includes capability group(s) absent from the framework catalog: $($missingGroups -join ', ')."
    }

    $packRows = @()
    foreach ($catalogRow in @($Catalog.packs)) {
        $row = Copy-FrameworkCatalogRow $catalogRow
        $selected = $selectedPacks.ContainsKey([string]$catalogRow.id)
        $row.catalog_record_id = $row.record_id
        $row.record_id = "framework-catalog-project-view:pack:$($row.id)"
        $row.project_state = [ordered]@{
            selected = $selected
            available = [bool]$catalogRow.discoverability.selectable
            enabled = $selected
            deprecated = $false
            planned = $catalogRow.lifecycle -ceq 'deferred'
            used_by_project = $selected
            unavailable_reason = if ($catalogRow.discoverability.selectable) {
                $null
            }
            else {
                'pack-lifecycle-deferred'
            }
        }
        $packRows += $row
    }

    $groupRows = @()
    foreach ($catalogRow in @($Catalog.capability_groups)) {
        $row = Copy-FrameworkCatalogRow $catalogRow
        $selectedCapabilityRows = @(
            $catalogRow.capability_ids |
                Where-Object { $selectedCapabilities.ContainsKey([string]$_) } |
                ForEach-Object { $selectedCapabilities[[string]$_] }
        )
        $available = @($selectedCapabilityRows | Where-Object available).Count -gt 0
        $enabled = @($selectedCapabilityRows | Where-Object enabled).Count -gt 0
        $deprecated = $selectedCapabilityRows.Count -gt 0 -and @(
            $selectedCapabilityRows | Where-Object { -not $_.deprecated }
        ).Count -eq 0
        $planned = $selectedCapabilityRows.Count -gt 0 -and @(
            $selectedCapabilityRows | Where-Object { -not $_.planned }
        ).Count -eq 0
        $row.catalog_record_id = $row.record_id
        $row.record_id = "framework-catalog-project-view:capability-group:$($row.id)"
        $row.project_state = [ordered]@{
            selected = $selectedGroups.ContainsKey([string]$catalogRow.id)
            available = $available
            enabled = $enabled
            deprecated = $deprecated
            planned = $planned
            used_by_project = $enabled
            unavailable_reason = if ($available) {
                $null
            }
            else {
                'no-selected-available-capabilities'
            }
        }
        $groupRows += $row
    }

    $capabilityRows = @()
    foreach ($catalogRow in @($Catalog.capabilities)) {
        $row = Copy-FrameworkCatalogRow $catalogRow
        $selected = $selectedCapabilities.ContainsKey([string]$catalogRow.id)
        $effectiveRow = if ($selected) {
            $selectedCapabilities[[string]$catalogRow.id]
        }
        else {
            $null
        }
        $enabled = $selected -and [bool]$effectiveRow.enabled
        $row.catalog_record_id = $row.record_id
        $row.record_id = "framework-catalog-project-view:capability:$($row.id)"
        $row.project_state = [ordered]@{
            selected = $selected
            available = [bool]$(if ($selected) {
                    $effectiveRow.available
                }
                else {
                    $catalogRow.available
                })
            enabled = $enabled
            deprecated = [bool]$(if ($selected) {
                    $effectiveRow.deprecated
                }
                else {
                    $catalogRow.deprecated
                })
            planned = [bool]$(if ($selected) {
                    $effectiveRow.planned
                }
                else {
                    $catalogRow.planned
                })
            used_by_project = $enabled
            unavailable_reason = if ($selected) {
                $effectiveRow.unavailable_reason
            }
            elseif ($catalogRow.planned) {
                'capability-lifecycle-planned'
            }
            else {
                $null
            }
        }
        $capabilityRows += $row
    }

    return [ordered]@{
        contract = 'framework-catalog-project-view'
        contract_version = $script:FrameworkCatalogProjectViewContractVersion
        catalog_contract_version = [int]$Catalog.contract_version
        effective_schema_contract_version = [int]$EffectiveSchema.contract_version
        project = [ordered]@{
            project_id = [string]$EffectiveSchema.project.project_id
            framework_id = [string]$EffectiveSchema.project.framework_id
            domain_id = [string]$EffectiveSchema.project.domain_id
        }
        summary = [ordered]@{
            pack_count = $packRows.Count
            selected_pack_count = @($packRows | Where-Object { $_.project_state.selected }).Count
            available_pack_count = @($packRows | Where-Object { $_.project_state.available }).Count
            capability_count = $capabilityRows.Count
            capability_group_count = $groupRows.Count
            selected_capability_group_count = @(
                $groupRows | Where-Object { $_.project_state.selected }
            ).Count
            enabled_capability_group_count = @(
                $groupRows | Where-Object { $_.project_state.enabled }
            ).Count
            selected_capability_count = @(
                $capabilityRows | Where-Object { $_.project_state.selected }
            ).Count
            enabled_capability_count = @(
                $capabilityRows | Where-Object { $_.project_state.enabled }
            ).Count
            available_capability_count = @(
                $capabilityRows | Where-Object { $_.project_state.available }
            ).Count
            deprecated_capability_count = @(
                $capabilityRows | Where-Object { $_.project_state.deprecated }
            ).Count
            planned_capability_count = @(
                $capabilityRows | Where-Object { $_.project_state.planned }
            ).Count
        }
        packs = @($packRows)
        capability_groups = @($groupRows)
        capabilities = @($capabilityRows)
    }
}

function New-KnowledgeFrameworkCatalogProjectViewSelection {
    param(
        [object]$Catalog,
        [object]$ProjectView,
        [object]$LookupKeys,
        [string]$PackId,
        [string]$GroupId,
        [string]$CapabilityId,
        [string[]]$ProviderPackIds = @(),
        [string[]]$Lifecycles = @(),
        [string[]]$Availability = @(),
        [string[]]$Activation = @(),
        [string[]]$Usage = @()
    )

    if ($ProjectView.contract -cne 'framework-catalog-project-view') {
        throw 'Project-view selection requires a FrameworkCatalogProjectView.'
    }
    if (
        [string]::IsNullOrWhiteSpace($PackId) -and
        [string]::IsNullOrWhiteSpace($GroupId) -and
        [string]::IsNullOrWhiteSpace($CapabilityId) -and
        @($ProviderPackIds).Count -eq 0 -and
        @($Lifecycles).Count -eq 0 -and
        @($Availability).Count -eq 0 -and
        @($Activation).Count -eq 0 -and
        @($Usage).Count -eq 0
    ) {
        throw 'Framework-catalog project-view selection requires an ID or capability filter.'
    }
    $groupRows = if ([string]::IsNullOrWhiteSpace($GroupId)) {
        @()
    }
    else {
        @(Resolve-KnowledgeFrameworkCatalogRow @($ProjectView.capability_groups) $GroupId 'capability group' $LookupKeys)
    }
    $groupRows = @($groupRows)
    $packRows = if ([string]::IsNullOrWhiteSpace($PackId)) {
        @()
    }
    else {
        @(Resolve-KnowledgeFrameworkCatalogRow @($ProjectView.packs) $PackId 'pack' $LookupKeys)
    }
    $packRows = @($packRows)
    $normalizedProviderIds = @(
        $ProviderPackIds | ForEach-Object {
            (Resolve-KnowledgeFrameworkCatalogRow @($ProjectView.packs) $_ 'pack' $LookupKeys).id
        }
    )
    $capabilityQueryRequested = (
        -not [string]::IsNullOrWhiteSpace($GroupId) -or
        -not [string]::IsNullOrWhiteSpace($CapabilityId) -or
        @($ProviderPackIds).Count -gt 0 -or @($Lifecycles).Count -gt 0 -or
        @($Availability).Count -gt 0 -or @($Activation).Count -gt 0 -or @($Usage).Count -gt 0
    )
    $capabilityRows = if ([string]::IsNullOrWhiteSpace($CapabilityId)) {
        if ($capabilityQueryRequested) {
            @($ProjectView.capabilities)
        }
        else {
            @()
        }
    }
    else {
        @(
            Resolve-KnowledgeFrameworkCatalogRow `
            @($ProjectView.capabilities) `
                $CapabilityId `
                'capability' `
                $LookupKeys
        )
    }
    $capabilityRows = @($capabilityRows)
    if ($groupRows.Count -gt 0) {
        $groupCapabilityIds = @($groupRows[0].capability_ids)
        $capabilityRows = @($capabilityRows | Where-Object { $groupCapabilityIds -ccontains $_.id })
    }
    $capabilityRows = @(
        Select-FrameworkCatalogCapabilities `
            -Rows $capabilityRows `
            -ProviderPackIds $normalizedProviderIds `
            -Lifecycles $Lifecycles `
            -Availability $Availability `
            -Activation $Activation `
            -Usage $Usage `
            -ProjectView $true
    )
    if ([string]::IsNullOrWhiteSpace($GroupId) -and (
            -not [string]::IsNullOrWhiteSpace($CapabilityId) -or
            @($ProviderPackIds).Count -gt 0 -or
            @($Lifecycles).Count -gt 0 -or
            @($Availability).Count -gt 0 -or
            @($Activation).Count -gt 0 -or
            @($Usage).Count -gt 0
        )) {
        $capabilityIds = @($capabilityRows | ForEach-Object id)
        $groupRows = @($ProjectView.capability_groups | Where-Object {
                @($_.capability_ids | Where-Object { $capabilityIds -ccontains $_ }).Count -gt 0
            })
    }
    return [ordered]@{
        contract = 'framework-catalog-project-view-selection'
        contract_version = $script:FrameworkCatalogProjectViewSelectionContractVersion
        project_view_contract_version = [int]$ProjectView.contract_version
        requested = [ordered]@{
            pack = if ([string]::IsNullOrWhiteSpace($PackId)) {
                $null
            }
            else {
                $PackId
            }
            capability_group = if ([string]::IsNullOrWhiteSpace($GroupId)) {
                $null
            }
            else {
                $GroupId
            }
            capability = if ([string]::IsNullOrWhiteSpace($CapabilityId)) {
                $null
            }
            else {
                $CapabilityId
            }
            filters = [ordered]@{
                provider_pack_ids = @($normalizedProviderIds)
                lifecycles = @($Lifecycles)
                availability = @($Availability)
                activation = @($Activation)
                usage = @($Usage)
            }
        }
        packs = @($packRows)
        capability_groups = @($groupRows)
        capabilities = @($capabilityRows)
    }
}

function New-KnowledgeFrameworkCatalogFailure {
    param(
        [System.Exception]$Exception,
        [string]$Classification = 'catalog-composition',
        [string]$Message
    )

    $diagnosticMessage = if ([string]::IsNullOrWhiteSpace($Message)) {
        $Exception.Message
    }
    else {
        $Message
    }

    return [ordered]@{
        contract = 'framework-catalog-result'
        contract_version = 1
        status = 'failed'
        catalog = $null
        diagnostic = [ordered]@{
            classification = $Classification
            message = $diagnosticMessage
        }
    }
}
