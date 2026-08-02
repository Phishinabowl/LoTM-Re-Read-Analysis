$script:SupportedSchemaPackRegistryVersion = 2
$script:SupportedSchemaPackVersion = 2
$script:AllowedSchemaPackLifecycles = @("active", "deferred")
$script:AllowedSchemaPackKinds = @("core", "domain", "extension")
$script:AllowedCapabilityLifecycles = @("available", "planned", "deprecated")
$script:SchemaPackNamespacePattern = "^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$"

function Get-RequiredSchemaPackString {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
        throw "Schema-pack configuration '$Context.$Key' must be a non-empty string."
    }
    return ([string]$value).Trim()
}

function Get-RequiredSchemaPackPositiveInteger {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($value -is [bool] -or $value -isnot [int] -or [int]$value -lt 1) {
        throw "Schema-pack configuration '$Context.$Key' must be a positive integer."
    }
    return [int]$value
}

function Get-SchemaPackStringList {
    param([object]$Map, [string]$Key, [string]$Context, [bool]$AllowEmpty = $false)

    if (-not $Map.Contains($Key)) {
        throw "Schema-pack configuration '$Context.$Key' must be a list of strings."
    }
    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        if ($AllowEmpty) {
            return @()
        }
        throw "Schema-pack configuration '$Context.$Key' must be a list of strings."
    }
    $items = @($value)
    if (-not $AllowEmpty -and $items.Count -eq 0) {
        throw "Schema-pack configuration '$Context.$Key' must be a non-empty list."
    }
    foreach ($item in $items) {
        if ($item -isnot [string] -or [string]::IsNullOrWhiteSpace($item)) {
            throw "Schema-pack configuration '$Context.$Key' must be a list of strings."
        }
    }
    return @($items | ForEach-Object { $_.Trim() })
}

function Assert-SchemaPackStableId {
    param([string]$Value, [string]$Context)

    if ($Value -cnotmatch $script:StableProjectIdPattern) {
        throw "Schema-pack configuration '$Context' must be a lowercase kebab-case stable ID: $Value"
    }
}

function Resolve-SchemaPackPath {
    param([object]$ProjectConfig, [string]$Value, [string]$Context)

    if ([System.IO.Path]::IsPathRooted($Value)) {
        throw "Schema-pack configuration '$Context' must be repository-relative: $Value"
    }
    $root = [System.IO.Path]::GetFullPath($ProjectConfig.root)
    $path = [System.IO.Path]::GetFullPath((Join-Path $root $Value))
    if ($path -ne $root -and -not $path.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Schema-pack configuration '$Context' escapes the repository: $Value"
    }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Schema-pack configuration '$Context' file does not exist: $path"
    }
    return $path
}

