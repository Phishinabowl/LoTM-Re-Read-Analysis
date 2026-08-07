$script:SupportedSchemaPackRegistryVersion = 2
$script:SupportedSchemaPackVersions = @(4, 5)
$script:CurrentSchemaPackVersion = 5
$script:AllowedSchemaPackLifecycles = @("active", "deferred")
$script:AllowedSchemaPackKinds = @("core", "domain", "extension")
$script:AllowedCapabilityLifecycles = @("available", "planned", "deprecated")
$script:AllowedSchemaPackRoles = @('foundation', 'domain', 'bridge', 'extension')
$script:AllowedSchemaPackScopes = @('domain-neutral', 'domain-specific', 'cross-domain')
$script:AllowedSchemaPackMaturities = @('experimental', 'preview', 'stable', 'legacy')
$script:AllowedDocumentationTargetKinds = @('repository-path', 'external-url')
$script:SchemaPackNamespacePattern = "^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$"
$script:LegacyCompoundSemanticNamespaces = @(
    'occurrence.transition-kind-profile'
    'occurrence.outcome-incompatibility-pair'
    'occurrence.rule-effect-kind-target-type'
    'occurrence.rule-kind-effect-kind'
    'occurrence.rule-effect-pattern-scope'
    'occurrence.rule-effect-repetition-policy'
    'occurrence.rule-effect-global-incompatibility-pair'
    'occurrence.rule-effect-same-target-incompatibility-pair'
    'state.change-kind-profile'
)
$script:EffectRepetitionPolicies = @('idempotent', 'accumulating', 'invalid')
$script:EffectPatternScopes = @('owning-pattern', 'external-pattern')
$script:EffectIncompatibilityScopes = @('global', 'same-target')
$script:StateDimensionRequirements = @('required', 'optional', 'forbidden')

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

function Get-SchemaPackStableIdList {
    param([object]$Map, [string]$Key, [string]$Context)

    $values = @(Get-SchemaPackStringList $Map $Key $Context $true)
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($value in $values) {
        Assert-SchemaPackStableId $value "$Context.$Key"
        if (-not $seen.Add($value)) {
            throw "Schema-pack configuration '$Context.$Key' contains duplicate '$value'."
        }
    }
    return @($values)
}

function ConvertTo-SchemaPackPresentationEntries {
    param(
        [System.Collections.IDictionary]$Presentation,
        [string]$Key,
        [string]$Context,
        [bool]$Required
    )

    if (-not $Presentation.Contains($Key)) {
        throw "Schema-pack configuration '$Context.$Key' must be a list."
    }
    $entries = @(Get-ProjectMapValue $Presentation $Key)
    if ($Required -and $entries.Count -eq 0) {
        throw "Schema-pack configuration '$Context.$Key' must be a non-empty list."
    }
    $result = @()
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $entries.Count; $index += 1) {
        $entry = $entries[$index]
        $entryContext = "$Context.$Key[$index]"
        Assert-KnowledgeMapKeys $entry @('id', 'label', 'description') "Schema pack '$entryContext'"
        $entryId = Get-RequiredSchemaPackString $entry 'id' $entryContext
        Assert-SchemaPackStableId $entryId "$entryContext.id"
        if (-not $seen.Add($entryId)) {
            throw "Schema-pack configuration '$Context.$Key' contains duplicate '$entryId'."
        }
        $result += [pscustomobject]@{
            id = $entryId
            label = Get-RequiredSchemaPackString $entry 'label' $entryContext
            description = Get-RequiredSchemaPackString $entry 'description' $entryContext
        }
    }
    return @($result)
}

