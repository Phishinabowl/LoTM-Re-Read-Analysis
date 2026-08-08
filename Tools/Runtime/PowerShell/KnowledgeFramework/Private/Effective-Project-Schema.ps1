$script:EffectiveProjectSchemaContractVersion = 2
$script:EffectiveProjectSchemaSelectionContractVersion = 1

function ConvertTo-KnowledgePortablePath {
    param([AllowNull()][object]$Path)

    if ($null -eq $Path) {
        return $null
    }
    return ([string]$Path).Replace('\', '/')
}

function ConvertTo-KnowledgeRepositoryRelativePath {
    param(
        [AllowNull()][object]$Path,
        [string]$Root
    )

    if ($null -eq $Path) {
        return $null
    }
    $rootPath = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $pathValue = [string]$Path
    $fullPath = if ([System.IO.Path]::IsPathRooted($pathValue)) {
        [System.IO.Path]::GetFullPath($pathValue)
    }
    else {
        [System.IO.Path]::GetFullPath((Join-Path $rootPath $pathValue))
    }
    $prefix = $rootPath + [System.IO.Path]::DirectorySeparatorChar
    if (-not $fullPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Effective-schema path escapes the project root: $fullPath"
    }
    return $fullPath.Substring($prefix.Length).Replace('\', '/')
}

function Get-KnowledgeOrdinalStrings {
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
    $result = [string[]]$normalized
    [Array]::Sort($result, [System.StringComparer]::Ordinal)
    return @($result)
}

function New-KnowledgeEffectiveSchemaDiagnostic {
    param(
        [string]$Severity,
        [string]$Code,
        [string]$Message,
        [AllowNull()][string]$Path,
        [string[]]$RelatedIds = @()
    )

    return [ordered]@{
        severity = $Severity
        code = $Code
        message = $Message
        path = $Path
        related_ids = @(Get-KnowledgeOrdinalStrings $RelatedIds)
    }
}

function Compare-KnowledgeEffectiveSchemaDiagnostic {
    param(
        [object]$Left,
        [object]$Right
    )

    $leftSeverity = if ($Left.severity -eq 'warning') {
        0
    }
    else {
        1
    }
    $rightSeverity = if ($Right.severity -eq 'warning') {
        0
    }
    else {
        1
    }
    if ($leftSeverity -ne $rightSeverity) {
        return $leftSeverity.CompareTo($rightSeverity)
    }
    $comparison = [string]::CompareOrdinal([string]$Left.code, [string]$Right.code)
    if ($comparison -ne 0) {
        return $comparison
    }
    $leftPathRank = if ($null -eq $Left.path) {
        0
    }
    else {
        1
    }
    $rightPathRank = if ($null -eq $Right.path) {
        0
    }
    else {
        1
    }
    if ($leftPathRank -ne $rightPathRank) {
        return $leftPathRank.CompareTo($rightPathRank)
    }
    foreach ($field in @('path', 'message')) {
        $leftValue = if ($null -eq $Left[$field]) {
            ''
        }
        else {
            [string]$Left[$field]
        }
        $rightValue = if ($null -eq $Right[$field]) {
            ''
        }
        else {
            [string]$Right[$field]
        }
        $comparison = [string]::CompareOrdinal($leftValue, $rightValue)
        if ($comparison -ne 0) {
            return $comparison
        }
    }
    return [string]::CompareOrdinal(($Left.related_ids -join "`0"), ($Right.related_ids -join "`0"))
}

function Get-KnowledgeSortedEffectiveSchemaDiagnostic {
    param([object[]]$Diagnostics)

    $result = @($Diagnostics)
    for ($index = 1; $index -lt $result.Count; $index += 1) {
        $current = $result[$index]
        $previous = $index - 1
        while (
            $previous -ge 0 -and
            (Compare-KnowledgeEffectiveSchemaDiagnostic $result[$previous] $current) -gt 0
        ) {
            $result[$previous + 1] = $result[$previous]
            $previous -= 1
        }
        $result[$previous + 1] = $current
    }
    return @($result)
}

function New-KnowledgeEffectiveProjectSchema {
    param(
        [Parameter(Mandatory = $true)][object]$ProjectConfig,
        [Parameter(Mandatory = $true)][object]$SchemaPacks,
        [Parameter(Mandatory = $true)][object]$TaxonomyConfig,
        [Parameter(Mandatory = $true)][object]$ResourceConfig
    )

    $diagnostics = @()
    $packRows = @()
    foreach ($packId in @($SchemaPacks.selection_order)) {
        $pack = $SchemaPacks.packs[$packId]
        $dependencies = @()
        foreach ($dependency in @($pack.dependencies)) {
            $dependencies += [ordered]@{
                pack_id = $dependency.pack_id
                minimum_version = [int]$dependency.minimum_version
                selected_version = [int]$SchemaPacks.packs[$dependency.pack_id].pack_version
                status = 'satisfied'
            }
        }
        $classification = if ($null -eq $pack.classification) {
            $null
        }
        else {
            [ordered]@{
                family = $pack.classification.family
                role = $pack.classification.role
                scope = $pack.classification.scope
                domains = @($pack.classification.domains)
                bridge_pack_ids = @($pack.classification.bridge_pack_ids)
            }
        }
        $presentation = if ($null -eq $pack.presentation) {
            $null
        }
        else {
            [ordered]@{
                localization_key = $pack.presentation.localization_key
                default_locale = $pack.presentation.default_locale
                label = $pack.presentation.label
                short_description = $pack.presentation.short_description
                long_description = $pack.presentation.long_description
                maturity = $pack.presentation.maturity
                intended_audiences = @(
                    $pack.presentation.intended_audiences | ForEach-Object {
                        [ordered]@{ id=$_.id
                            label=$_.label
                            description=$_.description
                        }
                    }
                )
                use_cases = @(
                    $pack.presentation.use_cases | ForEach-Object {
                        [ordered]@{ id=$_.id
                            label=$_.label
                            description=$_.description
                        }
                    }
                )
                examples = @(
                    $pack.presentation.examples | ForEach-Object {
                        [ordered]@{ id=$_.id
                            label=$_.label
                            description=$_.description
                        }
                    }
                )
                prerequisites = @(
                    $pack.presentation.prerequisites | ForEach-Object {
                        [ordered]@{ id=$_.id
                            label=$_.label
                            description=$_.description
                        }
                    }
                )
                provided_behaviors = @(
                    $pack.presentation.provided_behaviors | ForEach-Object {
                        [ordered]@{ id=$_.id
                            label=$_.label
                            description=$_.description
                        }
                    }
                )
                exclusions = @(
                    $pack.presentation.exclusions | ForEach-Object {
                        [ordered]@{ id=$_.id
                            label=$_.label
                            description=$_.description
                        }
                    }
                )
                documentation = @(
                    $pack.presentation.documentation | ForEach-Object {
                        [ordered]@{
                            id = $_.id
                            label = $_.label
                            target_kind = $_.target_kind
                            target = $_.target
                        }
                    }
                )
                search_keywords = @($pack.presentation.search_keywords)
                visual = if ($null -eq $pack.presentation.visual) {
                    $null
                }
                else {
                    [ordered]@{
                        icon_id = $pack.presentation.visual.icon_id
                        accent_token = $pack.presentation.visual.accent_token
                    }
                }
            }
        }
        $packRows += [ordered]@{
            id = $pack.id
            kind = $pack.kind
            lifecycle = $pack.lifecycle
            schema_version = [int]$pack.schema_version
            pack_version = [int]$pack.pack_version
            label = $pack.label
            description = $pack.description
            classification = $classification
            presentation = $presentation
            dependencies = @($dependencies)
        }
        if ($pack.lifecycle -eq 'deferred') {
            $diagnostics += New-KnowledgeEffectiveSchemaDiagnostic `
                'info' `
                'deferred-pack-selected' `
                "Selected pack ``$packId`` is deferred." `
                "packs.$packId.lifecycle" `
            @($packId)
        }
    }

    $capabilityRows = @()
    foreach ($capabilityId in @(Get-KnowledgeOrdinalStrings $SchemaPacks.declared_capabilities)) {
        $providerIds = @($SchemaPacks.capability_providers[$capabilityId])
        $providers = @()
        $lifecycles = @()
        $effectivePresentation = $null
        foreach ($packId in $providerIds) {
            $definition = $SchemaPacks.capability_definitions["$packId|$capabilityId"]
            $lifecycles += $definition.lifecycle
            $providerPresentation = if ($null -eq $definition.presentation) {
                $null
            }
            else {
                [ordered]@{
                    localization_key = $definition.presentation.localization_key
                    label = $definition.presentation.label
                    description = $definition.presentation.description
                }
            }
            if ($null -eq $effectivePresentation -and $null -ne $providerPresentation) {
                $effectivePresentation = $providerPresentation
            }
            $providers += [ordered]@{
                pack_id = $packId
                lifecycle = $definition.lifecycle
                label = $definition.label
                description = $definition.description
                presentation = $providerPresentation
            }
        }
        $effectiveLifecycle = if ($lifecycles -ccontains 'available') {
            'available'
        }
        elseif ($lifecycles -ccontains 'deprecated') {
            'deprecated'
        }
        else {
            'planned'
        }
        $isEnabled = @($SchemaPacks.enabled_capabilities) -ccontains $capabilityId
        $capabilityRows += [ordered]@{
            id = $capabilityId
            declared = $true
            effective_lifecycle = $effectiveLifecycle
            available = $effectiveLifecycle -in @('available', 'deprecated')
            deprecated = $effectiveLifecycle -eq 'deprecated'
            planned = $effectiveLifecycle -eq 'planned'
            enabled = $isEnabled
            disabled = -not $isEnabled
            presentation = $effectivePresentation
            providers = @($providers)
        }
        if ($effectiveLifecycle -eq 'deprecated' -and $isEnabled) {
            $diagnostics += New-KnowledgeEffectiveSchemaDiagnostic `
                'warning' `
                'deprecated-capability-enabled' `
                "Deprecated capability ``$capabilityId`` is enabled." `
                'capability_activation.enabled' `
            @($capabilityId) + $providerIds
        }
        if ($providerIds.Count -gt 1) {
            $diagnostics += New-KnowledgeEffectiveSchemaDiagnostic `
                'info' `
                'multiple-capability-providers' `
                "Capability ``$capabilityId`` has multiple selected providers." `
                "capabilities.$capabilityId.providers" `
            @($capabilityId) + $providerIds
        }
    }

    $namespaceRows = @()
    foreach ($namespace in @(Get-KnowledgeOrdinalStrings $SchemaPacks.controlled_values.Keys)) {
        $values = @()
        foreach ($valueId in @(Get-KnowledgeOrdinalStrings $SchemaPacks.controlled_values[$namespace])) {
            $key = "$namespace|$valueId"
            $definition = $SchemaPacks.controlled_value_definitions[$key]
            $values += [ordered]@{
                id = $valueId
                label = $definition.label
                description = $definition.description
                broader_value_id = $definition.broader_value
                owner_pack_id = $SchemaPacks.controlled_value_owners[$key]
            }
        }
        $namespaceRows += [ordered]@{
            id = $namespace
            values = @($values)
        }
    }

    $contentRoots = @(
        $ProjectConfig.content_roots | ForEach-Object {
            [ordered]@{
                id = $_.id
                relative_path = ConvertTo-KnowledgePortablePath $_.relative_path
                provenance_mode = $_.provenance_mode
                provenance_label = $_.provenance_label
            }
        }
    )
    $contentTypes = @()
    foreach ($id in @(Get-KnowledgeOrdinalStrings $TaxonomyConfig.content_types.Keys)) {
        $item = $TaxonomyConfig.content_types[$id]
        $contentTypes += [ordered]@{
            id = $item.id
            lifecycle = $item.lifecycle
            label = $item.label
            plural_label = $item.plural_label
            canonical_pages_enabled = [bool]$item.canonical_pages_enabled
            content_root_id = $item.content_root_id
            category_policy = $item.category_policy
            path_strategy = $item.path_strategy
            metadata_type_mode = $item.metadata_type_mode
            slug_mode = $item.slug_mode
            default_template = ConvertTo-KnowledgeRepositoryRelativePath $item.default_template $ProjectConfig.root
            qa_page_enabled = [bool]$item.qa_page_enabled
            graph_enabled = [bool]$item.graph_enabled
            metadata_type = $item.metadata_type
            record_slug_prefix = $item.record_slug_prefix
            record_slug_pattern = $item.record_slug_pattern
            record_path = ConvertTo-KnowledgeRepositoryRelativePath $item.record_path $ProjectConfig.root
        }
        if ($item.lifecycle -eq 'deferred') {
            $diagnostics += New-KnowledgeEffectiveSchemaDiagnostic `
                'info' `
                'deferred-content-type' `
                "Content type ``$id`` is deferred." `
                "content_types.$id.lifecycle" `
            @($id)
        }
    }

    $categories = @()
    foreach ($id in @(Get-KnowledgeOrdinalStrings $TaxonomyConfig.categories.Keys)) {
        $item = $TaxonomyConfig.categories[$id]
        $placements = @()
        if ($item.placements.Count -gt 0) {
            foreach ($contentTypeId in @(Get-KnowledgeOrdinalStrings $item.placements.Keys)) {
                $placement = $item.placements[$contentTypeId]
                $placements += [ordered]@{
                    content_type_id = $contentTypeId
                    relative_folder = ConvertTo-KnowledgePortablePath $placement.relative_folder
                    template = ConvertTo-KnowledgeRepositoryRelativePath $placement.template $ProjectConfig.root
                }
            }
        }
        $categories += [ordered]@{
            id = $item.id
            lifecycle = $item.lifecycle
            label = $item.label
            plural_label = $item.plural_label
            canonical_pages_enabled = [bool]$item.canonical_pages_enabled
            metadata_type = $item.metadata_type
            subject_slug_prefix = $item.subject_slug_prefix
            subject_slug_pattern = $item.subject_slug_pattern
            graph_class = $item.graph_class
            placements = @($placements)
        }
        if ($item.lifecycle -eq 'deferred') {
            $diagnostics += New-KnowledgeEffectiveSchemaDiagnostic `
                'info' `
                'deferred-category' `
                "Category ``$id`` is deferred." `
                "categories.$id.lifecycle" `
            @($id)
        }
    }

    $resourceRoots = @(
        $ProjectConfig.resource_roots | ForEach-Object {
            [ordered]@{
                id = $_.id
                relative_path = ConvertTo-KnowledgePortablePath $_.relative_path
                required = [bool]$_.required
            }
        }
    )
    $resourceKinds = @()
    foreach ($id in @(Get-KnowledgeOrdinalStrings $ResourceConfig.kinds.Keys)) {
        $item = $ResourceConfig.kinds[$id]
        $resourceKinds += [ordered]@{
            id = $item.id
            label = $item.label
            plural_label = $item.plural_label
        }
    }
    $resourceTypes = @()
    foreach ($id in @(Get-KnowledgeOrdinalStrings $ResourceConfig.types.Keys)) {
        $item = $ResourceConfig.types[$id]
        $placements = @(
            $item.placements | ForEach-Object {
                [ordered]@{
                    root_id = $_.root_id
                    relative_path = ConvertTo-KnowledgePortablePath $_.relative_path
                    tracking = $_.tracking
                    required = [bool]$_.required
                }
            }
        )
        $resourceTypes += [ordered]@{
            id = $item.id
            lifecycle = $item.lifecycle
            label = $item.label
            plural_label = $item.plural_label
            kind_id = $item.kind_id
            authority = $item.authority
            editor_enabled = [bool]$item.editor_enabled
            placements = @($placements)
        }
        if ($item.lifecycle -eq 'deferred') {
            $diagnostics += New-KnowledgeEffectiveSchemaDiagnostic `
                'info' `
                'deferred-resource-type' `
                "Resource type ``$id`` is deferred." `
                "resource_types.$id.lifecycle" `
            @($id)
        }
    }

    return [ordered]@{
        contract = 'effective-project-schema'
        contract_version = $script:EffectiveProjectSchemaContractVersion
        project = [ordered]@{
            project_id = $ProjectConfig.project_id
            framework_id = $ProjectConfig.framework
            domain_id = $ProjectConfig.domain
            project_manifest_schema_version = [int]$ProjectConfig.schema_version
        }
        registry_schema_versions = @(
            [ordered]@{ registry_id = 'resources'
                schema_version = [int]$ResourceConfig.schema_version
            }
            [ordered]@{ registry_id = 'schema-packs'
                schema_version = [int]$SchemaPacks.schema_version
            }
            [ordered]@{ registry_id = 'taxonomy'
                schema_version = [int]$TaxonomyConfig.schema_version
            }
        )
        packs = @($packRows)
        capabilities = @($capabilityRows)
        controlled_value_namespaces = @($namespaceRows)
        content = [ordered]@{
            roots = @($contentRoots)
            content_types = @($contentTypes)
            categories = @($categories)
        }
        resources = [ordered]@{
            roots = @($resourceRoots)
            kinds = @($resourceKinds)
            types = @($resourceTypes)
        }
        diagnostics = @(Get-KnowledgeSortedEffectiveSchemaDiagnostic $diagnostics)
    }
}

function Get-KnowledgeConsumerEnablementField {
    param([string]$ConsumerId)

    switch ($ConsumerId) {
        'qa' {
            return 'qa_page_enabled'
        }
        'visualization' {
            return 'graph_enabled'
        }
        default {
            throw "Unsupported effective-schema consumer '$ConsumerId'; expected one of: qa, visualization."
        }
    }
}

function Resolve-KnowledgeEffectiveSchemaRow {
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
        throw "Unknown effective-schema $RecordName ID ``$Value``."
    }
    if ($matches.Count -gt 1) {
        $matchIds = @($matches | ForEach-Object id) -join ', '
        throw "Ambiguous effective-schema $RecordName ID ``$Value``; matches: $matchIds."
    }
    return $matches[0]
}

function New-KnowledgeEffectiveSchemaSelection {
    param(
        [object]$Schema,
        [object]$LookupKeys,
        [string]$PackId,
        [string]$CapabilityId
    )

    if ([string]::IsNullOrWhiteSpace($PackId) -and [string]::IsNullOrWhiteSpace($CapabilityId)) {
        throw 'Effective-schema selection requires a pack or capability ID.'
    }
    $selectedPacks = if ([string]::IsNullOrWhiteSpace($PackId)) {
        @()
    }
    else {
        @(Resolve-KnowledgeEffectiveSchemaRow @($Schema.packs) $PackId 'pack' $LookupKeys)
    }
    $selectedCapabilities = if ([string]::IsNullOrWhiteSpace($CapabilityId)) {
        @()
    }
    else {
        @(Resolve-KnowledgeEffectiveSchemaRow @($Schema.capabilities) $CapabilityId 'capability' $LookupKeys)
    }
    return [ordered]@{
        contract = 'effective-project-schema-selection'
        contract_version = $script:EffectiveProjectSchemaSelectionContractVersion
        source_contract = $Schema.contract
        source_contract_version = [int]$Schema.contract_version
        project_id = $Schema.project.project_id
        packs = @($selectedPacks)
        capabilities = @($selectedCapabilities)
    }
}

function Get-KnowledgeConsumerRecordProjection {
    param(
        [object]$Roots,
        [object]$ContentTypes,
        [object]$Categories,
        [object]$Placements
    )

    $records = [ordered]@{}
    foreach ($placementId in @(Get-KnowledgeOrdinalStrings $Placements.Keys)) {
        $placement = $Placements[$placementId]
        $category = $Categories[$placement.category_id]
        $metadataType = [string]$category.metadata_type
        $records[$metadataType.ToLowerInvariant()] = [ordered]@{
            content_type_id = $placement.content_type_id
            content_root_id = $placement.content_root_id
            metadata_type = $metadataType
            label = $category.label
            plural_label = $category.plural_label
            relative_folder = $placement.relative_folder
            relative_file = ''
            export_folder = if ($placement.relative_folder) {
                $placement.relative_folder
            }
            else {
                ([string]$category.plural_label).Replace(' ', '_')
            }
            slug_prefix = $category.subject_slug_prefix
            slug_pattern = $category.subject_slug_pattern
            graph_class = if ($category.graph_class) {
                $category.graph_class
            }
            else {
                $placement.category_id
            }
        }
    }

    foreach ($contentTypeId in @(Get-KnowledgeOrdinalStrings $ContentTypes.Keys)) {
        $contentType = $ContentTypes[$contentTypeId]
        if ($contentType.metadata_type_mode -cne 'fixed') {
            continue
        }
        $rootPath = ([string]$Roots[$contentType.content_root_id].relative_path).Replace('\', '/').Trim('/')
        $relativeFile = ''
        $relativeFolder = ''
        if ($contentType.path_strategy -ceq 'fixed-file') {
            $recordPath = ([string]$contentType.record_path).Replace('\', '/').Trim('/')
            $rootPrefix = "$rootPath/"
            if (-not $recordPath.StartsWith($rootPrefix, [System.StringComparison]::Ordinal)) {
                throw "Consumer content type '$contentTypeId' record path is outside its effective content root."
            }
            $relativeFile = $recordPath.Substring($rootPrefix.Length)
            $relativeFolder = [System.IO.Path]::GetDirectoryName($relativeFile)
            if ($null -eq $relativeFolder) {
                $relativeFolder = ''
            }
            $relativeFolder = $relativeFolder.Replace('\', '/')
        }
        $slugPrefix = [string]$contentType.record_slug_prefix
        $metadataType = [string]$contentType.metadata_type
        $records[$metadataType.ToLowerInvariant()] = [ordered]@{
            content_type_id = $contentTypeId
            content_root_id = $contentType.content_root_id
            metadata_type = $metadataType
            label = $contentType.label
            plural_label = $contentType.plural_label
            relative_folder = $relativeFolder
            relative_file = $relativeFile
            export_folder = Split-Path -Leaf $rootPath
            slug_prefix = $slugPrefix
            slug_pattern = $contentType.record_slug_pattern
            graph_class = if ($slugPrefix) {
                $slugPrefix
            }
            else {
                $contentTypeId
            }
        }
    }
    return $records
}

function New-KnowledgeEffectiveConsumerSchemaProjection {
    param(
        [object]$EffectiveSchema,
        [string]$ConsumerId
    )

    $enablementField = Get-KnowledgeConsumerEnablementField $ConsumerId
    $contentTypes = [ordered]@{}
    foreach ($item in @($EffectiveSchema.content.content_types | Sort-Object id)) {
        $enabled = [bool]$item[$enablementField]
        if ($item.lifecycle -ceq 'active' -and [bool]$item.canonical_pages_enabled -and $enabled) {
            $contentTypes[$item.id] = $item
        }
    }
    $rootIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($item in $contentTypes.Values) {
        [void]$rootIds.Add($item.content_root_id)
    }
    $roots = [ordered]@{}
    foreach ($root in @($EffectiveSchema.content.roots | Sort-Object id)) {
        if ($rootIds.Contains($root.id)) {
            $roots[$root.id] = [ordered]@{
                relative_path = $root.relative_path
                provenance_mode = $root.provenance_mode
                provenance_label = $root.provenance_label
            }
        }
    }

    $contentTypeRows = [ordered]@{}
    foreach ($contentTypeId in $contentTypes.Keys) {
        $item = $contentTypes[$contentTypeId]
        $contentTypeRows[$contentTypeId] = [ordered]@{
            label = $item.label
            plural_label = $item.plural_label
            content_root_id = $item.content_root_id
            category_policy = $item.category_policy
            path_strategy = $item.path_strategy
            metadata_type_mode = $item.metadata_type_mode
            slug_mode = $item.slug_mode
            default_template = $item.default_template
            metadata_type = $item.metadata_type
            record_slug_prefix = $item.record_slug_prefix
            record_slug_pattern = $item.record_slug_pattern
            record_path = $item.record_path
            qa_page_enabled = [bool]$item.qa_page_enabled
            graph_enabled = [bool]$item.graph_enabled
        }
    }

    $categories = [ordered]@{}
    $placements = [ordered]@{}
    $graphClasses = [ordered]@{}
    foreach ($category in @($EffectiveSchema.content.categories | Sort-Object id)) {
        $eligiblePlacements = @(
            $category.placements | Where-Object { $contentTypes.Contains($_.content_type_id) } | Sort-Object content_type_id
        )
        if (
            $category.lifecycle -cne 'active' -or
            -not [bool]$category.canonical_pages_enabled -or
            $eligiblePlacements.Count -eq 0
        ) {
            continue
        }
        $categoryId = $category.id
        $categories[$categoryId] = [ordered]@{
            label = $category.label
            plural_label = $category.plural_label
            metadata_type = $category.metadata_type
            subject_slug_prefix = $category.subject_slug_prefix
            subject_slug_pattern = $category.subject_slug_pattern
            graph_class = $category.graph_class
        }
        if (-not [string]::IsNullOrWhiteSpace($category.graph_class)) {
            $graphClasses[$categoryId] = $category.graph_class
        }
        foreach ($placement in $eligiblePlacements) {
            $contentTypeId = $placement.content_type_id
            $placementId = "$categoryId|$contentTypeId"
            $placements[$placementId] = [ordered]@{
                category_id = $categoryId
                content_type_id = $contentTypeId
                content_root_id = $contentTypes[$contentTypeId].content_root_id
                relative_folder = $placement.relative_folder
                template = $placement.template
            }
        }
    }

    $capabilityState = [ordered]@{}
    foreach ($capability in @($EffectiveSchema.capabilities | Sort-Object id)) {
        $capabilityState[$capability.id] = [ordered]@{
            effective_lifecycle = $capability.effective_lifecycle
            available = [bool]$capability.available
            enabled = [bool]$capability.enabled
        }
    }
    return [ordered]@{
        consumer_id = $ConsumerId
        roots = $roots
        content_types = $contentTypeRows
        categories = $categories
        placements = $placements
        records = Get-KnowledgeConsumerRecordProjection $roots $contentTypeRows $categories $placements
        graph_classes = $graphClasses
        capability_state = $capabilityState
    }
}

function Get-KnowledgeEffectiveProjectSchema {
    param([string]$Root)

    $resolvedRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root
    $project = Get-KnowledgeProjectConfig $resolvedRoot
    $catalogModel = Get-KnowledgeFrameworkCatalogModel $project.root
    return New-KnowledgeEffectiveProjectSchema `
        $project `
    (Get-KnowledgeSchemaPackRegistryFromCatalog $project $catalogModel) `
    (Get-KnowledgeTaxonomyConfig $project) `
    (Get-KnowledgeResourceConfig $project)
}

function Get-KnowledgeEffectiveSchemaErrorCode {
    param([System.Exception]$ErrorRecord)

    $message = $ErrorRecord.Message.ToLowerInvariant()
    if ($message.Contains('requires unselected pack')) {
        return 'missing-pack-dependency'
    }
    if ($message.Contains('must be selected after dependency')) {
        return 'pack-dependency-order'
    }
    if ($message.Contains('requires') -and $message.Contains('version') -and $message.Contains('selected version')) {
        return 'incompatible-pack-dependency'
    }
    if ($message.Contains('provided by both') -or $message.Contains('conflict')) {
        return 'provider-or-ownership-conflict'
    }
    if ($message.Contains('enables capability') -or $message.Contains('capability_activation')) {
        return 'invalid-capability-activation'
    }
    if ($message.Contains('unknown') -or $message.Contains('references')) {
        return 'unknown-reference'
    }
    return 'malformed-configuration'
}

function New-KnowledgeEffectiveSchemaFailure {
    param([System.Exception]$ErrorRecord)

    return [ordered]@{
        contract = 'effective-project-schema-result'
        contract_version = $script:EffectiveProjectSchemaContractVersion
        schema = $null
        diagnostics = @(
            [ordered]@{
                severity = 'error'
                code = Get-KnowledgeEffectiveSchemaErrorCode $ErrorRecord
                message = $ErrorRecord.Message
                path = $null
                related_ids = @()
            }
        )
    }
}