function ConvertTo-SchemaPackConfig {
    param([string]$Path, [string]$ExpectedPackId)

    $pack = ConvertFrom-KnowledgeYamlFile $Path $script:SupportedSchemaPackVersion "schema pack"
    if ($null -eq $pack -or -not ($pack -is [System.Collections.IDictionary])) {
        throw "Schema-pack configuration '$ExpectedPackId' must be a mapping."
    }
    $packKeys = @(
        "schema_version"
        "pack_id"
        "pack_version"
        "lifecycle"
        "pack_kind"
        "label"
        "description"
        "dependencies"
        "capabilities"
        "controlled_values"
    )
    Assert-KnowledgeMapKeys $pack $packKeys "Schema pack '$ExpectedPackId'"
    $schemaVersion = Get-RequiredSchemaPackPositiveInteger $pack "schema_version" $ExpectedPackId
    if ($schemaVersion -ne $script:SupportedSchemaPackVersion) {
        throw "Unsupported schema-pack schema_version '$schemaVersion' in $Path; expected $($script:SupportedSchemaPackVersion)."
    }
    $packId = Get-RequiredSchemaPackString $pack "pack_id" $ExpectedPackId
    Assert-SchemaPackStableId $packId "$ExpectedPackId.pack_id"
    if ($packId -ne $ExpectedPackId) {
        throw "Schema-pack selection '$ExpectedPackId' loads pack '$packId'."
    }
    $packVersion = Get-RequiredSchemaPackPositiveInteger $pack "pack_version" $packId
    $lifecycle = Get-RequiredSchemaPackString $pack "lifecycle" $packId
    if ($script:AllowedSchemaPackLifecycles -cnotcontains $lifecycle) {
        throw "Schema pack '$packId.lifecycle' must be one of: $($script:AllowedSchemaPackLifecycles -join ', ')."
    }
    $kind = Get-RequiredSchemaPackString $pack "pack_kind" $packId
    if ($script:AllowedSchemaPackKinds -cnotcontains $kind) {
        throw "Schema pack '$packId.pack_kind' must be one of: $($script:AllowedSchemaPackKinds -join ', ')."
    }

    $dependencies = @()
    $seenDependencies = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawDependencies = @(Get-ProjectMapValue $pack "dependencies")
    for ($index = 0; $index -lt $rawDependencies.Count; $index += 1) {
        $context = "$packId.dependencies[$index]"
        $dependency = $rawDependencies[$index]
        Assert-KnowledgeMapKeys $dependency @("pack_id", "minimum_version") "Schema pack '$context'"
        $dependencyId = Get-RequiredSchemaPackString $dependency "pack_id" $context
        Assert-SchemaPackStableId $dependencyId "$context.pack_id"
        if ($dependencyId -eq $packId) {
            throw "Schema pack '$packId' cannot depend on itself."
        }
        if (-not $seenDependencies.Add($dependencyId)) {
            throw "Schema pack '$packId' repeats dependency '$dependencyId'."
        }
        $dependencies += [pscustomobject]@{
            pack_id = $dependencyId
            minimum_version = Get-RequiredSchemaPackPositiveInteger $dependency "minimum_version" $context
        }
    }

    $rawCapabilities = @(Get-ProjectMapValue $pack "capabilities")
    if ($rawCapabilities.Count -eq 0) {
        throw "Schema pack '$packId.capabilities' cannot be empty."
    }
    $capabilities = @()
    $capabilityDefinitions = [ordered]@{}
    $seenCapabilities = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawCapabilities.Count; $index += 1) {
        $rawCapability = $rawCapabilities[$index]
        $context = "$packId.capabilities[$index]"
        if ($rawCapability -is [string]) {
            $capabilityId = $rawCapability.Trim()
            $capabilityLifecycle = "available"
            $capabilityLabel = $null
            $capabilityDescription = $null
        }
        elseif ($rawCapability -is [System.Collections.IDictionary]) {
            Assert-KnowledgeMapKeys $rawCapability @("id", "lifecycle", "label", "description") "Schema pack '$context'"
            $capabilityId = Get-RequiredSchemaPackString $rawCapability "id" $context
            $capabilityLifecycle = Get-RequiredSchemaPackString $rawCapability "lifecycle" $context
            $labelValue = Get-ProjectMapValue $rawCapability "label"
            $descriptionValue = Get-ProjectMapValue $rawCapability "description"
            foreach ($field in @(
                    [pscustomobject]@{ name = "label"
                        value = $labelValue
                    },
                    [pscustomobject]@{ name = "description"
                        value = $descriptionValue
                    }
                )) {
                if ($null -ne $field.value -and [string]::IsNullOrWhiteSpace([string]$field.value)) {
                    throw "Schema-pack configuration '$context.$($field.name)' must be a non-empty string when present."
                }
            }
            $capabilityLabel = if ($null -eq $labelValue) {
                $null
            }
            else {
                ([string]$labelValue).Trim()
            }
            $capabilityDescription = if ($null -eq $descriptionValue) {
                $null
            }
            else {
                ([string]$descriptionValue).Trim()
            }
        }
        else {
            throw "Schema-pack configuration '$context' must be a stable-ID string or capability-definition mapping."
        }
        Assert-SchemaPackStableId $capabilityId $context
        if ($script:AllowedCapabilityLifecycles -cnotcontains $capabilityLifecycle) {
            throw "Schema pack '$context.lifecycle' must be one of: $($script:AllowedCapabilityLifecycles -join ', ')."
        }
        if (-not $seenCapabilities.Add($capabilityId)) {
            throw "Schema pack '$packId.capabilities' contains duplicate '$capabilityId'."
        }
        $capabilities += $capabilityId
        $capabilityDefinitions[$capabilityId] = [pscustomobject]@{
            id = $capabilityId
            lifecycle = $capabilityLifecycle
            label = $capabilityLabel
            description = $capabilityDescription
        }
    }

    $rawControlled = Get-ProjectMapValue $pack "controlled_values"
    if ($null -eq $rawControlled -or -not ($rawControlled -is [System.Collections.IDictionary])) {
        throw "Schema-pack configuration '$packId.controlled_values' must be a mapping."
    }
    $controlledValues = [ordered]@{}
    $controlledValueDefinitions = [ordered]@{}
    foreach ($namespace in $rawControlled.Keys) {
        $context = "$packId.controlled_values.$namespace"
        if ($namespace -cnotmatch $script:SchemaPackNamespacePattern) {
            throw "Schema-pack controlled-value namespace must use dotted lowercase kebab-case: $namespace"
        }
        $values = @($rawControlled[$namespace])
        if ($values.Count -eq 0) {
            throw "Schema-pack configuration '$context' must be a non-empty list."
        }
        $seenValues = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $definitions = [ordered]@{}
        for ($index = 0; $index -lt $values.Count; $index += 1) {
            $rawValue = $values[$index]
            if ($rawValue -is [string]) {
                $valueId = $rawValue.Trim()
                $label = $null
                $description = $null
                $broaderValue = $null
            }
            elseif ($rawValue -is [System.Collections.IDictionary]) {
                $valueContext = "$context[$index]"
                Assert-KnowledgeMapKeys $rawValue @("id", "label", "description", "broader_value") "Schema pack '$valueContext'"
                $valueId = Get-RequiredSchemaPackString $rawValue "id" $valueContext
                $label = Get-RequiredSchemaPackString $rawValue "label" $valueContext
                $descriptionValue = Get-ProjectMapValue $rawValue "description"
                if ($null -ne $descriptionValue -and [string]::IsNullOrWhiteSpace([string]$descriptionValue)) {
                    throw "Schema-pack configuration '$valueContext.description' must be a non-empty string when present."
                }
                $description = if ($null -eq $descriptionValue) {
                    $null
                }
                else {
                    ([string]$descriptionValue).Trim()
                }
                $broaderValueRaw = Get-ProjectMapValue $rawValue "broader_value"
                if ($null -ne $broaderValueRaw -and [string]::IsNullOrWhiteSpace([string]$broaderValueRaw)) {
                    throw "Schema-pack configuration '$valueContext.broader_value' must be a stable ID when present."
                }
                $broaderValue = if ($null -eq $broaderValueRaw) {
                    $null
                }
                else {
                    ([string]$broaderValueRaw).Trim()
                }
            }
            else {
                throw "Schema-pack configuration '$context' must contain stable-ID strings or value-definition mappings."
            }
            Assert-SchemaPackStableId $valueId $context
            if ($null -ne $broaderValue) {
                Assert-SchemaPackStableId $broaderValue "$context.broader_value"
                if ($broaderValue -eq $valueId) {
                    throw "Schema-pack controlled value '$namespace`:$valueId' cannot be broader than itself."
                }
            }
            if (-not $seenValues.Add($valueId)) {
                throw "Schema-pack configuration '$context' contains duplicates."
            }
            $definitions[$valueId] = [pscustomobject]@{
                id = $valueId
                label = $label
                description = $description
                broader_value = $broaderValue
            }
        }
        $controlledValues[$namespace] = @($definitions.Keys)
        $controlledValueDefinitions[$namespace] = $definitions
    }

    return [pscustomobject]@{
        id = $packId
        path = $Path
        schema_version = $schemaVersion
        pack_version = $packVersion
        lifecycle = $lifecycle
        kind = $kind
        label = Get-RequiredSchemaPackString $pack "label" $packId
        description = Get-RequiredSchemaPackString $pack "description" $packId
        dependencies = @($dependencies)
        capabilities = @($capabilities)
        capability_definitions = $capabilityDefinitions
        controlled_values = $controlledValues
        controlled_value_definitions = $controlledValueDefinitions
    }
}