function ConvertTo-SchemaPackDocumentationEntries {
    param([System.Collections.IDictionary]$Presentation, [string]$Context)

    if (-not $Presentation.Contains('documentation')) {
        throw "Schema-pack configuration '$Context.documentation' must be a list."
    }
    $entries = @(Get-ProjectMapValue $Presentation 'documentation')
    $result = @()
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $entries.Count; $index += 1) {
        $entry = $entries[$index]
        $entryContext = "$Context.documentation[$index]"
        Assert-KnowledgeMapKeys $entry @('id', 'label', 'target_kind', 'target') "Schema pack '$entryContext'"
        $entryId = Get-RequiredSchemaPackString $entry 'id' $entryContext
        Assert-SchemaPackStableId $entryId "$entryContext.id"
        if (-not $seen.Add($entryId)) {
            throw "Schema-pack configuration '$Context.documentation' contains duplicate '$entryId'."
        }
        $targetKind = Get-RequiredSchemaPackString $entry 'target_kind' $entryContext
        if ($script:AllowedDocumentationTargetKinds -cnotcontains $targetKind) {
            throw "Schema-pack configuration '$entryContext.target_kind' is unsupported."
        }
        $target = Get-RequiredSchemaPackString $entry 'target' $entryContext
        if ($targetKind -ceq 'repository-path') {
            $segments = @($target.Replace('\', '/').Split('/'))
            if ([System.IO.Path]::IsPathRooted($target) -or $segments -ccontains '..') {
                throw "Schema-pack configuration '$entryContext.target' must remain repository-relative."
            }
            $target = $target.Replace('\', '/')
        }
        else {
            $uri = $null
            if (
                -not [System.Uri]::TryCreate($target, [System.UriKind]::Absolute, [ref]$uri) -or
                $uri.Scheme -cne 'https' -or
                [string]::IsNullOrWhiteSpace($uri.Host) -or
                -not [string]::IsNullOrEmpty($uri.UserInfo)
            ) {
                throw "Schema-pack configuration '$entryContext.target' must be an absolute HTTPS URL."
            }
        }
        $result += [pscustomobject]@{
            id = $entryId
            label = Get-RequiredSchemaPackString $entry 'label' $entryContext
            target_kind = $targetKind
            target = $target
        }
    }
    return @($result)
}

function ConvertTo-SchemaPackClassification {
    param([System.Collections.IDictionary]$Pack, [string]$PackId)

    $context = "$PackId.classification"
    $classification = Get-ProjectMapValue $Pack 'classification'
    Assert-KnowledgeMapKeys $classification @('family', 'role', 'scope', 'domains', 'bridge_pack_ids') "Schema pack '$context'"
    $family = Get-RequiredSchemaPackString $classification 'family' $context
    Assert-SchemaPackStableId $family "$context.family"
    $role = Get-RequiredSchemaPackString $classification 'role' $context
    if ($script:AllowedSchemaPackRoles -cnotcontains $role) {
        throw "Schema-pack configuration '$context.role' is unsupported."
    }
    $scope = Get-RequiredSchemaPackString $classification 'scope' $context
    if ($script:AllowedSchemaPackScopes -cnotcontains $scope) {
        throw "Schema-pack configuration '$context.scope' is unsupported."
    }
    $domains = @(Get-SchemaPackStableIdList $classification 'domains' $context)
    $bridgePackIds = @(Get-SchemaPackStableIdList $classification 'bridge_pack_ids' $context)
    if ($scope -ceq 'domain-neutral' -and $domains.Count -gt 0) {
        throw "Schema-pack configuration '$context.domains' must be empty for domain-neutral scope."
    }
    if ($scope -ceq 'domain-specific' -and $domains.Count -eq 0) {
        throw "Schema-pack configuration '$context.domains' must identify at least one domain."
    }
    if ($scope -ceq 'cross-domain' -and $domains.Count -lt 2) {
        throw "Schema-pack configuration '$context.domains' must identify at least two domains."
    }
    if ($role -ceq 'bridge') {
        if ($scope -cne 'cross-domain' -or $bridgePackIds.Count -lt 2) {
            throw "Schema-pack configuration '$context' bridges require cross-domain scope and at least two joins."
        }
    }
    elseif ($bridgePackIds.Count -gt 0) {
        throw "Schema-pack configuration '$context.bridge_pack_ids' is only valid for bridges."
    }
    return [pscustomobject]@{
        family = $family
        role = $role
        scope = $scope
        domains = @($domains)
        bridge_pack_ids = @($bridgePackIds)
    }
}

function ConvertTo-SchemaPackPresentation {
    param([System.Collections.IDictionary]$Pack, [string]$PackId)

    $context = "$PackId.presentation"
    $presentation = Get-ProjectMapValue $Pack 'presentation'
    Assert-KnowledgeMapKeys $presentation @(
        'localization_key', 'default_locale', 'label', 'short_description', 'long_description',
        'maturity', 'intended_audiences', 'use_cases', 'examples', 'prerequisites',
        'provided_behaviors', 'exclusions', 'documentation', 'search_keywords', 'visual'
    ) "Schema pack '$context'"
    $localizationKey = Get-RequiredSchemaPackString $presentation 'localization_key' $context
    if ($localizationKey -cnotmatch $script:SchemaPackNamespacePattern) {
        throw "Schema-pack configuration '$context.localization_key' must be a dotted stable key."
    }
    $defaultLocale = Get-RequiredSchemaPackString $presentation 'default_locale' $context
    if ($defaultLocale -cne 'en') {
        throw "Schema-pack configuration '$context.default_locale' must currently be 'en'."
    }
    $maturity = Get-RequiredSchemaPackString $presentation 'maturity' $context
    if ($script:AllowedSchemaPackMaturities -cnotcontains $maturity) {
        throw "Schema-pack configuration '$context.maturity' is unsupported."
    }
    $keywords = @(Get-SchemaPackStringList $presentation 'search_keywords' $context $true)
    $seenKeywords = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($keyword in $keywords) {
        if (-not $seenKeywords.Add($keyword)) {
            throw "Schema-pack configuration '$context.search_keywords' contains duplicates."
        }
    }
    $visual = $null
    if ($presentation.Contains('visual')) {
        $rawVisual = Get-ProjectMapValue $presentation 'visual'
        Assert-KnowledgeMapKeys $rawVisual @('icon_id', 'accent_token') "Schema pack '$context.visual'"
        $iconId = if ($rawVisual.Contains('icon_id')) {
            Get-RequiredSchemaPackString $rawVisual 'icon_id' "$context.visual"
        }
        else {
            $null
        }
        $accentToken = if ($rawVisual.Contains('accent_token')) {
            Get-RequiredSchemaPackString $rawVisual 'accent_token' "$context.visual"
        }
        else {
            $null
        }
        if ($null -eq $iconId -and $null -eq $accentToken) {
            throw "Schema-pack configuration '$context.visual' must declare at least one identifier."
        }
        foreach ($field in @([pscustomobject]@{name='icon_id'
                    value=$iconId
                }, [pscustomobject]@{name='accent_token'
                    value=$accentToken
                })) {
            if ($null -ne $field.value) {
                Assert-SchemaPackStableId $field.value "$context.visual.$($field.name)"
            }
        }
        $visual = [pscustomobject]@{icon_id=$iconId
            accent_token=$accentToken
        }
    }
    return [pscustomobject]@{
        localization_key = $localizationKey
        default_locale = $defaultLocale
        label = Get-RequiredSchemaPackString $presentation 'label' $context
        short_description = Get-RequiredSchemaPackString $presentation 'short_description' $context
        long_description = Get-RequiredSchemaPackString $presentation 'long_description' $context
        maturity = $maturity
        intended_audiences = @(ConvertTo-SchemaPackPresentationEntries $presentation 'intended_audiences' $context $true)
        use_cases = @(ConvertTo-SchemaPackPresentationEntries $presentation 'use_cases' $context $true)
        examples = @(ConvertTo-SchemaPackPresentationEntries $presentation 'examples' $context $false)
        prerequisites = @(ConvertTo-SchemaPackPresentationEntries $presentation 'prerequisites' $context $false)
        provided_behaviors = @(ConvertTo-SchemaPackPresentationEntries $presentation 'provided_behaviors' $context $true)
        exclusions = @(ConvertTo-SchemaPackPresentationEntries $presentation 'exclusions' $context $true)
        documentation = @(ConvertTo-SchemaPackDocumentationEntries $presentation $context)
        search_keywords = @($keywords)
        visual = $visual
    }
}

function ConvertTo-SchemaPackCapabilityPresentation {
    param([System.Collections.IDictionary]$Capability, [string]$Context)

    $presentationContext = "$Context.presentation"
    $presentation = Get-ProjectMapValue $Capability 'presentation'
    Assert-KnowledgeMapKeys $presentation @('localization_key', 'label', 'description') "Schema pack '$presentationContext'"
    $localizationKey = Get-RequiredSchemaPackString $presentation 'localization_key' $presentationContext
    if ($localizationKey -cnotmatch $script:SchemaPackNamespacePattern) {
        throw "Schema-pack configuration '$presentationContext.localization_key' must be a dotted stable key."
    }
    return [pscustomobject]@{
        localization_key = $localizationKey
        label = Get-RequiredSchemaPackString $presentation 'label' $presentationContext
        description = Get-RequiredSchemaPackString $presentation 'description' $presentationContext
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

function Get-SchemaPackSemanticRows {
    param([System.Collections.IDictionary]$Map, [string]$Key, [string]$Context)

    if (-not $Map.Contains($Key)) {
        return @()
    }
    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        throw "Schema-pack configuration '$Context.$Key' must be a list."
    }
    return @($value)
}

function Get-SchemaPackSemanticPairMembers {
    param([System.Collections.IDictionary]$Map, [string]$Context)

    $members = @(Get-SchemaPackStringList $Map 'members' $Context)
    if ($members.Count -ne 2) {
        throw "Schema-pack configuration '$Context.members' must contain exactly two stable IDs."
    }
    foreach ($member in $members) {
        Assert-SchemaPackStableId $member "$Context.members"
    }
    if ($members[0] -ceq $members[1]) {
        throw "Schema-pack configuration '$Context.members' must contain distinct stable IDs."
    }
    return @($members | Sort-Object)
}

function ConvertTo-SchemaPackSemanticDeclarations {
    param([System.Collections.IDictionary]$Pack, [string]$PackId)

    $declarations = Get-ProjectMapValue $Pack 'semantic_declarations'
    if ($null -eq $declarations) {
        $declarations = [ordered]@{}
    }
    if ($declarations -isnot [System.Collections.IDictionary]) {
        throw "Schema-pack configuration '$PackId.semantic_declarations' must be a mapping."
    }
    Assert-KnowledgeMapKeys $declarations @('occurrence', 'state') "Schema pack '$PackId.semantic_declarations'"

    $occurrence = Get-ProjectMapValue $declarations 'occurrence'
    if ($null -eq $occurrence) {
        $occurrence = [ordered]@{}
    }
    if ($occurrence -isnot [System.Collections.IDictionary]) {
        throw "Schema-pack configuration '$PackId.semantic_declarations.occurrence' must be a mapping."
    }
    $occurrenceKeys = @(
        'transition_profiles'
        'outcome_incompatibilities'
        'effect_target_compatibilities'
        'rule_effect_compatibilities'
        'effect_policies'
        'effect_incompatibilities'
    )
    Assert-KnowledgeMapKeys $occurrence $occurrenceKeys "Schema pack '$PackId.semantic_declarations.occurrence'"

    $state = Get-ProjectMapValue $declarations 'state'
    if ($null -eq $state) {
        $state = [ordered]@{}
    }
    if ($state -isnot [System.Collections.IDictionary]) {
        throw "Schema-pack configuration '$PackId.semantic_declarations.state' must be a mapping."
    }
    Assert-KnowledgeMapKeys `
        $state `
    @('change_profiles', 'profiles', 'kind_profiles') `
        "Schema pack '$PackId.semantic_declarations.state'"

    $transitionProfiles = @()
    $rows = @(Get-SchemaPackSemanticRows $occurrence 'transition_profiles' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.occurrence.transition_profiles[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('transition_kind', 'transition_profile') "Schema pack '$context'"
        $kind = Get-RequiredSchemaPackString $row 'transition_kind' $context
        $profile = Get-RequiredSchemaPackString $row 'transition_profile' $context
        Assert-SchemaPackStableId $kind "$context.transition_kind"
        Assert-SchemaPackStableId $profile "$context.transition_profile"
        $transitionProfiles += [pscustomobject]@{transition_kind=$kind
            transition_profile=$profile
        }
    }

    $outcomeIncompatibilities = @()
    $rows = @(Get-SchemaPackSemanticRows $occurrence 'outcome_incompatibilities' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.occurrence.outcome_incompatibilities[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('members') "Schema pack '$context'"
        $outcomeIncompatibilities += [pscustomobject]@{
            members = @(Get-SchemaPackSemanticPairMembers $row $context)
        }
    }

    $targetCompatibilities = @()
    $rows = @(Get-SchemaPackSemanticRows $occurrence 'effect_target_compatibilities' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.occurrence.effect_target_compatibilities[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('effect_kind', 'target_type') "Schema pack '$context'"
        $effectKind = Get-RequiredSchemaPackString $row 'effect_kind' $context
        $targetType = Get-RequiredSchemaPackString $row 'target_type' $context
        Assert-SchemaPackStableId $effectKind "$context.effect_kind"
        Assert-SchemaPackStableId $targetType "$context.target_type"
        $targetCompatibilities += [pscustomobject]@{effect_kind=$effectKind
            target_type=$targetType
        }
    }

    $ruleCompatibilities = @()
    $rows = @(Get-SchemaPackSemanticRows $occurrence 'rule_effect_compatibilities' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.occurrence.rule_effect_compatibilities[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('rule_kind', 'effect_kind') "Schema pack '$context'"
        $ruleKind = Get-RequiredSchemaPackString $row 'rule_kind' $context
        $effectKind = Get-RequiredSchemaPackString $row 'effect_kind' $context
        Assert-SchemaPackStableId $ruleKind "$context.rule_kind"
        Assert-SchemaPackStableId $effectKind "$context.effect_kind"
        $ruleCompatibilities += [pscustomobject]@{rule_kind=$ruleKind
            effect_kind=$effectKind
        }
    }

    $effectPolicies = @()
    $rows = @(Get-SchemaPackSemanticRows $occurrence 'effect_policies' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.occurrence.effect_policies[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('effect_kind', 'repetition_policy', 'recurrence_pattern_scope') "Schema pack '$context'"
        $effectKind = Get-RequiredSchemaPackString $row 'effect_kind' $context
        $policy = Get-RequiredSchemaPackString $row 'repetition_policy' $context
        $scopeValue = Get-ProjectMapValue $row 'recurrence_pattern_scope'
        $scope = if ($null -eq $scopeValue) {
            $null
        }
        else {
            ([string]$scopeValue).Trim()
        }
        Assert-SchemaPackStableId $effectKind "$context.effect_kind"
        if ($script:EffectRepetitionPolicies -cnotcontains $policy) {
            throw "Schema-pack configuration '$context.repetition_policy' is unsupported."
        }
        if ($null -ne $scope -and $script:EffectPatternScopes -cnotcontains $scope) {
            throw "Schema-pack configuration '$context.recurrence_pattern_scope' is unsupported."
        }
        $effectPolicies += [pscustomobject]@{
            effect_kind=$effectKind
            repetition_policy=$policy
            recurrence_pattern_scope=$scope
        }
    }

    $effectIncompatibilities = @()
    $rows = @(Get-SchemaPackSemanticRows $occurrence 'effect_incompatibilities' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.occurrence.effect_incompatibilities[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('members', 'scope') "Schema pack '$context'"
        $scope = Get-RequiredSchemaPackString $row 'scope' $context
        if ($script:EffectIncompatibilityScopes -cnotcontains $scope) {
            throw "Schema-pack configuration '$context.scope' is unsupported."
        }
        $effectIncompatibilities += [pscustomobject]@{
            members=@(Get-SchemaPackSemanticPairMembers $row $context)
            scope=$scope
        }
    }

    $changeProfiles = @()
    $rows = @(Get-SchemaPackSemanticRows $state 'change_profiles' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.state.change_profiles[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('change_kind', 'change_profile') "Schema pack '$context'"
        $kind = Get-RequiredSchemaPackString $row 'change_kind' $context
        $profile = Get-RequiredSchemaPackString $row 'change_profile' $context
        Assert-SchemaPackStableId $kind "$context.change_kind"
        Assert-SchemaPackStableId $profile "$context.change_profile"
        $changeProfiles += [pscustomobject]@{change_kind=$kind
            change_profile=$profile
        }
    }

    $stateProfiles = @()
    $rows = @(Get-SchemaPackSemanticRows $state 'profiles' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.state.profiles[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys `
            $row `
        @('profile_id', 'availability', 'completeness', 'attitude', 'capability') `
            "Schema pack '$context'"
        $profileId = Get-RequiredSchemaPackString $row 'profile_id' $context
        Assert-SchemaPackStableId $profileId "$context.profile_id"
        $requirements = @(
            Get-RequiredSchemaPackString $row 'availability' $context
            Get-RequiredSchemaPackString $row 'completeness' $context
            Get-RequiredSchemaPackString $row 'attitude' $context
            Get-RequiredSchemaPackString $row 'capability' $context
        )
        if (@($requirements | Where-Object { $script:StateDimensionRequirements -cnotcontains $_ }).Count -gt 0) {
            throw "Schema-pack configuration '$context' has an unsupported dimension requirement."
        }
        if ($requirements[0] -cne 'required') {
            throw "Schema-pack configuration '$context.availability' must be 'required'."
        }
        if (@($requirements | Where-Object { $_ -cne 'forbidden' }).Count -eq 0) {
            throw "Schema-pack configuration '$context' must use at least one state dimension."
        }
        $stateProfiles += [pscustomobject]@{
            profile_id=$profileId
            availability=$requirements[0]
            completeness=$requirements[1]
            attitude=$requirements[2]
            capability=$requirements[3]
        }
    }

    $stateKindProfiles = @()
    $rows = @(Get-SchemaPackSemanticRows $state 'kind_profiles' $PackId)
    for ($index = 0; $index -lt $rows.Count; $index += 1) {
        $context = "$PackId.semantic_declarations.state.kind_profiles[$index]"
        $row = $rows[$index]
        Assert-KnowledgeMapKeys $row @('state_kind', 'profile_id') "Schema pack '$context'"
        $stateKind = Get-RequiredSchemaPackString $row 'state_kind' $context
        $profileId = Get-RequiredSchemaPackString $row 'profile_id' $context
        Assert-SchemaPackStableId $stateKind "$context.state_kind"
        Assert-SchemaPackStableId $profileId "$context.profile_id"
        $stateKindProfiles += [pscustomobject]@{state_kind=$stateKind
            profile_id=$profileId
        }
    }

    return [pscustomobject]@{
        transition_profiles=@($transitionProfiles)
        outcome_incompatibilities=@($outcomeIncompatibilities)
        effect_target_compatibilities=@($targetCompatibilities)
        rule_effect_compatibilities=@($ruleCompatibilities)
        effect_policies=@($effectPolicies)
        effect_incompatibilities=@($effectIncompatibilities)
        state_change_profiles=@($changeProfiles)
        state_profiles=@($stateProfiles)
        state_kind_profiles=@($stateKindProfiles)
    }
}

function ConvertTo-SchemaPackConfig {
    param([string]$Path, [string]$ExpectedPackId)

    $pack = ConvertFrom-KnowledgeYamlFile $Path $script:SupportedSchemaPackVersions "schema pack"
    if ($null -eq $pack -or -not ($pack -is [System.Collections.IDictionary])) {
        throw "Schema-pack configuration '$ExpectedPackId' must be a mapping."
    }
    $schemaVersion = Get-RequiredSchemaPackPositiveInteger $pack "schema_version" $ExpectedPackId
    $legacy = $schemaVersion -eq 4
    $packKeys = @(
        "schema_version"
        "pack_id"
        "pack_version"
        "lifecycle"
        "pack_kind"
        "dependencies"
        "capabilities"
        "controlled_values"
        "semantic_declarations"
    )
    $packKeys += if ($legacy) {
        @('label', 'description')
    }
    else {
        @('classification', 'presentation')
    }
    Assert-KnowledgeMapKeys $pack $packKeys "Schema pack '$ExpectedPackId'"
    if ($script:SupportedSchemaPackVersions -notcontains $schemaVersion) {
        throw "Unsupported schema-pack schema_version '$schemaVersion' in $Path."
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
    $classification = if ($legacy) {
        $null
    }
    else {
        ConvertTo-SchemaPackClassification $pack $packId
    }
    $presentation = if ($legacy) {
        $null
    }
    else {
        ConvertTo-SchemaPackPresentation $pack $packId
    }
    $packLabel = if ($legacy) {
        Get-RequiredSchemaPackString $pack 'label' $packId
    }
    else {
        $presentation.label
    }
    $packDescription = if ($legacy) {
        Get-RequiredSchemaPackString $pack 'description' $packId
    }
    else {
        $presentation.short_description
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

    if (-not $pack.Contains('capabilities')) {
        throw "Schema pack '$packId.capabilities' must be a list."
    }
    $rawCapabilityValue = $pack['capabilities']
    if (
        $null -eq $rawCapabilityValue -or
        $rawCapabilityValue -is [string] -or
        $rawCapabilityValue -isnot [System.Collections.IEnumerable]
    ) {
        throw "Schema pack '$packId.capabilities' must be a list."
    }
    $rawCapabilities = @($rawCapabilityValue)
    $capabilities = @()
    $capabilityDefinitions = [ordered]@{}
    $seenCapabilities = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawCapabilities.Count; $index += 1) {
        $rawCapability = $rawCapabilities[$index]
        $context = "$packId.capabilities[$index]"
        if ($rawCapability -is [string]) {
            if (-not $legacy) {
                throw "Schema-pack configuration '$context' must be a capability-definition mapping in schema 5."
            }
            $capabilityId = $rawCapability.Trim()
            $capabilityLifecycle = "available"
            $capabilityLabel = $null
            $capabilityDescription = $null
            $capabilityPresentation = $null
        }
        elseif ($rawCapability -is [System.Collections.IDictionary]) {
            $capabilityKeys = if ($legacy) {
                @('id', 'lifecycle', 'label', 'description')
            }
            else {
                @('id', 'lifecycle', 'presentation')
            }
            Assert-KnowledgeMapKeys $rawCapability $capabilityKeys "Schema pack '$context'"
            $capabilityId = Get-RequiredSchemaPackString $rawCapability "id" $context
            $capabilityLifecycle = Get-RequiredSchemaPackString $rawCapability "lifecycle" $context
            if ($legacy) {
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
                $capabilityPresentation = $null
            }
            else {
                $capabilityPresentation = ConvertTo-SchemaPackCapabilityPresentation $rawCapability $context
                $capabilityLabel = $capabilityPresentation.label
                $capabilityDescription = $capabilityPresentation.description
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
            presentation = $capabilityPresentation
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
        if ($script:LegacyCompoundSemanticNamespaces -ccontains $namespace) {
            throw "Schema-pack controlled-value namespace '$namespace' was replaced by typed semantic declarations."
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
        label = $packLabel
        description = $packDescription
        classification = $classification
        presentation = $presentation
        dependencies = @($dependencies)
        capabilities = @($capabilities)
        capability_definitions = $capabilityDefinitions
        controlled_values = $controlledValues
        controlled_value_definitions = $controlledValueDefinitions
        semantic_declarations = ConvertTo-SchemaPackSemanticDeclarations $pack $packId
    }
}

function Assert-SchemaPackPresentationComposition {
    param(
        [System.Collections.IDictionary]$Packs,
        [string[]]$SelectionOrder
    )

    $versions = @($Packs.Values | ForEach-Object schema_version | Sort-Object -Unique)
    if ($versions.Count -eq 1 -and [int]$versions[0] -eq 4) {
        return
    }
    if ($versions.Count -ne 1 -or [int]$versions[0] -ne $script:CurrentSchemaPackVersion) {
        throw 'Schema-pack composition must not mix legacy schema 4 and presentation schema 5 packs.'
    }

    $localizationOwners = @{}
    $capabilityPresentations = @{}
    foreach ($packId in $SelectionOrder) {
        $pack = $Packs[$packId]
        $classification = $pack.classification
        $presentation = $pack.presentation
        if ($null -eq $classification -or $null -eq $presentation) {
            throw "Schema pack '$packId' is missing schema-5 presentation metadata."
        }
        if ($localizationOwners.ContainsKey($presentation.localization_key)) {
            throw "Schema-pack localization key '$($presentation.localization_key)' is shared by multiple packs."
        }
        $localizationOwners[$presentation.localization_key] = "pack:$packId"

        $dependencyIds = @($pack.dependencies | ForEach-Object pack_id)
        if ($classification.scope -ceq 'domain-neutral') {
            $nonneutral = @(
                $dependencyIds | Where-Object {
                    $null -eq $Packs[$_].classification -or
                    $Packs[$_].classification.scope -cne 'domain-neutral'
                }
            )
            if ($nonneutral.Count -gt 0) {
                throw "Domain-neutral schema pack '$packId' depends on domain-facing pack(s): $($nonneutral -join ', ')."
            }
        }
        elseif ($classification.scope -ceq 'domain-specific') {
            $incompatible = @()
            foreach ($dependencyId in $dependencyIds) {
                $dependencyClassification = $Packs[$dependencyId].classification
                if ($null -eq $dependencyClassification -or $dependencyClassification.scope -ceq 'domain-neutral') {
                    continue
                }
                $overlap = @($classification.domains | Where-Object { @($dependencyClassification.domains) -ccontains $_ })
                if ($overlap.Count -eq 0) {
                    $incompatible += $dependencyId
                }
            }
            if ($incompatible.Count -gt 0) {
                throw "Domain-specific schema pack '$packId' has incompatible dependency scope: $($incompatible -join ', ')."
            }
        }

        if ($classification.role -ceq 'bridge') {
            $bridgeIds = @($classification.bridge_pack_ids)
            $missing = @($bridgeIds | Where-Object { $dependencyIds -cnotcontains $_ })
            if ($missing.Count -gt 0) {
                throw "Bridge schema pack '$packId' joins nondependency pack(s): $($missing -join ', ')."
            }
            $joinable = @(
                $dependencyIds | Where-Object {
                    $null -ne $Packs[$_].classification -and
                    @('foundation', 'domain') -ccontains $Packs[$_].classification.role
                }
            )
            if ((@($bridgeIds | Sort-Object) -join '|') -cne (@($joinable | Sort-Object) -join '|')) {
                throw "Bridge schema pack '$packId' must declare every joined foundation or domain."
            }
            $joinedDomains = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
            foreach ($dependencyId in $bridgeIds) {
                $joined = $Packs[$dependencyId].classification
                $values = if (@($joined.domains).Count -gt 0) {
                    @($joined.domains)
                }
                else {
                    @($joined.family)
                }
                foreach ($value in $values) {
                    $null = $joinedDomains.Add($value)
                }
            }
            if ((@($classification.domains | Sort-Object) -join '|') -cne (@($joinedDomains | Sort-Object) -join '|')) {
                throw "Bridge schema pack '$packId' domains do not match its declared joins."
            }
        }
        elseif ($classification.scope -ceq 'cross-domain') {
            throw "Cross-domain schema pack '$packId' must use the bridge role."
        }

        foreach ($capabilityId in @($pack.capabilities)) {
            $capabilityPresentation = $pack.capability_definitions[$capabilityId].presentation
            if ($null -eq $capabilityPresentation) {
                throw "Schema pack '$packId' capability '$capabilityId' lacks presentation metadata."
            }
            $owner = "capability:$capabilityId"
            if (
                $localizationOwners.ContainsKey($capabilityPresentation.localization_key) -and
                $localizationOwners[$capabilityPresentation.localization_key] -cne $owner
            ) {
                throw "Schema-pack localization key '$($capabilityPresentation.localization_key)' conflicts with another record."
            }
            $localizationOwners[$capabilityPresentation.localization_key] = $owner
            $serialized = $capabilityPresentation | ConvertTo-Json -Compress
            if (
                $capabilityPresentations.ContainsKey($capabilityId) -and
                $capabilityPresentations[$capabilityId] -cne $serialized
            ) {
                throw "Capability '$capabilityId' providers declare conflicting presentation metadata."
            }
            $capabilityPresentations[$capabilityId] = $serialized
        }
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

    Assert-SchemaPackPresentationComposition $packs $selectionOrder

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

    $semantics = Merge-SchemaPackSemanticDeclarations $packs $selectionOrder $controlledValues

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
        transition_profiles = $semantics.transition_profiles
        outcome_incompatibilities = $semantics.outcome_incompatibilities
        effect_target_compatibilities = $semantics.effect_target_compatibilities
        rule_effect_compatibilities = $semantics.rule_effect_compatibilities
        effect_policies = $semantics.effect_policies
        effect_incompatibilities = $semantics.effect_incompatibilities
        state_change_profiles = $semantics.state_change_profiles
        state_profiles = $semantics.state_profiles
        state_kind_profiles = $semantics.state_kind_profiles
        semantic_declaration_owners = $semantics.owners
    }
}

function Merge-SchemaPackSemanticDeclarations {
    param(
        [System.Collections.IDictionary]$Packs,
        [string[]]$SelectionOrder,
        [System.Collections.IDictionary]$ControlledValues
    )

    $owners = @{}
    $transitionProfiles = @{}
    $outcomeIncompatibilities = @{}
    $targetCompatibilities = @{}
    $ruleCompatibilities = @{}
    $effectPolicies = @{}
    $effectIncompatibilities = @{}
    $stateChangeProfiles = @{}
    $stateProfiles = @{}
    $stateKindProfiles = @{}

    function Assert-Atom {
        param([string]$Namespace, [string]$Value, [string]$Context)
        if (@($ControlledValues[$Namespace]) -cnotcontains $Value) {
            throw "Schema-pack semantic declaration '$Context' references unknown '$Namespace`:$Value'."
        }
    }

    function Add-DeclarationOwner {
        param([string]$Key, [string]$PackId)
        if ($owners.ContainsKey($Key)) {
            throw "Schema-pack semantic declaration '$Key' is provided by both '$($owners[$Key])' and '$PackId'."
        }
        $owners[$Key] = $PackId
    }

    foreach ($packId in $SelectionOrder) {
        $declarations = $Packs[$packId].semantic_declarations
        foreach ($declaration in @($declarations.transition_profiles)) {
            $context = "$packId.transition_profiles.$($declaration.transition_kind)"
            Assert-Atom 'occurrence.transition-kind' $declaration.transition_kind $context
            Assert-Atom 'occurrence.transition-profile' $declaration.transition_profile $context
            $key = "transition-profile|$($declaration.transition_kind)"
            Add-DeclarationOwner $key $packId
            $transitionProfiles[$declaration.transition_kind] = $declaration.transition_profile
        }
        foreach ($declaration in @($declarations.outcome_incompatibilities)) {
            foreach ($member in @($declaration.members)) {
                Assert-Atom 'occurrence.outcome-kind' $member "$packId.outcome_incompatibilities"
            }
            $pairKey = "$($declaration.members[0])|$($declaration.members[1])"
            Add-DeclarationOwner "outcome-incompatibility|$pairKey" $packId
            $outcomeIncompatibilities[$pairKey] = $true
        }
        foreach ($declaration in @($declarations.effect_target_compatibilities)) {
            $context = "$packId.effect_target_compatibilities"
            Assert-Atom 'occurrence.rule-effect-kind' $declaration.effect_kind $context
            Assert-Atom 'occurrence.rule-effect-target-type' $declaration.target_type $context
            $pairKey = "$($declaration.effect_kind)|$($declaration.target_type)"
            Add-DeclarationOwner "effect-target-compatibility|$pairKey" $packId
            $targetCompatibilities[$pairKey] = $true
        }
        foreach ($declaration in @($declarations.rule_effect_compatibilities)) {
            $context = "$packId.rule_effect_compatibilities"
            Assert-Atom 'occurrence.rule-kind' $declaration.rule_kind $context
            Assert-Atom 'occurrence.rule-effect-kind' $declaration.effect_kind $context
            $pairKey = "$($declaration.rule_kind)|$($declaration.effect_kind)"
            Add-DeclarationOwner "rule-effect-compatibility|$pairKey" $packId
            $ruleCompatibilities[$pairKey] = $true
        }
        foreach ($declaration in @($declarations.effect_policies)) {
            $context = "$packId.effect_policies.$($declaration.effect_kind)"
            Assert-Atom 'occurrence.rule-effect-kind' $declaration.effect_kind $context
            Add-DeclarationOwner "effect-policy|$($declaration.effect_kind)" $packId
            $effectPolicies[$declaration.effect_kind] = $declaration
        }
        foreach ($declaration in @($declarations.effect_incompatibilities)) {
            foreach ($member in @($declaration.members)) {
                Assert-Atom 'occurrence.rule-effect-kind' $member "$packId.effect_incompatibilities"
            }
            $pairKey = "$($declaration.members[0])|$($declaration.members[1])"
            Add-DeclarationOwner "effect-incompatibility|$pairKey" $packId
            $effectIncompatibilities[$pairKey] = $declaration.scope
        }
        foreach ($declaration in @($declarations.state_change_profiles)) {
            $context = "$packId.change_profiles.$($declaration.change_kind)"
            Assert-Atom 'state.change-kind' $declaration.change_kind $context
            Assert-Atom 'state.change-profile' $declaration.change_profile $context
            Add-DeclarationOwner "state-change-profile|$($declaration.change_kind)" $packId
            $stateChangeProfiles[$declaration.change_kind] = $declaration.change_profile
        }
        foreach ($declaration in @($declarations.state_profiles)) {
            Add-DeclarationOwner "state-profile|$($declaration.profile_id)" $packId
            $stateProfiles[$declaration.profile_id] = $declaration
        }
        foreach ($declaration in @($declarations.state_kind_profiles)) {
            $context = "$packId.kind_profiles.$($declaration.state_kind)"
            Assert-Atom 'state.state-kind' $declaration.state_kind $context
            Add-DeclarationOwner "state-kind-profile|$($declaration.state_kind)" $packId
            $stateKindProfiles[$declaration.state_kind] = $declaration.profile_id
        }
    }

    $transitionKinds = @($ControlledValues['occurrence.transition-kind'] | Where-Object { $null -ne $_ })
    $missing = @($transitionKinds | Where-Object { -not $transitionProfiles.ContainsKey($_) })
    if ($missing.Count -gt 0 -or $transitionProfiles.Count -ne $transitionKinds.Count) {
        throw "Schema-pack transition kinds require exactly one typed profile: $($missing -join ', ')."
    }
    $changeKinds = @($ControlledValues['state.change-kind'] | Where-Object { $null -ne $_ })
    $missing = @($changeKinds | Where-Object { -not $stateChangeProfiles.ContainsKey($_) })
    if ($missing.Count -gt 0 -or $stateChangeProfiles.Count -ne $changeKinds.Count) {
        throw "Schema-pack state change kinds require exactly one typed profile: $($missing -join ', ')."
    }
    $stateKinds = @($ControlledValues['state.state-kind'] | Where-Object { $null -ne $_ })
    $missing = @($stateKinds | Where-Object { -not $stateKindProfiles.ContainsKey($_) })
    if ($missing.Count -gt 0 -or $stateKindProfiles.Count -ne $stateKinds.Count) {
        throw "Schema-pack state kinds require exactly one typed profile: $($missing -join ', ')."
    }
    $unknownProfiles = @(
        $stateKindProfiles.Values |
            Where-Object { -not $stateProfiles.ContainsKey($_) } |
            Sort-Object -Unique
    )
    if ($unknownProfiles.Count -gt 0) {
        throw "Schema-pack state-kind mappings reference unknown profiles: $($unknownProfiles -join ', ')."
    }
    $effectKinds = @($ControlledValues['occurrence.rule-effect-kind'] | Where-Object { $null -ne $_ })
    $missing = @($effectKinds | Where-Object { -not $effectPolicies.ContainsKey($_) })
    if ($missing.Count -gt 0 -or $effectPolicies.Count -ne $effectKinds.Count) {
        throw "Schema-pack effect kinds require exactly one typed policy: $($missing -join ', ')."
    }
    foreach ($effectKind in $effectKinds) {
        $hasTarget = @($targetCompatibilities.Keys | Where-Object { $_.StartsWith("$effectKind|", [StringComparison]::Ordinal) }).Count -gt 0
        if (-not $hasTarget) {
            throw "Schema-pack effect kinds require a typed target compatibility: $effectKind."
        }
        $hasRule = @($ruleCompatibilities.Keys | Where-Object { $_.EndsWith("|$effectKind", [StringComparison]::Ordinal) }).Count -gt 0
        if (-not $hasRule) {
            throw "Schema-pack effect kinds require a typed rule compatibility: $effectKind."
        }
        $targetsRecurrence = $targetCompatibilities.ContainsKey("$effectKind|recurrence-pattern")
        $hasScope = $null -ne $effectPolicies[$effectKind].recurrence_pattern_scope
        if ($targetsRecurrence -ne $hasScope) {
            $requirement = if ($targetsRecurrence) {
                'requires'
            }
            else {
                'must not declare'
            }
            throw "Schema-pack effect kind '$effectKind' $requirement a recurrence-pattern scope."
        }
    }

    return [pscustomobject]@{
        transition_profiles=$transitionProfiles
        outcome_incompatibilities=$outcomeIncompatibilities
        effect_target_compatibilities=$targetCompatibilities
        rule_effect_compatibilities=$ruleCompatibilities
        effect_policies=$effectPolicies
        effect_incompatibilities=$effectIncompatibilities
        state_change_profiles=$stateChangeProfiles
        state_profiles=$stateProfiles
        state_kind_profiles=$stateKindProfiles
        owners=$owners
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