function Get-KnowledgeSchemaPackRegistry {
    param([object]$ProjectConfig)

    Import-ProjectYamlModule
    $registryPath = $ProjectConfig.schema_packs_registry
    $registry = ConvertFrom-KnowledgeYamlFile $registryPath $script:SupportedSchemaPackRegistryVersion "schema-pack registry"
    if ($null -eq $registry -or -not ($registry -is [System.Collections.IDictionary])) {
        throw "Schema-pack registry root must be a mapping: $registryPath"
    }
    Assert-KnowledgeMapKeys $registry @("schema_version", "selected_packs", "capability_activation") "Schema-pack registry root"
    $schemaVersion = Get-RequiredSchemaPackPositiveInteger $registry "schema_version" "root"
    if ($schemaVersion -ne $script:SupportedSchemaPackRegistryVersion) {
        throw "Unsupported schema-pack registry version '$schemaVersion'; expected $($script:SupportedSchemaPackRegistryVersion)."
    }
    $rawSelections = @(Get-ProjectMapValue $registry "selected_packs")
    if ($rawSelections.Count -eq 0) {
        throw "Schema-pack registry 'selected_packs' must be a non-empty list."
    }

    $packs = [ordered]@{}
    $selectionOrder = @()
    for ($index = 0; $index -lt $rawSelections.Count; $index += 1) {
        $context = "selected_packs[$index]"
        $selection = $rawSelections[$index]
        Assert-KnowledgeMapKeys $selection @("pack_id", "path") "Schema-pack registry '$context'"
        $packId = Get-RequiredSchemaPackString $selection "pack_id" $context
        Assert-SchemaPackStableId $packId "$context.pack_id"
        if ($packs.Contains($packId)) {
            throw "Schema-pack registry repeats pack '$packId'."
        }
        $packPath = Resolve-SchemaPackPath $ProjectConfig (Get-RequiredSchemaPackString $selection "path" $context) "$context.path"
        $packs[$packId] = ConvertTo-SchemaPackConfig $packPath $packId
        $selectionOrder += $packId
    }

    $selectedBefore = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($packId in $selectionOrder) {
        $pack = $packs[$packId]
        foreach ($dependency in $pack.dependencies) {
            if (-not $packs.Contains($dependency.pack_id)) {
                throw "Schema pack '$packId' requires unselected pack '$($dependency.pack_id)'."
            }
            if (-not $selectedBefore.Contains($dependency.pack_id)) {
                throw "Schema pack '$packId' must be selected after dependency '$($dependency.pack_id)'."
            }
            if ($packs[$dependency.pack_id].pack_version -lt $dependency.minimum_version) {
                throw "Schema pack '$packId' requires '$($dependency.pack_id)' version $($dependency.minimum_version) or newer; selected version is $($packs[$dependency.pack_id].pack_version)."
            }
        }
        $null = $selectedBefore.Add($packId)
    }

    $declaredCapabilities = @()
    $availableCapabilities = @()
    $capabilityProviders = @{}
    $capabilityDefinitions = @{}
    foreach ($packId in $selectionOrder) {
        foreach ($capability in $packs[$packId].capabilities) {
            if (-not $capabilityProviders.ContainsKey($capability)) {
                $capabilityProviders[$capability] = @()
                $declaredCapabilities += $capability
            }
            $capabilityProviders[$capability] = @($capabilityProviders[$capability]) + $packId
            $definition = $packs[$packId].capability_definitions[$capability]
            $capabilityDefinitions["$packId|$capability"] = $definition
            if ($definition.lifecycle -in @("available", "deprecated") -and $availableCapabilities -cnotcontains $capability) {
                $availableCapabilities += $capability
            }
        }
    }

    $activation = Get-ProjectMapValue $registry "capability_activation"
    if ($null -eq $activation -or -not ($activation -is [System.Collections.IDictionary])) {
        throw "Schema-pack registry 'capability_activation' must be a mapping."
    }
    Assert-KnowledgeMapKeys $activation @("default", "enabled") "Schema-pack registry 'capability_activation'"
    $activationDefault = Get-RequiredSchemaPackString $activation "default" "capability_activation"
    if ($activationDefault -ne "disabled") {
        throw "Schema-pack registry 'capability_activation.default' must be 'disabled' so features remain opt-in."
    }
    $enabledCapabilities = @(Get-SchemaPackStringList $activation "enabled" "capability_activation" $true)
    $seenEnabledCapabilities = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($capability in $enabledCapabilities) {
        Assert-SchemaPackStableId $capability "capability_activation.enabled"
        if (-not $seenEnabledCapabilities.Add($capability)) {
            throw "Schema-pack registry 'capability_activation.enabled' contains duplicates."
        }
        if (-not $capabilityProviders.ContainsKey($capability)) {
            throw "Schema-pack registry enables capability not declared by selected packs: $capability."
        }
        if ($availableCapabilities -cnotcontains $capability) {
            throw "Schema-pack registry enables capability that is not available or deprecated in selected packs: $capability."
        }
    }

    $controlledValues = [ordered]@{}
    $owners = @{}
    $definitions = @{}
    foreach ($packId in $selectionOrder) {
        foreach ($namespace in $packs[$packId].controlled_values.Keys) {
            if (-not $controlledValues.Contains($namespace)) {
                $controlledValues[$namespace] = @()
            }
            foreach ($value in $packs[$packId].controlled_values[$namespace]) {
                $key = "$namespace|$value"
                if ($owners.ContainsKey($key)) {
                    throw "Schema-pack controlled value '$namespace`:$value' is provided by both '$($owners[$key])' and '$packId'."
                }
                $owners[$key] = $packId
                $controlledValues[$namespace] = @($controlledValues[$namespace]) + $value
                $definitions[$key] = $packs[$packId].controlled_value_definitions[$namespace][$value]
            }
        }
    }

    foreach ($key in $definitions.Keys) {
        $definition = $definitions[$key]
        if ($null -ne $definition.broader_value) {
            $namespace = $key.Substring(0, $key.LastIndexOf("|"))
            $broaderKey = "$namespace|$($definition.broader_value)"
            if (-not $owners.ContainsKey($broaderKey)) {
                throw "Schema-pack controlled value '$($key.Replace('|', ':'))' references unknown broader value '$($definition.broader_value)'."
            }
        }
    }
    foreach ($startKey in $definitions.Keys) {
        $active = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $cursor = $startKey
        while ($null -ne $cursor) {
            if (-not $active.Add($cursor)) {
                throw "Schema-pack controlled-value hierarchy contains a cycle at '$($cursor.Replace('|', ':'))'."
            }
            $definition = $definitions[$cursor]
            if ($null -eq $definition.broader_value) {
                $cursor = $null
            }
            else {
                $namespace = $cursor.Substring(0, $cursor.LastIndexOf("|"))
                $cursor = "$namespace|$($definition.broader_value)"
            }
        }
    }

    Assert-SchemaPackOccurrenceSemanticDeclarations $controlledValues

    return [pscustomobject]@{
        path = $registryPath
        schema_version = $schemaVersion
        packs = $packs
        selection_order = @($selectionOrder)
        declared_capabilities = @($declaredCapabilities)
        available_capabilities = @($availableCapabilities)
        enabled_capabilities = @($enabledCapabilities)
        capability_providers = $capabilityProviders
        capability_definitions = $capabilityDefinitions
        controlled_values = $controlledValues
        controlled_value_owners = $owners
        controlled_value_definitions = $definitions
    }
}

function Assert-SchemaPackOccurrenceSemanticDeclarations {
    param([System.Collections.IDictionary]$ControlledValues)

    $effectKinds = @($ControlledValues['occurrence.rule-effect-kind'])
    if ($effectKinds.Count -eq 0) {
        return
    }
    $targetPairs = @($ControlledValues['occurrence.rule-effect-kind-target-type'])
    $recurrenceEffects = @($effectKinds | Where-Object { $targetPairs -ccontains "$_-uses-recurrence-pattern" })
    $scopeValues = @($ControlledValues['occurrence.rule-effect-pattern-scope'])
    foreach ($value in $scopeValues) {
        $matches = @($recurrenceEffects | Where-Object { $value -ceq "$_-uses-owning-pattern" -or $value -ceq "$_-allows-external-pattern" })
        if ($matches.Count -ne 1) {
            throw "Schema-pack occurrence scope declaration '$value' must reference a known recurrence-pattern-capable effect kind."
        }
    }
    foreach ($effect in $recurrenceEffects) {
        $matches = @($scopeValues | Where-Object { $_ -ceq "$effect-uses-owning-pattern" -or $_ -ceq "$effect-allows-external-pattern" })
        if ($matches.Count -ne 1) {
            throw "Schema-pack effect kind '$effect' requires exactly one recurrence-pattern scope declaration."
        }
    }

    $repetitionValues = @($ControlledValues['occurrence.rule-effect-repetition-policy'])
    foreach ($value in $repetitionValues) {
        $matches = @($effectKinds | Where-Object { $value -in @("$_-uses-idempotent", "$_-uses-accumulating", "$_-uses-invalid") })
        if ($matches.Count -ne 1) {
            throw "Schema-pack effect repetition declaration '$value' must reference a known effect kind."
        }
    }
    foreach ($effect in $effectKinds) {
        $matches = @($repetitionValues | Where-Object { $_ -in @("$effect-uses-idempotent", "$effect-uses-accumulating", "$effect-uses-invalid") })
        if ($matches.Count -ne 1) {
            throw "Schema-pack effect kind '$effect' requires exactly one repetition policy declaration."
        }
    }

    $canonical = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $sorted = @($effectKinds | Sort-Object)
    for ($left = 0; $left -lt $sorted.Count; $left++) {
        for ($right = $left + 1; $right -lt $sorted.Count; $right++) {
            $null = $canonical.Add("$($sorted[$left])-with-$($sorted[$right])")
        }
    }
    $global = @($ControlledValues['occurrence.rule-effect-global-incompatibility-pair'] | Where-Object { $null -ne $_ })
    $sameTarget = @($ControlledValues['occurrence.rule-effect-same-target-incompatibility-pair'] | Where-Object { $null -ne $_ })
    $conflictNamespaces = [ordered]@{'occurrence.rule-effect-global-incompatibility-pair'=$global
        'occurrence.rule-effect-same-target-incompatibility-pair'=$sameTarget
    }
    foreach ($namespace in $conflictNamespaces.Keys) {
        foreach ($value in @($conflictNamespaces[$namespace])) {
            if (-not $canonical.Contains([string]$value)) {
                throw "Schema-pack namespace '$namespace' contains a noncanonical or unknown effect pair: $value."
            }
        }
    }
    $duplicates = @($global | Where-Object { $sameTarget -ccontains $_ } | Sort-Object -Unique)
    if ($duplicates.Count -gt 0) {
        throw "Schema-pack effect incompatibility pairs must declare exactly one conflict scope: $($duplicates -join ', ')."
    }
}

function Test-SchemaPackCapabilityAvailable {
    param([object]$SchemaPackRegistry, [string]$Capability)

    return @($SchemaPackRegistry.available_capabilities) -ccontains $Capability
}

function Test-SchemaPackCapabilityDeclared {
    param([object]$SchemaPackRegistry, [string]$Capability)

    return $SchemaPackRegistry.capability_providers.ContainsKey($Capability)
}

function Get-SchemaPackCapabilityDefinitions {
    param([object]$SchemaPackRegistry, [string]$Capability)

    $definitions = @()
    foreach ($packId in @($SchemaPackRegistry.capability_providers[$Capability])) {
        $key = "$packId|$Capability"
        if ($SchemaPackRegistry.capability_definitions.ContainsKey($key)) {
            $definitions += [pscustomobject]@{
                pack_id = $packId
                definition = $SchemaPackRegistry.capability_definitions[$key]
            }
        }
    }
    return @($definitions)
}

function Test-SchemaPackCapabilityEnabled {
    param([object]$SchemaPackRegistry, [string]$Capability)

    return @($SchemaPackRegistry.enabled_capabilities) -ccontains $Capability
}

function Get-SchemaPackAllowedValues {
    param([object]$SchemaPackRegistry, [string]$Namespace)

    if ($SchemaPackRegistry.controlled_values.Contains($Namespace)) {
        return @($SchemaPackRegistry.controlled_values[$Namespace])
    }
    return @()
}

function Test-SchemaPackOwnsValue {
    param([object]$SchemaPackRegistry, [string]$Namespace, [string]$Value)

    return $SchemaPackRegistry.controlled_value_owners.ContainsKey("$Namespace|$Value")
}

function Get-SchemaPackValueDefinition {
    param([object]$SchemaPackRegistry, [string]$Namespace, [string]$Value)

    $key = "$Namespace|$Value"
    if ($SchemaPackRegistry.controlled_value_definitions.ContainsKey($key)) {
        return $SchemaPackRegistry.controlled_value_definitions[$key]
    }
    return $null
}
