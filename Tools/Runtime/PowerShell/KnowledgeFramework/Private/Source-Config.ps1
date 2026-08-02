$script:SupportedSourceSchemaVersion = 18
$script:AllowedSourceLifecycles = @("active", "deferred")
$script:AllowedPositionFieldTypes = @("string", "integer", "number", "timestamp", "boolean")
$script:AllowedPriorityOrders = @("ascending", "descending")
$script:AllowedConflictBehaviors = @("flag")
$script:AllowedDeviationOwners = @("derivative-work")
$script:AllowedChapterNumberingModes = @("work-local", "series-global", "not-applicable")
$script:AllowedVolumeCatalogStatuses = @("verified", "pending-verification", "not-applicable")
$script:AllowedOrderingModes = @("total", "partial")
$script:SourceFieldIdPattern = "^[a-z][a-z0-9_]*$"
$script:SourceLanguageTagPattern = "^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$"

function Get-RequiredSourceString {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
        throw "Source registry '$Context.$Key' must be a non-empty string."
    }
    return ([string]$value).Trim()
}

function Get-RequiredSourceBoolean {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($value -isnot [bool]) {
        throw "Source registry '$Context.$Key' must be true or false."
    }
    return [bool]$value
}

function Get-OptionalSourceString {
    param([object]$Map, [string]$Key, [string]$Context)

    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        return $null
    }
    if ($value -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$value)) {
        throw "Source registry '$Context.$Key' must be a non-empty string when present."
    }
    return ([string]$value).Trim()
}

function Get-SourceStringList {
    param([object]$Map, [string]$Key, [string]$Context)

    [object]$value = $null
    if ($Map -is [System.Collections.IDictionary]) {
        if ($Map.Contains($Key)) {
            $value = $Map[$Key]
        }
    }
    else {
        $property = $Map.PSObject.Properties[$Key]
        if ($null -ne $property) {
            $value = $property.Value
        }
    }
    if ($null -eq $value) {
        throw "Source registry '$Context.$Key' must be a list of strings."
    }
    $items = @($value)
    foreach ($item in $items) {
        if ($item -isnot [string] -or [string]::IsNullOrWhiteSpace($item)) {
            throw "Source registry '$Context.$Key' must be a list of strings."
        }
    }
    return @($items | ForEach-Object { $_.Trim() })
}

function Get-SourceStringListAllowEmpty {
    param([object]$Map, [string]$Key, [string]$Context)

    if (-not $Map.Contains($Key)) {
        throw "Source registry '$Context.$Key' must be a list of strings."
    }
    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value) {
        return @()
    }
    return @(Get-SourceStringList $Map $Key $Context)
}

function Test-StableSourceId {
    param([string]$Value, [string]$Context)

    if ($Value -cnotmatch $script:StableProjectIdPattern) {
        throw "Source registry '$Context' must be a lowercase kebab-case stable ID: $Value"
    }
}

function Test-SourceFieldId {
    param([string]$Value, [string]$Context)

    if ($Value -cnotmatch $script:SourceFieldIdPattern) {
        throw "Source registry '$Context' must be a lowercase snake_case field ID: $Value"
    }
}

function Test-SourceLanguageTag {
    param([string]$Value, [string]$Context)

    if ($Value -notmatch $script:SourceLanguageTagPattern) {
        throw "Source registry '$Context' must be a BCP-47-style language tag: $Value"
    }
}

function Assert-SourcePositionValues {
    param(
        [System.Collections.IDictionary]$Values,
        [System.Collections.IDictionary]$Fields,
        [string]$Context
    )
    foreach ($fieldId in $Values.Keys) {
        $value = $Values[$fieldId]
        $fieldType = [string]$Fields[$fieldId]
        $valid = $false
        switch ($fieldType) {
            "string" {
                $valid = $value -is [string] -and -not [string]::IsNullOrWhiteSpace($value)
            }
            "timestamp" {
                $valid = $value -is [string] -and -not [string]::IsNullOrWhiteSpace($value)
            }
            "integer" {
                $valid = $value -isnot [bool] -and ($value -is [int] -or $value -is [long])
            }
            "number" {
                $valid = $value -isnot [bool] -and ($value -is [int] -or $value -is [long] -or $value -is [double] -or $value -is [decimal])
            }
            "boolean" {
                $valid = $value -is [bool]
            }
        }
        if (-not $valid) {
            throw "Source registry '$Context.$fieldId' must match position field type '$fieldType'."
        }
    }
}

function ConvertTo-SourceLocalizedTitles {
    param([object]$Map, [string]$Context, [object]$SchemaPackRegistry)

    $titles = @()
    $seenIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $scopeWindows = @{}
    foreach ($rawTitle in @(Get-ProjectMapValue $Map "localized_titles")) {
        if ($rawTitle -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$Context.localized_titles' entries must be mappings."
        }
        $localizedTitleKeys = @(
            "id"
            "language_tag"
            "territory_ids"
            "title"
            "title_type"
            "status"
            "is_primary"
            "romanization_scheme"
            "valid_window"
        )
        Assert-KnowledgeMapKeys `
            $rawTitle $localizedTitleKeys "Source registry '$Context.localized_titles'"
        $titleId = Get-RequiredSourceString $rawTitle "id" "$Context.localized_titles"
        Test-StableSourceId $titleId "$Context.localized_titles.id"
        if (-not $seenIds.Add($titleId)) {
            throw "Source registry '$Context.localized_titles' repeats ID '$titleId'."
        }
        $languageTag = Get-RequiredSourceString $rawTitle "language_tag" "$Context.localized_titles"
        Test-SourceLanguageTag $languageTag "$Context.localized_titles.language_tag"
        $territoryIds = @(Get-SourceStringListAllowEmpty $rawTitle "territory_ids" "$Context.localized_titles")
        $titleType = Get-RequiredSourceString $rawTitle "title_type" "$Context.localized_titles"
        $status = Get-RequiredSourceString $rawTitle "status" "$Context.localized_titles"
        $romanizationScheme = Get-OptionalSourceString $rawTitle "romanization_scheme" "$Context.localized_titles"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.localized-title-type" @($titleType) "$Context.localized_titles.title_type"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.localized-title-status" @($status) "$Context.localized_titles.status"
        $scope = "$languageTag|$(($territoryIds | Sort-Object) -join ',')|$titleType|$romanizationScheme"
        $validWindow = ConvertTo-KnowledgeTemporalWindow $rawTitle "valid_window" "$Context.localized_titles" $SchemaPackRegistry
        if (-not $scopeWindows.ContainsKey($scope)) {
            $scopeWindows[$scope] = New-Object System.Collections.ArrayList
        }
        foreach ($existingWindow in $scopeWindows[$scope]) {
            if (Test-KnowledgeTemporalWindowsOverlap $validWindow $existingWindow) {
                throw "Source registry '$Context.localized_titles' has overlapping validity windows in one locale scope."
            }
        }
        [void]$scopeWindows[$scope].Add($validWindow)
        $titles += [pscustomobject]@{
            id=$titleId
            language_tag=$languageTag
            territory_ids=@($territoryIds)
            title=Get-RequiredSourceString $rawTitle "title" "$Context.localized_titles"
            title_type=$titleType
            status=$status
            is_primary=Get-RequiredSourceBoolean $rawTitle "is_primary" "$Context.localized_titles"
            romanization_scheme=$romanizationScheme
            valid_window=$validWindow
        }
    }
    return @($titles)
}

function ConvertTo-LabeledSourceRegistry {
    param([object]$RawRegistry, [string]$Context)

    if ($null -eq $RawRegistry -or -not ($RawRegistry -is [System.Collections.IDictionary])) {
        throw "Source registry '$Context' must be a mapping."
    }
    if ($RawRegistry.Count -eq 0) {
        throw "Source registry '$Context' must not be empty."
    }
    $parsed = [ordered]@{}
    foreach ($valueId in $RawRegistry.Keys) {
        $valueContext = "$Context.$valueId"
        Test-StableSourceId $valueId $valueContext
        $definition = $RawRegistry[$valueId]
        if ($null -eq $definition -or -not ($definition -is [System.Collections.IDictionary])) {
            throw "Source registry '$valueContext' must be a mapping."
        }
        Assert-KnowledgeMapKeys $definition @("label") "Source registry '$valueContext'"
        $parsed[$valueId] = [pscustomobject]@{
            id = $valueId
            label = Get-RequiredSourceString $definition "label" $valueContext
        }
    }
    return $parsed
}

function ConvertTo-MediumConfig {
    param(
        [string]$MediumId,
        [object]$RawMedium,
        [object]$MediaModalities,
        [object]$CulturalForms,
        [object]$SchemaPackRegistry
    )

    $context = "mediums.$MediumId"
    Test-StableSourceId $MediumId $context
    if ($null -eq $RawMedium -or -not ($RawMedium -is [System.Collections.IDictionary])) {
        throw "Source registry '$context' must be a mapping."
    }
    Assert-KnowledgeMapKeys $RawMedium @("lifecycle", "label", "plural_label", "modality_ids", "cultural_form_ids", "position") "Source registry '$context'"
    $lifecycle = Get-RequiredSourceString $RawMedium "lifecycle" $context
    if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
        throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
    }
    $modalityIds = @(Get-SourceStringList $RawMedium "modality_ids" $context)
    if ($modalityIds.Count -eq 0) {
        throw "Source registry '$context.modality_ids' must not be empty."
    }
    $unknownModalities = @($modalityIds | Where-Object { -not $MediaModalities.Contains($_) } | Sort-Object -Unique)
    if ($unknownModalities.Count -gt 0) {
        throw "Source registry '$context.modality_ids' references unknown media modalities: $($unknownModalities -join ', ')."
    }
    $culturalFormIds = @(Get-SourceStringListAllowEmpty $RawMedium "cultural_form_ids" $context)
    $unknownCulturalForms = @($culturalFormIds | Where-Object { -not $CulturalForms.Contains($_) } | Sort-Object -Unique)
    if ($unknownCulturalForms.Count -gt 0) {
        throw "Source registry '$context.cultural_form_ids' references unknown cultural forms: $($unknownCulturalForms -join ', ')."
    }
    $incompatibleForms = @($culturalFormIds | Where-Object { $modalityIds -cnotcontains $CulturalForms[$_].modality_id } | Sort-Object -Unique)
    if ($incompatibleForms.Count -gt 0) {
        throw "Source registry '$context.cultural_form_ids' contains forms whose modalities are absent from 'modality_ids': $($incompatibleForms -join ', ')."
    }
    $position = Get-ProjectMapValue $RawMedium "position"
    if ($null -eq $position -or -not ($position -is [System.Collections.IDictionary])) {
        throw "Source registry '$context.position' must be a mapping."
    }
    Assert-KnowledgeMapKeys $position @("fields", "work_scope_field", "structural_validation", "required_fields", "sort_fields", "citation_formats") "Source registry '$context.position'"
    $rawFields = Get-ProjectMapValue $position "fields"
    if ($null -eq $rawFields -or -not ($rawFields -is [System.Collections.IDictionary])) {
        throw "Source registry '$context.position.fields' must be a mapping."
    }
    $fields = [ordered]@{}
    foreach ($fieldId in $rawFields.Keys) {
        Test-SourceFieldId $fieldId "$context.position.fields.$fieldId"
        $fieldType = [string]$rawFields[$fieldId]
        if ($script:AllowedPositionFieldTypes -cnotcontains $fieldType) {
            throw "Source registry '$context.position.fields.$fieldId' must be one of: $($script:AllowedPositionFieldTypes -join ', ')."
        }
        $fields[$fieldId] = $fieldType
    }
    $workScopeField = Get-RequiredSourceString $position "work_scope_field" "$context.position"
    if (-not $fields.Contains($workScopeField) -or $fields[$workScopeField] -ne "string") {
        throw "Source registry '$context.position.work_scope_field' must reference a configured string position field."
    }
    $requiredFields = @(Get-SourceStringList $position "required_fields" "$context.position")
    $sortFields = @(Get-SourceStringList $position "sort_fields" "$context.position")
    if ($requiredFields -cnotcontains $workScopeField) {
        throw "Source registry '$context.position.work_scope_field' must also be listed in required_fields."
    }
    $structuralValidation = $null
    $rawStructuralValidation = Get-ProjectMapValue $position "structural_validation"
    if ($null -ne $rawStructuralValidation) {
        $validationContext = "$context.position.structural_validation"
        if ($rawStructuralValidation -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$validationContext' must be a mapping."
        }
        Assert-KnowledgeMapKeys $rawStructuralValidation @("strategy", "partition_field", "ordinal_field", "segment_field", "ordering_scheme_field") "Source registry '$validationContext'"
        $strategy = Get-RequiredSourceString $rawStructuralValidation "strategy" $validationContext
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.position-structure-strategy" @($strategy) "$validationContext.strategy"
        $partitionField = $null
        $ordinalField = $null
        $segmentField = $null
        $orderingSchemeField = $null
        if ($strategy -eq "work-volume-catalog") {
            $partitionField = Get-RequiredSourceString $rawStructuralValidation "partition_field" $validationContext
            $ordinalField = Get-RequiredSourceString $rawStructuralValidation "ordinal_field" $validationContext
            $configuredFields = @([pscustomobject]@{name="partition_field"
                    id=$partitionField
                    type="integer"
                }, [pscustomobject]@{name="ordinal_field"
                    id=$ordinalField
                    type="integer"
                })
            $orderedField = $ordinalField
            $requiredValidationFields = @($ordinalField)
        }
        elseif ($strategy -eq "work-segment-ordering") {
            $segmentField = Get-RequiredSourceString $rawStructuralValidation "segment_field" $validationContext
            $orderingSchemeField = Get-RequiredSourceString $rawStructuralValidation "ordering_scheme_field" $validationContext
            $configuredFields = @([pscustomobject]@{name="segment_field"
                    id=$segmentField
                    type="string"
                }, [pscustomobject]@{name="ordering_scheme_field"
                    id=$orderingSchemeField
                    type="string"
                })
            $orderedField = $segmentField
            $requiredValidationFields = @($segmentField, $orderingSchemeField)
        }
        else {
            throw "Source registry '$validationContext.strategy' is not implemented by this loader: '$strategy'."
        }
        foreach ($entry in $configuredFields) {
            if (-not $fields.Contains($entry.id) -or $fields[$entry.id] -ne $entry.type) {
                throw "Source registry '$validationContext.$($entry.name)' must reference a configured $($entry.type) position field."
            }
        }
        if ($sortFields -cnotcontains $orderedField) {
            throw "Source registry '$validationContext' ordered field must also be listed in sort_fields."
        }
        if (@($requiredValidationFields | Where-Object { $requiredFields -cnotcontains $_ }).Count -gt 0) {
            throw "Source registry '$validationContext' structural fields must be listed in required_fields."
        }
        $structuralValidation = [pscustomobject]@{strategy=$strategy
            partition_field=$partitionField
            ordinal_field=$ordinalField
            segment_field=$segmentField
            ordering_scheme_field=$orderingSchemeField
        }
    }
    foreach ($entry in @(
            [pscustomobject]@{ name = "required_fields"
                values = $requiredFields
            },
            [pscustomobject]@{ name = "sort_fields"
                values = $sortFields
            }
        )) {
        $unknown = @($entry.values | Where-Object { -not $fields.Contains($_) })
        if ($unknown.Count -gt 0) {
            throw "Source registry '$context.position.$($entry.name)' references unknown field(s): $(($unknown | Sort-Object) -join ', ')."
        }
    }

    $rawFormats = @(Get-ProjectMapValue $position "citation_formats")
    if ($rawFormats.Count -eq 0) {
        throw "Source registry '$context.position.citation_formats' must be a non-empty list."
    }
    $citationFormats = @()
    $seenFormatIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawFormats.Count; $index += 1) {
        $citation = $rawFormats[$index]
        $formatContext = "$context.position.citation_formats[$index]"
        if ($null -eq $citation -or -not ($citation -is [System.Collections.IDictionary])) {
            throw "Source registry '$formatContext' must be a mapping."
        }
        Assert-KnowledgeMapKeys $citation @("id", "template", "required_fields") "Source registry '$formatContext'"
        $formatId = Get-RequiredSourceString $citation "id" $formatContext
        Test-StableSourceId $formatId "$formatContext.id"
        if (-not $seenFormatIds.Add($formatId)) {
            throw "Source registry '$formatContext.id' duplicates '$formatId'."
        }
        $template = Get-RequiredSourceString $citation "template" $formatContext
        $citationRequired = @(Get-SourceStringList $citation "required_fields" $formatContext)
        $placeholders = @([regex]::Matches($template, "\{([a-z][a-z0-9_]*)\}") | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
        $placeholderDiff = @(Compare-Object @($placeholders | Sort-Object) @($citationRequired | Sort-Object))
        if ($placeholderDiff.Count -gt 0) {
            throw "Source registry '$formatContext' template placeholders must match 'required_fields'."
        }
        $unknown = @($placeholders | Where-Object { -not $fields.Contains($_) })
        if ($unknown.Count -gt 0) {
            throw "Source registry '$formatContext.template' references unknown field(s): $(($unknown | Sort-Object) -join ', ')."
        }
        $citationFormats += [pscustomobject]@{
            id = $formatId
            template = $template
            required_fields = @($citationRequired)
        }
    }

    return [pscustomobject]@{
        id = $MediumId
        lifecycle = $lifecycle
        label = Get-RequiredSourceString $RawMedium "label" $context
        plural_label = Get-RequiredSourceString $RawMedium "plural_label" $context
        modality_ids = @($modalityIds)
        cultural_form_ids = @($culturalFormIds)
        fields = $fields
        work_scope_field = $workScopeField
        structural_validation = $structuralValidation
        required_fields = @($requiredFields)
        sort_fields = @($sortFields)
        citation_formats = @($citationFormats)
    }
}

function Assert-SourceSchemaPackValues {
    param(
        [object]$SchemaPackRegistry,
        [string]$Namespace,
        [object[]]$Values,
        [string]$Context
    )

    $allowed = @(Get-SchemaPackAllowedValues $SchemaPackRegistry $Namespace)
    if ($allowed.Count -eq 0) {
        throw "Selected schema packs do not provide controlled namespace '$Namespace' required by '$Context'."
    }
    $unknown = @($Values | Where-Object { $allowed -cnotcontains $_ } | Sort-Object -Unique)
    if ($unknown.Count -gt 0) {
        throw "Source registry '$Context' uses value(s) not provided by the selected schema packs in '$Namespace': $($unknown -join ', ')."
    }
}

function Get-SourceControlledValueAncestors {
    param([object]$SchemaPackRegistry, [string]$Namespace)
    $result = [ordered]@{}
    foreach ($value in @(Get-SchemaPackAllowedValues $SchemaPackRegistry $Namespace)) {
        $lineage = @($value)
        $current = $value
        while ($true) {
            $definition = Get-SchemaPackValueDefinition $SchemaPackRegistry $Namespace $current
            if ($null -eq $definition -or [string]::IsNullOrWhiteSpace([string]$definition.broader_value)) {
                break
            }
            $current = [string]$definition.broader_value
            $lineage += $current
        }
        $result[$value] = @($lineage)
    }
    return $result
}

function Compare-SourcePositions {
    param([object]$Left, [object]$Right, [object]$Medium, [object]$OrderingSchemes = $null, [string]$Context = "position range")
    $validation = $Medium.structural_validation
    foreach ($fieldId in $Medium.sort_fields) {
        if (-not $Left.Contains($fieldId)) {
            continue
        }
        if ($null -ne $validation -and $validation.strategy -eq "work-segment-ordering" -and $fieldId -eq $validation.segment_field) {
            if ($null -eq $OrderingSchemes) {
                throw "Source registry '$Context' requires ordering schemes for segment comparison."
            }
            $schemeField = [string]$validation.ordering_scheme_field
            if ([string]$Left[$schemeField] -ne [string]$Right[$schemeField]) {
                throw "Source registry '$Context' range endpoints must use the same ordering scheme."
            }
            $scheme = $OrderingSchemes[[string]$Left[$schemeField]]
            $leftEntry = @($scheme.entries | Where-Object { $_.target_id -eq [string]$Left[$fieldId] })
            $rightEntry = @($scheme.entries | Where-Object { $_.target_id -eq [string]$Right[$fieldId] })
            $leftValue = [int]$leftEntry[0].ordinal
            $rightValue = [int]$rightEntry[0].ordinal
        }
        else {
            $leftValue = $Left[$fieldId]
            $rightValue = $Right[$fieldId]
            if ($Medium.fields[$fieldId] -eq "timestamp") {
                $leftValue = [datetimeoffset]::Parse([string]$leftValue).UtcDateTime
                $rightValue = [datetimeoffset]::Parse([string]$rightValue).UtcDateTime
            }
        }
        if ($leftValue -lt $rightValue) {
            return -1
        }
        if ($leftValue -gt $rightValue) {
            return 1
        }
    }
    return 0
}

function Assert-SourceStructuralPosition {
    param([object]$Position, [object]$Medium, [object]$Works, [object]$Segments, [object]$OrderingSchemes, [string]$Context)
    $validation = $Medium.structural_validation
    if ($null -eq $validation) {
        return
    }
    $workId = [string]$Position[$Medium.work_scope_field]
    $work = $Works[$workId]
    if ($validation.strategy -eq "work-segment-ordering") {
        $segmentId = [string]$Position[$validation.segment_field]
        $schemeId = [string]$Position[$validation.ordering_scheme_field]
        if (-not $Segments.Contains($segmentId)) {
            throw "Source registry '$Context.$($validation.segment_field)' references unknown segment '$segmentId'."
        }
        if ($Segments[$segmentId].work_id -ne $workId) {
            throw "Source registry '$Context' assigns segment '$segmentId' to the wrong work."
        }
        if (-not $OrderingSchemes.Contains($schemeId)) {
            throw "Source registry '$Context.$($validation.ordering_scheme_field)' references unknown ordering scheme '$schemeId'."
        }
        $scheme = $OrderingSchemes[$schemeId]
        if ($scheme.ordering_mode -ne "total") {
            throw "Source registry '$Context' requires a total ordering scheme."
        }
        if (@($scheme.entries | Where-Object { $_.target_type -eq "segment" -and $_.target_id -eq $segmentId }).Count -ne 1) {
            throw "Source registry '$Context' segment '$segmentId' is absent from ordering scheme '$schemeId'."
        }
        return
    }
    if ($validation.strategy -ne "work-volume-catalog") {
        throw "Source registry '$Context' uses unsupported structural validation strategy '$($validation.strategy)'."
    }
    if ($work.volume_catalog_status -ne "verified") {
        return
    }
    $ordinal = [int]$Position[$validation.ordinal_field]
    $matching = @($work.volumes | Where-Object { $_.chapter_start -le $ordinal -and $_.chapter_end -ge $ordinal })
    if ($matching.Count -eq 0) {
        throw "Source registry '$Context.$($validation.ordinal_field)' falls outside the verified volume catalog for work '$workId'."
    }
    if ($Position.Contains($validation.partition_field) -and @($matching | Where-Object { $_.number -eq [int]$Position[$validation.partition_field] }).Count -eq 0) {
        throw "Source registry '$Context' assigns $($validation.ordinal_field) '$ordinal' to the wrong $($validation.partition_field)."
    }
}

function Assert-SourceEvidencePosition {
    param([object]$Position, [object]$Medium, [object[]]$SourceWorkIds, [object]$Works, [object]$Segments, [object]$OrderingSchemes, [string]$Context)
    if ($null -eq $Position -or $Position -isnot [System.Collections.IDictionary] -or $Position.Count -eq 0) {
        throw "Source registry '$Context' must be a non-empty mapping."
    }
    $unknown = @($Position.Keys | ForEach-Object { [string]$_ } | Where-Object { -not $Medium.fields.Contains($_) })
    if ($unknown.Count -gt 0) {
        throw "Source registry '$Context' references unknown position fields: $($unknown -join ', ')."
    }
    $missing = @($Medium.required_fields | Where-Object { -not $Position.Contains($_) })
    if ($missing.Count -gt 0) {
        throw "Source registry '$Context' omits required position fields: $($missing -join ', ')."
    }
    Assert-SourcePositionValues $Position $Medium.fields $Context
    if ($SourceWorkIds -cnotcontains [string]$Position[$Medium.work_scope_field]) {
        throw "Source registry '$Context' falls outside the evidence source work scope."
    }
    Assert-SourceStructuralPosition $Position $Medium $Works $Segments $OrderingSchemes $Context
}

function Get-SourceTargetWorkScope {
    param([string]$TargetType, [string]$TargetId, [object]$Segments, [object]$ContentGroups, [object]$Manifestations, [object]$ReleaseComponents, [object]$ReleasePackages)
    switch ($TargetType) {
        "work" {
            return @($TargetId)
        }
        "segment" {
            return @([string]$Segments[$TargetId].work_id)
        }
        "content-group" {
            $result = @()
            foreach ($member in $ContentGroups[$TargetId].members) {
                $result += @(Get-SourceTargetWorkScope $member.target_type $member.target_id $Segments $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            }
            return @($result | Sort-Object -Unique)
        }
        "manifestation" {
            return @([string]$Manifestations[$TargetId].work_id)
        }
        "release-component" {
            $component = $ReleaseComponents[$TargetId]
            $result = @($component.segment_ids | ForEach-Object { [string]$Segments[$_].work_id })
            if ($null -ne $component.manifestation_id) {
                $result += @([string]$Manifestations[$component.manifestation_id].work_id)
            }
            return @($result | Sort-Object -Unique)
        }
        "release-package" {
            $package = $ReleasePackages[$TargetId]
            $result = @($package.segment_ids | ForEach-Object { [string]$Segments[$_].work_id })
            $result += @($package.manifestation_ids | ForEach-Object { [string]$Manifestations[$_].work_id })
            foreach ($componentId in $package.release_component_ids) {
                $result += @(Get-SourceTargetWorkScope "release-component" $componentId $Segments $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            }
            return @($result | Sort-Object -Unique)
        }
    }
    return @()
}

function Get-SourceTargetSegmentScope {
    param([string]$TargetType, [string]$TargetId, [object]$ContentGroups, [object]$Manifestations, [object]$ReleaseComponents, [object]$ReleasePackages)
    switch ($TargetType) {
        "segment" {
            return @($TargetId)
        }
        "content-group" {
            $result = @()
            foreach ($member in $ContentGroups[$TargetId].members) {
                $result += @(Get-SourceTargetSegmentScope $member.target_type $member.target_id $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            }
            return @($result | Sort-Object -Unique)
        }
        "manifestation" {
            return @($Manifestations[$TargetId].segment_ids)
        }
        "release-component" {
            return @($ReleaseComponents[$TargetId].segment_ids)
        }
        "release-package" {
            $package = $ReleasePackages[$TargetId]
            $result = @($package.segment_ids)
            foreach ($id in $package.release_component_ids) {
                $result += @($ReleaseComponents[$id].segment_ids)
            }
            foreach ($id in $package.manifestation_ids) {
                $result += @($Manifestations[$id].segment_ids)
            }
            return @($result | Sort-Object -Unique)
        }
    }
    return @()
}

function Get-SourceTargetCompleteWorkScope {
    param([string]$TargetType, [string]$TargetId, [object]$ContentGroups, [object]$Manifestations, [object]$ReleaseComponents, [object]$ReleasePackages)
    switch ($TargetType) {
        "work" {
            return @($TargetId)
        }
        "content-group" {
            $result = @()
            foreach ($member in $ContentGroups[$TargetId].members) {
                $result += @(Get-SourceTargetCompleteWorkScope $member.target_type $member.target_id $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            }
            return @($result | Sort-Object -Unique)
        }
        "manifestation" {
            $item = $Manifestations[$TargetId]
            if ($item.segment_ids.Count -eq 0) {
                return @([string]$item.work_id)
            }
            return @()
        }
        "release-component" {
            $item = $ReleaseComponents[$TargetId]
            if ($item.segment_ids.Count -eq 0 -and $null -ne $item.manifestation_id -and $Manifestations[$item.manifestation_id].segment_ids.Count -eq 0) {
                return @([string]$Manifestations[$item.manifestation_id].work_id)
            }
            return @()
        }
        "release-package" {
            $item = $ReleasePackages[$TargetId]
            $result = @()
            foreach ($id in $item.manifestation_ids) {
                if ($Manifestations[$id].segment_ids.Count -eq 0) {
                    $result += @([string]$Manifestations[$id].work_id)
                }
            }
            foreach ($id in $item.release_component_ids) {
                $result += @(Get-SourceTargetCompleteWorkScope "release-component" $id $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            }
            return @($result | Sort-Object -Unique)
        }
    }
    return @()
}

function Get-SourcePositionSegmentId {
    param([object]$Position, [object]$Medium)
    $validation = $Medium.structural_validation
    if ($null -eq $validation -or $validation.strategy -ne "work-segment-ordering") {
        return $null
    }
    return [string]$Position[$validation.segment_field]
}

function Test-SourceCoverageRangeContainsPositions {
    param([object]$CoverageRange, [object[]]$Positions, [object]$Medium, [object]$OrderingSchemes, [string]$Context)
    $rangeFields = @($CoverageRange.start.Keys | ForEach-Object { [string]$_ })
    foreach ($position in $Positions) {
        if (@($rangeFields | Where-Object { -not $position.Contains($_) }).Count -gt 0) {
            return $false
        }
        $projected = [ordered]@{}
        foreach ($field in $rangeFields) {
            $projected[$field] = $position[$field]
        }
        $startsBeforeCoverage = (
            Compare-SourcePositions `
                $CoverageRange.start $projected $Medium $OrderingSchemes $Context
        ) -gt 0
        $endsAfterCoverage = (
            Compare-SourcePositions `
                $projected $CoverageRange.end $Medium $OrderingSchemes $Context
        ) -gt 0
        if ($startsBeforeCoverage -or $endsAfterCoverage) {
            return $false
        }
    }
    return $true
}

function Assert-SourceLocatorCoverage {
    param(
        [object]$Source,
        [object]$Medium,
        [string]$EvidenceMode,
        [object[]]$Positions,
        [object]$Segments,
        [object]$ContentGroups,
        [object]$Manifestations,
        [object]$ReleaseComponents,
        [object]$ReleasePackages,
        [object]$OrderingSchemes,
        [string]$Context
    )
    $workId = [string]$Positions[0][$Medium.work_scope_field]
    if ($Source.coverage.Count -gt 0) {
        $covered = $false
        foreach ($coverage in $Source.coverage) {
            if ($coverage.medium_id -ne $Medium.id -or $coverage.evidence_modes -cnotcontains $EvidenceMode) {
                continue
            }
            $targetWorks = @(Get-SourceTargetWorkScope $coverage.target_type $coverage.target_id $Segments $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            if ($targetWorks -cnotcontains $workId) {
                continue
            }
            foreach ($range in $coverage.position_ranges) {
                if (Test-SourceCoverageRangeContainsPositions $range $Positions $Medium $OrderingSchemes $Context) {
                    $covered = $true
                    break
                }
            }
            if ($covered) {
                break
            }
            $segmentIds = @($Positions | ForEach-Object { Get-SourcePositionSegmentId $_ $Medium } | Where-Object { $null -ne $_ } | Sort-Object -Unique)
            $targetSegments = @(Get-SourceTargetSegmentScope $coverage.target_type $coverage.target_id $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            $completeWorks = @(Get-SourceTargetCompleteWorkScope $coverage.target_type $coverage.target_id $ContentGroups $Manifestations $ReleaseComponents $ReleasePackages)
            if ($coverage.coverage_type -eq "complete" -and $coverage.position_ranges.Count -eq 0 -and $completeWorks -ccontains $workId) {
                $covered = $true
                break
            }
            if ($segmentIds.Count -eq $Positions.Count -and @($segmentIds | Where-Object { $targetSegments -cnotcontains $_ }).Count -eq 0) {
                $covered = $true
                break
            }
        }
        if (-not $covered) {
            throw "Source registry '$Context' falls outside the evidence source's declared coverage."
        }
    }
    $scopeSets = @()
    if ($null -ne $Source.manifestation_id) {
        $scope = @($Manifestations[$Source.manifestation_id].segment_ids)
        if ($scope.Count -gt 0) {
            $scopeSets += , @($scope)
        }
    }
    foreach ($componentId in $Source.release_component_ids) {
        $scope = @($ReleaseComponents[$componentId].segment_ids)
        if ($scope.Count -gt 0) {
            $scopeSets += , @($scope)
        }
    }
    if ($null -ne $Source.release_package_id) {
        $package = $ReleasePackages[$Source.release_package_id]
        if ($package.segment_ids.Count -gt 0 -and $package.manifestation_ids.Count -eq 0) {
            $scopeSets += , @($package.segment_ids)
        }
    }
    if ($scopeSets.Count -gt 0) {
        $segmentIds = @($Positions | ForEach-Object { Get-SourcePositionSegmentId $_ $Medium } | Where-Object { $null -ne $_ } | Sort-Object -Unique)
        if ($segmentIds.Count -ne $Positions.Count) {
            throw "Source registry '$Context' falls outside the evidence source's segment scope."
        }
        foreach ($scope in $scopeSets) {
            if (@($segmentIds | Where-Object { $scope -cnotcontains $_ }).Count -gt 0) {
                throw "Source registry '$Context' falls outside the evidence source's segment scope."
            }
        }
    }
}

function ConvertTo-SourceIdMap {
    param([object[]]$Records)
    $result = [ordered]@{}
    foreach ($record in @($Records)) {
        if ($null -ne $record) {
            $result[[string]$record.id] = $record
        }
    }
    return $result
}

function ConvertTo-SourceCanonicalJson {
    param([object]$Value)
    if ($null -eq $Value) {
        return "null"
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $members = @($Value.Keys | ForEach-Object { [string]$_ } | Sort-Object | ForEach-Object {
                $keyJson = ConvertTo-Json ([string]$_) -Compress
                $valueJson = ConvertTo-SourceCanonicalJson $Value[$_]
                "$keyJson`:$valueJson"
            })
        return "{$($members -join ',')}"
    }
    if ($Value -is [System.Collections.IList] -and $Value -isnot [string]) {
        $members = @($Value | ForEach-Object { ConvertTo-SourceCanonicalJson $_ })
        return "[$($members -join ',')]"
    }
    return (ConvertTo-Json $Value -Compress)
}

function Test-SourceAuthorityRuleMatch {
    param([object]$Rule, [object]$Source, [string]$EvidenceMode = $null, [object]$EvidenceModeAncestors = $null)
    $applicableModes = @($EvidenceMode)
    if ($null -ne $EvidenceMode -and $null -ne $EvidenceModeAncestors -and $EvidenceModeAncestors.Contains($EvidenceMode)) {
        $applicableModes = @($EvidenceModeAncestors[$EvidenceMode])
    }
    return (($Rule.source_ids.Count -eq 0 -or $Rule.source_ids -ccontains $Source.id) -and
        ($Rule.source_roles.Count -eq 0 -or $Rule.source_roles -ccontains $Source.role) -and
        ($Rule.medium_ids.Count -eq 0 -or $Rule.medium_ids -ccontains $Source.medium_id) -and
        ($Rule.evidence_modes.Count -eq 0 -or @($applicableModes | Where-Object { $Rule.evidence_modes -ccontains $_ }).Count -gt 0))
}

function Resolve-SourceResourceBinding {
    param(
        [object]$ProjectConfig,
        [object]$ResourceConfig,
        [object]$Binding,
        [string]$Context
    )

    if ($null -eq $Binding -or -not ($Binding -is [System.Collections.IDictionary])) {
        throw "Source registry '$Context' must be a mapping."
    }
    $resourceTypeId = Get-RequiredSourceString $Binding "resource_type_id" $Context
    Test-StableSourceId $resourceTypeId "$Context.resource_type_id"
    if (-not $ResourceConfig.types.Contains($resourceTypeId)) {
        throw "Source registry '$Context.resource_type_id' references unknown resource type '$resourceTypeId'."
    }
    $rootId = Get-RequiredSourceString $Binding "root_id" $Context
    Test-StableSourceId $rootId "$Context.root_id"
    $resourceRoot = @($ProjectConfig.resource_roots | Where-Object { $_.id -eq $rootId })
    if ($resourceRoot.Count -ne 1) {
        throw "Source registry '$Context.root_id' references unknown resource root '$rootId'."
    }
    $allowedPlacements = @($ResourceConfig.types[$resourceTypeId].placements | Where-Object { $_.root_id -eq $rootId })
    $allowedRoots = @($allowedPlacements | ForEach-Object { $_.root_id })
    if ($allowedRoots -cnotcontains $rootId) {
        throw "Source registry '$Context' binds resource type '$resourceTypeId' outside its configured roots: $rootId."
    }
    $relativePath = Get-RequiredSourceString $Binding "relative_path" $Context
    if ([System.IO.Path]::IsPathRooted($relativePath)) {
        throw "Source registry '$Context.relative_path' must be relative: $relativePath"
    }
    $rootPath = [System.IO.Path]::GetFullPath($resourceRoot[0].path)
    $path = [System.IO.Path]::GetFullPath((Join-Path $rootPath $relativePath))
    if ($path -ne $rootPath -and -not $path.StartsWith($rootPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Source registry '$Context.relative_path' escapes resource root '$rootId': $relativePath"
    }
    $insidePlacement = $false
    foreach ($placement in $allowedPlacements) {
        $placementPath = [System.IO.Path]::GetFullPath($placement.path)
        if ($path -eq $placementPath -or $path.StartsWith($placementPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
            $insidePlacement = $true
            break
        }
    }
    if (-not $insidePlacement) {
        throw "Source registry '$Context' path is outside every configured '$resourceTypeId' placement beneath '$rootId': $relativePath"
    }
    $required = Get-RequiredSourceBoolean $Binding "required" $Context
    if ($required -and -not (Test-Path -LiteralPath $path)) {
        throw "Source registry '$Context' path does not exist: $path"
    }
    return [pscustomobject]@{
        resource_type_id = $resourceTypeId
        root_id = $rootId
        relative_path = $relativePath
        path = $path
        required = $required
    }
}

function Resolve-KnowledgeSourceId {
    param([object]$SourceRegistry, [string]$Value)

    $normalized = ConvertTo-KnowledgeLookupKey $Value $SourceRegistry.lookup_keys
    foreach ($sourceId in $SourceRegistry.sources.Keys) {
        if (Test-KnowledgeLookupKeysEqual (ConvertTo-KnowledgeLookupKey $sourceId $SourceRegistry.lookup_keys) $normalized) {
            return $sourceId
        }
    }
    if ($SourceRegistry.source_aliases.ContainsKey($normalized)) {
        return $SourceRegistry.source_aliases[$normalized]
    }
    return $null
}

function Resolve-KnowledgeWorkId {
    param([object]$SourceRegistry, [string]$Value)

    $normalized = ConvertTo-KnowledgeLookupKey $Value $SourceRegistry.lookup_keys
    foreach ($workId in $SourceRegistry.works.Keys) {
        if (Test-KnowledgeLookupKeysEqual (ConvertTo-KnowledgeLookupKey $workId $SourceRegistry.lookup_keys) $normalized) {
            return $workId
        }
    }
    if ($SourceRegistry.work_aliases.ContainsKey($normalized)) {
        return $SourceRegistry.work_aliases[$normalized]
    }
    return $null
}

function Get-KnowledgeHighestPrecedenceScopes {
    param([object]$SourceRegistry, [string[]]$ScopeIds)
    if ($null -eq $ScopeIds -or $ScopeIds.Count -eq 0) {
        throw "At least one applicability scope ID is required."
    }
    $scopes = @()
    foreach ($scopeId in $ScopeIds) {
        if (-not $SourceRegistry.applicability_scopes.Contains($scopeId)) {
            throw "Unknown applicability scope ID '$scopeId'."
        }
        $scopes += @($SourceRegistry.applicability_scopes[$scopeId])
    }
    $highest = [int](($scopes | Measure-Object -Property precedence -Maximum).Maximum)
    return @($scopes | Where-Object { $_.precedence -eq $highest })
}

function ConvertTo-KnowledgeApplicabilityInstant {
    param([object]$EffectiveAt)
    return ConvertTo-KnowledgeTemporalInstant $EffectiveAt
}

function Test-KnowledgeSegmentWithin {
    param([object]$SourceRegistry, [string]$SegmentId, [string]$AncestorId)
    $currentId = $SegmentId
    while ($null -ne $currentId) {
        if ($currentId -eq $AncestorId) {
            return $true
        }
        $currentId = $SourceRegistry.segments[$currentId].parent_segment_id
    }
    return $false
}

function Get-KnowledgeApplicabilityTargetWorkIds {
    param([object]$SourceRegistry, [string]$TargetType, [string]$TargetId)
    $result = @()
    switch ($TargetType) {
        "work" {
            $result = @($TargetId)
        }
        "segment" {
            $result = @($SourceRegistry.segments[$TargetId].work_id)
        }
        "content-group" {
            foreach ($member in $SourceRegistry.content_groups[$TargetId].members) {
                $result += @(Get-KnowledgeApplicabilityTargetWorkIds $SourceRegistry $member.target_type $member.target_id)
            }
        }
        "work-relationship" {
            $item = @($SourceRegistry.work_relationships | Where-Object { $_.id -eq $TargetId })[0]
            $result = @($item.source_work_id)
        }
        "adaptation-mapping" {
            $item = @($SourceRegistry.adaptation_mappings | Where-Object { $_.id -eq $TargetId })[0]
            $result = @($item.target_work_id)
        }
        "manifestation" {
            $result = @($SourceRegistry.manifestations[$TargetId].work_id)
        }
        "release-component" {
            $component = $SourceRegistry.release_components[$TargetId]
            foreach ($segmentId in $component.segment_ids) {
                $result += @($SourceRegistry.segments[$segmentId].work_id)
            }
            if ($null -ne $component.manifestation_id) {
                $result += @($SourceRegistry.manifestations[$component.manifestation_id].work_id)
            }
        }
        "release-package" {
            $package = $SourceRegistry.release_packages[$TargetId]
            foreach ($segmentId in $package.segment_ids) {
                $result += @($SourceRegistry.segments[$segmentId].work_id)
            }
            foreach ($manifestationId in $package.manifestation_ids) {
                $result += @($SourceRegistry.manifestations[$manifestationId].work_id)
            }
            foreach ($componentId in $package.release_component_ids) {
                $result += @(Get-KnowledgeApplicabilityTargetWorkIds $SourceRegistry "release-component" $componentId)
            }
        }
    }
    return @($result | Sort-Object -Unique)
}

function Test-KnowledgeApplicabilityTargetWithinSegment {
    param([object]$SourceRegistry, [string]$TargetType, [string]$TargetId, [string]$SegmentId)
    if ($TargetType -eq "segment") {
        return Test-KnowledgeSegmentWithin $SourceRegistry $TargetId $SegmentId
    }
    if ($TargetType -eq "content-group") {
        $members = @($SourceRegistry.content_groups[$TargetId].members)
        if ($members.Count -eq 0) {
            return $false
        }
        foreach ($member in $members) {
            if (-not (Test-KnowledgeApplicabilityTargetWithinSegment $SourceRegistry $member.target_type $member.target_id $SegmentId)) {
                return $false
            }
        }
        return $true
    }
    if ($TargetType -eq "adaptation-mapping") {
        $mapping = @($SourceRegistry.adaptation_mappings | Where-Object { $_.id -eq $TargetId })[0]
        if ($mapping.target_segment_ids.Count -eq 0) {
            return $false
        }
        foreach ($item in $mapping.target_segment_ids) {
            if (-not (Test-KnowledgeSegmentWithin $SourceRegistry $item $SegmentId)) {
                return $false
            }
        }
        return $true
    }
    if ($TargetType -eq "manifestation") {
        $segmentIds = @($SourceRegistry.manifestations[$TargetId].segment_ids)
        if ($segmentIds.Count -eq 0) {
            return $false
        }
        foreach ($item in $segmentIds) {
            if (-not (Test-KnowledgeSegmentWithin $SourceRegistry $item $SegmentId)) {
                return $false
            }
        }
        return $true
    }
    if ($TargetType -eq "release-component") {
        $component = $SourceRegistry.release_components[$TargetId]
        if ($component.segment_ids.Count -gt 0) {
            foreach ($item in $component.segment_ids) {
                if (-not (Test-KnowledgeSegmentWithin $SourceRegistry $item $SegmentId)) {
                    return $false
                }
            }
            return $true
        }
        if ($null -ne $component.manifestation_id) {
            return Test-KnowledgeApplicabilityTargetWithinSegment $SourceRegistry "manifestation" $component.manifestation_id $SegmentId
        }
    }
    return $false
}

function Test-KnowledgeApplicabilityGroupContains {
    param([object]$SourceRegistry, [string]$GroupId, [string]$TargetType, [string]$TargetId, [object]$Active)
    if ($TargetType -eq "content-group") {
        $pending = New-Object System.Collections.ArrayList
        [void]$pending.Add($TargetId)
        $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        while ($pending.Count -gt 0) {
            $candidate = [string]$pending[0]
            $pending.RemoveAt(0)
            if (-not $seen.Add($candidate)) {
                continue
            }
            if (@($SourceRegistry.content_groups[$candidate].parent_group_ids) -ccontains $GroupId) {
                return $true
            }
            foreach ($parentId in $SourceRegistry.content_groups[$candidate].parent_group_ids) {
                [void]$pending.Add($parentId)
            }
        }
    }
    foreach ($member in $SourceRegistry.content_groups[$GroupId].members) {
        if ($null -ne (Get-KnowledgeApplicabilityTargetMatch $SourceRegistry $member.target_type $member.target_id $TargetType $TargetId $Active)) {
            return $true
        }
    }
    return $false
}

function Get-KnowledgeApplicabilityTargetMatch {
    param([object]$SourceRegistry, [string]$ScopeType, [string]$ScopeId, [string]$TargetType, [string]$TargetId, [object]$Active)
    $key = "$ScopeType|$ScopeId|$TargetType|$TargetId"
    if ($Active.Contains($key)) {
        return $null
    }
    if ($ScopeType -eq $TargetType -and $ScopeId -eq $TargetId) {
        return "exact"
    }
    $next = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($item in $Active) {
        [void]$next.Add($item)
    }
    [void]$next.Add($key)
    if ($ScopeType -eq "work") {
        $workIds = @(Get-KnowledgeApplicabilityTargetWorkIds $SourceRegistry $TargetType $TargetId)
        if ($workIds.Count -eq 1 -and $workIds[0] -eq $ScopeId) {
            return "contained"
        }
        return $null
    }
    if ($ScopeType -eq "segment") {
        if (Test-KnowledgeApplicabilityTargetWithinSegment $SourceRegistry $TargetType $TargetId $ScopeId) {
            return "contained"
        }
        return $null
    }
    if ($ScopeType -eq "content-group") {
        if (Test-KnowledgeApplicabilityGroupContains $SourceRegistry $ScopeId $TargetType $TargetId $next) {
            return "contained"
        }
        return $null
    }
    if ($ScopeType -eq "manifestation" -and $TargetType -eq "release-component") {
        if ($SourceRegistry.release_components[$TargetId].manifestation_id -eq $ScopeId) {
            return "contained"
        }
        return $null
    }
    if ($ScopeType -eq "release-package") {
        $package = $SourceRegistry.release_packages[$ScopeId]
        if ($TargetType -eq "manifestation" -and @($package.manifestation_ids) -ccontains $TargetId) {
            return "contained"
        }
        if ($TargetType -eq "release-component" -and @($package.release_component_ids) -ccontains $TargetId) {
            return "contained"
        }
        if ($TargetType -eq "segment" -and @($package.segment_ids) -ccontains $TargetId) {
            return "contained"
        }
    }
    return $null
}

function Get-KnowledgeApplicabilityTerritoryMatch {
    param([object]$SourceRegistry, [object]$Scope, [string]$TerritoryId)
    if ($Scope.territory_ids.Count -eq 0) {
        return "unspecified"
    }
    if ([string]::IsNullOrWhiteSpace($TerritoryId)) {
        return $null
    }
    $currentId = $TerritoryId
    while ($null -ne $currentId) {
        if (@($Scope.territory_ids) -ccontains $currentId) {
            if ($currentId -eq $TerritoryId) {
                return "exact"
            }
            return "ancestor"
        }
        $currentId = $SourceRegistry.territories[$currentId].parent_territory_id
    }
    return $null
}

function Get-KnowledgeApplicabilityTemporalMatch {
    param([object]$Window, [object]$EffectiveInstant)
    return Get-KnowledgeTemporalMatch $Window $EffectiveInstant
}

function Get-KnowledgeApplicabilityDecision {
    param(
        [object]$SourceRegistry,
        [string]$TargetType,
        [string]$TargetId,
        [AllowNull()][AllowEmptyString()][string]$TerritoryId = $null,
        [object]$EffectiveAt = $null
    )
    if ([string]::IsNullOrWhiteSpace($TargetType) -or [string]::IsNullOrWhiteSpace($TargetId)) {
        throw "Applicability target type and ID are required."
    }
    $TargetType = $TargetType.Trim()
    $TargetId = $TargetId.Trim()
    if (-not $PSBoundParameters.ContainsKey("TerritoryId")) {
        $TerritoryId = $null
    }
    elseif ($null -ne $TerritoryId) {
        if ([string]::IsNullOrWhiteSpace($TerritoryId)) {
            throw "Applicability territory ID must not be empty."
        }
        $TerritoryId = $TerritoryId.Trim()
        if (-not $SourceRegistry.territories.Contains($TerritoryId)) {
            throw "Unknown territory '$TerritoryId'."
        }
    }
    $targetExists = $false
    switch ($TargetType) {
        "work" {
            $targetExists = $SourceRegistry.works.Contains($TargetId)
        }
        "segment" {
            $targetExists = $SourceRegistry.segments.Contains($TargetId)
        }
        "content-group" {
            $targetExists = $SourceRegistry.content_groups.Contains($TargetId)
        }
        "work-relationship" {
            $targetExists = @($SourceRegistry.work_relationships | Where-Object { $_.id -eq $TargetId }).Count -gt 0
        }
        "adaptation-mapping" {
            $targetExists = @($SourceRegistry.adaptation_mappings | Where-Object { $_.id -eq $TargetId }).Count -gt 0
        }
        "manifestation" {
            $targetExists = $SourceRegistry.manifestations.Contains($TargetId)
        }
        "release-component" {
            $targetExists = $SourceRegistry.release_components.Contains($TargetId)
        }
        "release-package" {
            $targetExists = $SourceRegistry.release_packages.Contains($TargetId)
        }
        default {
            throw "Unknown applicability target type '$TargetType'."
        }
    }
    if (-not $targetExists) {
        throw "Unknown $TargetType applicability target '$TargetId'."
    }
    $effective = ConvertTo-KnowledgeApplicabilityInstant $EffectiveAt
    $effectiveQuery = $effective
    $matches = @()
    foreach ($scope in $SourceRegistry.applicability_scopes.Values) {
        $active = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $targetMatch = Get-KnowledgeApplicabilityTargetMatch $SourceRegistry $scope.target_type $scope.target_id $TargetType $TargetId $active
        if ($null -eq $targetMatch) {
            continue
        }
        $territoryMatch = Get-KnowledgeApplicabilityTerritoryMatch $SourceRegistry $scope $TerritoryId
        if ($null -eq $territoryMatch) {
            continue
        }
        $temporalMatch = Get-KnowledgeApplicabilityTemporalMatch $scope.effective_window $effectiveQuery
        if ($null -eq $temporalMatch) {
            continue
        }
        $outcome = if (Test-KnowledgeTemporalMatchIndeterminate $temporalMatch) {
            "indeterminate"
        }
        else {
            "applicable"
        }
        $matches += @([pscustomobject]@{scope_id=$scope.id
                outcome=$outcome
                target_match=$targetMatch
                territory_match=$territoryMatch
                temporal_match=$temporalMatch
                precedence=[int]$scope.precedence
            })
    }
    $matches = @($matches | Sort-Object @{Expression="precedence"
            Descending=$true
        }, @{Expression="scope_id"
            Descending=$false
        })
    $applicableMatches = @($matches | Where-Object { $_.outcome -eq "applicable" })
    $highest = if ($applicableMatches.Count -eq 0) {
        $null
    }
    else {
        [int]$applicableMatches[0].precedence
    }
    $winners = if ($null -eq $highest) {
        @()
    }
    else {
        @($applicableMatches | Where-Object { $_.precedence -eq $highest } | ForEach-Object { $_.scope_id })
    }
    return [pscustomobject]@{
        target_type=$TargetType
        target_id=$TargetId
        territory_id=if ([string]::IsNullOrWhiteSpace($TerritoryId)) {
            $null
        }
        else {
            $TerritoryId
        }
        effective_at=if ($null -eq $effective) {
            $null
        }
        else {
            $effective.label
        }
        matching_scope_ids=@($applicableMatches | ForEach-Object { $_.scope_id })
        indeterminate_scope_ids=@($matches | Where-Object { $_.outcome -eq "indeterminate" } | ForEach-Object { $_.scope_id })
        winning_scope_ids=@($winners)
        highest_precedence=$highest
        ambiguous=($winners.Count -gt 1)
        matches=@($matches)
    }
}

function ConvertTo-RelationshipTypeRegistry {
    param([object]$RawTypes, [string]$Context)

    if ($null -eq $RawTypes -or -not ($RawTypes -is [System.Collections.IDictionary])) {
        throw "Source registry '$Context' must be a mapping."
    }
    $types = [ordered]@{}
    foreach ($typeId in $RawTypes.Keys) {
        $typeContext = "$Context.$typeId"
        Test-StableSourceId $typeId $typeContext
        $rawType = $RawTypes[$typeId]
        if ($null -eq $rawType -or -not ($rawType -is [System.Collections.IDictionary])) {
            throw "Source registry '$typeContext' must be a mapping."
        }
        Assert-KnowledgeMapKeys $rawType @("label", "inverse_type", "symmetric") "Source registry '$typeContext'"
        $inverseType = Get-RequiredSourceString $rawType "inverse_type" $typeContext
        Test-StableSourceId $inverseType "$typeContext.inverse_type"
        $types[$typeId] = [pscustomobject]@{
            id = $typeId
            label = Get-RequiredSourceString $rawType "label" $typeContext
            inverse_type = $inverseType
            symmetric = Get-RequiredSourceBoolean $rawType "symmetric" $typeContext
        }
    }
    foreach ($type in $types.Values) {
        if (-not $types.Contains($type.inverse_type)) {
            throw "Source registry '$Context.$($type.id).inverse_type' references unknown type '$($type.inverse_type)'."
        }
        $inverse = $types[$type.inverse_type]
        if ($inverse.inverse_type -ne $type.id) {
            throw "Source registry relationship types '$($type.id)' and '$($inverse.id)' do not define reciprocal inverses."
        }
        if ($type.symmetric -ne ($type.id -eq $type.inverse_type)) {
            throw "Source registry relationship type '$($type.id)' has inconsistent symmetric and inverse settings."
        }
    }
    return $types
}

function Assert-SourceRegistryShapes {
    param([object]$Registry)

    $schemas = [ordered]@{
        work_group_types=@("label", "ordered")
        work_groups=@("lifecycle", "label", "short_label", "group_type", "parent_group_id")
        continuities=@("lifecycle", "label", "short_label", "continuity_type", "aliases")
        continuity_relationships=@("id", "source_continuity_id", "relationship_type", "target_continuity_id", "status")
        authority_profiles=@(
            "lifecycle"
            "label"
            "continuity_order"
            "accepted_membership_statuses"
            "source_priority_order"
            "comparison_work_relationship_types"
            "cross_source_conflict"
            "derivative_deviation_owner"
            "preserve_source_scoped_claims"
            "claim_authority_rules"
        )
        segments=@("work_id", "parent_segment_id", "segment_type", "label", "aliases", "localized_titles", "ordinal")
        content_groups=@("lifecycle", "label", "group_type", "members", "parent_group_ids", "ordering_scheme_id", "localized_titles", "aliases")
        numbering_schemes=@("lifecycle", "label", "target_type", "scope_type", "scope_id", "entries")
        ordering_schemes=@("label", "ordering_type", "ordering_mode", "entries")
        work_relationships=@("id", "source_work_id", "relationship_type", "target_work_id", "continuity_ids", "status", "applicability_scope_id")
        adaptation_mappings=@("id", "basis_inputs", "target_work_id", "target_segment_ids", "mapping_type", "status")
        territories=@("lifecycle", "label", "territory_type", "parent_territory_id", "codes")
        applicability_scopes=@("id", "target_type", "target_id", "territory_ids", "effective_window", "precedence")
        scoped_continuity_assertions=@("id", "applicability_scope_id", "continuity_id", "status")
        work_production_contexts=@("id", "work_id", "production_origin", "authorization_status", "rights_basis", "commerciality", "applicability_scope_id")
        platforms=@("lifecycle", "label", "platform_type", "aliases")
        manifestations=@("lifecycle", "label", "work_id", "segment_ids", "manifestation_type", "language_tags", "territory_ids", "container_format_ids", "localized_titles", "aliases")
        manifestation_relationships=@("id", "source_manifestation_id", "relationship_type", "target_manifestation_id", "status")
        manifestation_segment_mappings=@("id", "source_manifestation_id", "source_segment_ids", "target_manifestation_id", "target_segment_ids", "mapping_type", "status")
        release_components=@("lifecycle", "label", "manifestation_id", "component_type", "segment_ids", "language_tag")
        release_component_relationships=@("id", "source_component_id", "relationship_type", "target_component_id")
        release_packages=@("lifecycle", "label", "package_type", "manifestation_ids", "segment_ids", "release_component_ids", "container_format_ids", "localized_titles", "aliases")
        release_runs=@(
            "lifecycle"
            "label"
            "subject_type"
            "subject_id"
            "segment_ids"
            "ordering_scheme_id"
            "release_event_type"
            "phases"
            "territory_ids"
            "platform_ids"
            "availability_status"
            "exceptions"
        )
        release_events=@(
            "lifecycle"
            "label"
            "subject_type"
            "subject_id"
            "segment_ids"
            "release_event_type"
            "release_window"
            "territory_ids"
            "platform_ids"
            "availability_status"
            "release_run_id"
        )
        catalog_placements=@("lifecycle", "label", "platform_id", "placement_type", "parent_placement_id", "target_type", "target_id", "ordinal", "provider_key", "localized_titles")
        platform_offerings=@(
            "lifecycle"
            "label"
            "platform_id"
            "subject_type"
            "subject_id"
            "segment_ids"
            "release_event_id"
            "offering_type"
            "availability_status"
            "territory_ids"
            "language_tags"
            "availability_window"
            "catalog_placement_ids"
        )
        identifier_schemes=@("lifecycle", "label", "target_types", "case_sensitive")
        sources=@(
            "lifecycle"
            "label"
            "work_ids"
            "manifestation_id"
            "release_package_id"
            "release_event_id"
            "release_component_ids"
            "platform_offering_id"
            "medium_id"
            "locator_medium_ids"
            "container_format_ids"
            "role"
            "comparison_group"
            "priority"
            "aliases"
            "evidence_modes"
            "observations"
            "coverage"
            "resource_bindings"
        )
        source_relationships=@("id", "source_source_id", "relationship_type", "target_source_id")
        external_identifiers=@("id", "scheme_id", "target_type", "target_id", "value", "territory_ids", "language_tag", "status")
    }
    $listRegistries = @(
        "continuity_relationships"
        "work_relationships"
        "adaptation_mappings"
        "applicability_scopes"
        "scoped_continuity_assertions"
        "work_production_contexts"
        "manifestation_relationships"
        "manifestation_segment_mappings"
        "release_component_relationships"
        "source_relationships"
        "external_identifiers"
    )
    foreach ($registryName in $schemas.Keys) {
        $raw = Get-ProjectMapValue $Registry $registryName
        if ($listRegistries -ccontains $registryName) {
            $records = @($raw)
        }
        elseif ($raw -is [System.Collections.IDictionary]) {
            $records = @($raw.Values)
        }
        else {
            $records = @()
        }
        for ($index = 0; $index -lt $records.Count; $index++) {
            $record = $records[$index]
            if ($record -is [System.Collections.IDictionary]) {
                Assert-KnowledgeMapKeys $record $schemas[$registryName] "Source registry '$registryName.$index'"
            }
        }
    }
    $nestedSchemas = @(
        [pscustomobject]@{registry="authority_profiles"
            field="claim_authority_rules"
            keys=@("id", "claim_namespace", "precedence", "source_ids", "source_roles", "medium_ids", "evidence_modes", "rank")
        },
        [pscustomobject]@{registry="content_groups"
            field="members"
            keys=@("id", "target_type", "target_id", "role")
        },
        [pscustomobject]@{registry="numbering_schemes"
            field="entries"
            keys=@("target_id", "display_number", "aliases")
        },
        [pscustomobject]@{registry="ordering_schemes"
            field="entries"
            keys=@("id", "target_type", "target_id", "ordinal", "after_entry_ids")
        },
        [pscustomobject]@{registry="adaptation_mappings"
            field="basis_inputs"
            keys=@("work_id", "segment_ids", "basis_role")
        },
        [pscustomobject]@{registry="release_runs"
            field="phases"
            keys=@("id", "segment_ids", "first_release_window", "cadence", "batch_size")
        },
        [pscustomobject]@{registry="release_runs"
            field="exceptions"
            keys=@("exception_type", "segment_id", "release_window", "interval_count")
        },
        [pscustomobject]@{registry="sources"
            field="observations"
            keys=@("id", "target_type", "target_id")
        },
        [pscustomobject]@{registry="sources"
            field="coverage"
            keys=@("id", "target_type", "target_id", "coverage_type", "medium_id", "evidence_modes", "position_ranges")
        },
        [pscustomobject]@{registry="sources"
            field="resource_bindings"
            keys=@("resource_type_id", "root_id", "relative_path", "required")
        }
    )
    foreach ($shape in $nestedSchemas) {
        $raw = Get-ProjectMapValue $Registry $shape.registry
        if ($raw -isnot [System.Collections.IDictionary]) {
            continue
        }
        foreach ($parent in $raw.Values) {
            if ($parent -isnot [System.Collections.IDictionary]) {
                continue
            }
            $children = @(Get-ProjectMapValue $parent $shape.field)
            for ($index = 0; $index -lt $children.Count; $index++) {
                $child = $children[$index]
                if ($child -is [System.Collections.IDictionary]) {
                    Assert-KnowledgeMapKeys $child $shape.keys "Source registry '$($shape.registry).$($shape.field)[$index]'"
                }
                if ($shape.field -eq "coverage" -and $child -is [System.Collections.IDictionary]) {
                    $ranges = @(Get-ProjectMapValue $child "position_ranges")
                    for ($rangeIndex = 0; $rangeIndex -lt $ranges.Count; $rangeIndex++) {
                        if ($ranges[$rangeIndex] -is [System.Collections.IDictionary]) {
                            Assert-KnowledgeMapKeys $ranges[$rangeIndex] @("id", "start", "end") "Source registry 'sources.coverage[$index].position_ranges[$rangeIndex]'"
                        }
                    }
                }
            }
        }
    }
}

function Get-KnowledgeSourceRegistry {
    param(
        [object]$ProjectConfig,
        [object]$ResourceConfig,
        [object]$SchemaPackRegistry = $null
    )

    Import-ProjectYamlModule
    if ($null -eq $SchemaPackRegistry) {
        $SchemaPackRegistry = Get-KnowledgeSchemaPackRegistry $ProjectConfig
    }
    $lookupKeys = Get-KnowledgeLookupKeyConfig $ProjectConfig
    $allowedSourceRoles = @(Get-SchemaPackAllowedValues $SchemaPackRegistry "source.source-role")
    if ($allowedSourceRoles.Count -eq 0) {
        throw "Selected schema packs do not provide controlled namespace 'source.source-role' required by 'sources.*.role'."
    }
    $allowedMembershipStatuses = @(Get-SchemaPackAllowedValues $SchemaPackRegistry "source.membership-status")
    if ($allowedMembershipStatuses.Count -eq 0) {
        throw "Selected schema packs do not provide controlled namespace 'source.membership-status' required by continuity memberships and relationship statuses."
    }
    $claimNamespaceAncestors = Get-SourceControlledValueAncestors $SchemaPackRegistry "provenance.claim-namespace"
    if ($claimNamespaceAncestors.Count -eq 0) {
        throw "Selected schema packs do not provide controlled namespace 'provenance.claim-namespace'."
    }
    $evidenceModeAncestors = Get-SourceControlledValueAncestors $SchemaPackRegistry "provenance.evidence-mode"
    if ($evidenceModeAncestors.Count -eq 0) {
        throw "Selected schema packs do not provide controlled namespace 'provenance.evidence-mode'."
    }
    $registryPath = $ProjectConfig.sources_registry
    $registry = ConvertFrom-KnowledgeYamlFile $registryPath $script:SupportedSourceSchemaVersion "source registry"
    if ($null -eq $registry -or -not ($registry -is [System.Collections.IDictionary])) {
        throw "Source registry root must be a mapping: $registryPath"
    }
    $rootKeys = @(
        "schema_version"
        "default_authority_profile_id"
        "media_modalities"
        "cultural_forms"
        "release_forms"
        "container_formats"
        "mediums"
        "work_group_types"
        "work_groups"
        "continuities"
        "continuity_relationship_types"
        "continuity_relationships"
        "authority_profiles"
        "work_relationship_types"
        "works"
        "segments"
        "content_groups"
        "numbering_schemes"
        "ordering_schemes"
        "work_relationships"
        "adaptation_mappings"
        "territories"
        "applicability_scopes"
        "scoped_continuity_assertions"
        "work_production_contexts"
        "platforms"
        "manifestation_relationship_types"
        "manifestations"
        "manifestation_relationships"
        "manifestation_segment_mappings"
        "release_components"
        "release_component_relationship_types"
        "release_component_relationships"
        "release_packages"
        "release_runs"
        "release_events"
        "catalog_placements"
        "platform_offerings"
        "identifier_schemes"
        "source_relationship_types"
        "sources"
        "source_relationships"
        "external_identifiers"
    )
    Assert-KnowledgeMapKeys $registry $rootKeys "Source registry root"
    Assert-SourceRegistryShapes $registry
    $schemaVersion = Get-ProjectMapValue $registry "schema_version"
    if ($schemaVersion -isnot [int] -or $schemaVersion -ne $script:SupportedSourceSchemaVersion) {
        throw "Unsupported source schema_version '$schemaVersion'; expected $($script:SupportedSourceSchemaVersion)."
    }

    $mediaModalities = ConvertTo-LabeledSourceRegistry (Get-ProjectMapValue $registry "media_modalities") "media_modalities"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.media-modality" @($mediaModalities.Keys) "media_modalities"

    $rawCulturalForms = Get-ProjectMapValue $registry "cultural_forms"
    if ($null -eq $rawCulturalForms -or -not ($rawCulturalForms -is [System.Collections.IDictionary])) {
        throw "Source registry 'cultural_forms' must be a mapping."
    }
    $culturalForms = [ordered]@{}
    foreach ($culturalFormId in $rawCulturalForms.Keys) {
        $context = "cultural_forms.$culturalFormId"
        Test-StableSourceId $culturalFormId $context
        $culturalForm = $rawCulturalForms[$culturalFormId]
        if ($culturalForm -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $culturalForm @("label", "modality_id") "Source registry '$context'"
        $modalityId = Get-RequiredSourceString $culturalForm "modality_id" $context
        if (-not $mediaModalities.Contains($modalityId)) {
            throw "Source registry '$context.modality_id' references unknown media modality '$modalityId'."
        }
        $culturalForms[$culturalFormId] = [pscustomobject]@{
            id = $culturalFormId
            label = Get-RequiredSourceString $culturalForm "label" $context
            modality_id = $modalityId
        }
    }
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.cultural-form" @($culturalForms.Keys) "cultural_forms"

    $releaseForms = ConvertTo-LabeledSourceRegistry (Get-ProjectMapValue $registry "release_forms") "release_forms"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-form" @($releaseForms.Keys) "release_forms"

    $containerFormats = ConvertTo-LabeledSourceRegistry (Get-ProjectMapValue $registry "container_formats") "container_formats"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.container-format" @($containerFormats.Keys) "container_formats"

    $rawMediums = Get-ProjectMapValue $registry "mediums"
    if ($null -eq $rawMediums -or -not ($rawMediums -is [System.Collections.IDictionary])) {
        throw "Source registry 'mediums' must be a mapping."
    }
    $mediums = [ordered]@{}
    foreach ($mediumId in $rawMediums.Keys) {
        $mediums[$mediumId] = ConvertTo-MediumConfig $mediumId $rawMediums[$mediumId] $mediaModalities $culturalForms $SchemaPackRegistry
    }
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.medium" @($mediums.Keys) "mediums"

    $rawGroupTypes = Get-ProjectMapValue $registry "work_group_types"
    if ($null -eq $rawGroupTypes -or -not ($rawGroupTypes -is [System.Collections.IDictionary])) {
        throw "Source registry 'work_group_types' must be a mapping."
    }
    $workGroupTypes = [ordered]@{}
    foreach ($typeId in $rawGroupTypes.Keys) {
        $context = "work_group_types.$typeId"
        Test-StableSourceId $typeId $context
        $rawType = $rawGroupTypes[$typeId]
        if ($rawType -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $rawType @("label", "ordered") "Source registry '$context'"
        $workGroupTypes[$typeId] = [pscustomobject]@{
            id = $typeId
            label = Get-RequiredSourceString $rawType "label" $context
            ordered = Get-RequiredSourceBoolean $rawType "ordered" $context
        }
    }
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-group-type" @($workGroupTypes.Keys) "work_group_types"

    $rawGroups = Get-ProjectMapValue $registry "work_groups"
    if ($null -eq $rawGroups -or -not ($rawGroups -is [System.Collections.IDictionary])) {
        throw "Source registry 'work_groups' must be a mapping."
    }
    $workGroups = [ordered]@{}
    foreach ($groupId in $rawGroups.Keys) {
        $context = "work_groups.$groupId"
        Test-StableSourceId $groupId $context
        $group = $rawGroups[$groupId]
        if ($group -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $group @("lifecycle", "label", "short_label", "group_type", "parent_group_id") "Source registry '$context'"
        $lifecycle = Get-RequiredSourceString $group "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $groupType = Get-RequiredSourceString $group "group_type" $context
        if (-not $workGroupTypes.Contains($groupType)) {
            throw "Source registry '$context.group_type' references unknown work group type '$groupType'."
        }
        $parentGroupId = ([string](Get-ProjectMapValue $group "parent_group_id" "")).Trim()
        $workGroups[$groupId] = [pscustomobject]@{
            id = $groupId
            lifecycle = $lifecycle
            label = Get-RequiredSourceString $group "label" $context
            short_label = Get-RequiredSourceString $group "short_label" $context
            group_type = $groupType
            parent_group_id = if ([string]::IsNullOrWhiteSpace($parentGroupId)) {
                $null
            }
            else {
                $parentGroupId
            }
        }
    }
    foreach ($group in $workGroups.Values) {
        if ($null -eq $group.parent_group_id) {
            continue
        }
        if (-not $workGroups.Contains($group.parent_group_id)) {
            throw "Source registry 'work_groups.$($group.id).parent_group_id' references unknown work group '$($group.parent_group_id)'."
        }
        if ($group.parent_group_id -eq $group.id) {
            throw "Source registry work group '$($group.id)' cannot parent itself."
        }
        $active = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $cursor = $group.id
        while ($null -ne $cursor) {
            if (-not $active.Add($cursor)) {
                throw "Source registry contains a work-group parent cycle involving '$cursor'."
            }
            $cursor = $workGroups[$cursor].parent_group_id
        }
    }

    $rawContinuities = Get-ProjectMapValue $registry "continuities"
    if ($null -eq $rawContinuities -or -not ($rawContinuities -is [System.Collections.IDictionary])) {
        throw "Source registry 'continuities' must be a mapping."
    }
    $continuities = [ordered]@{}
    $continuityAliases = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    $continuityIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($continuityId in $rawContinuities.Keys) {
        [void]$continuityIdKeys.Add((ConvertTo-KnowledgeLookupKey $continuityId $lookupKeys))
    }
    foreach ($continuityId in $rawContinuities.Keys) {
        $context = "continuities.$continuityId"
        Test-StableSourceId $continuityId $context
        $continuity = $rawContinuities[$continuityId]
        if ($continuity -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $continuity @("lifecycle", "label", "short_label", "continuity_type", "aliases") "Source registry '$context'"
        $lifecycle = Get-RequiredSourceString $continuity "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $continuityType = Get-RequiredSourceString $continuity "continuity_type" $context
        Test-StableSourceId $continuityType "$context.continuity_type"
        $aliases = @(Get-SourceStringList $continuity "aliases" $context)
        foreach ($alias in $aliases) {
            Test-StableSourceId $alias "$context.aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($continuityAliases.ContainsKey($aliasKey) -or $continuityIdKeys.Contains($aliasKey)) {
                throw "Source registry continuity alias '$alias' is duplicated or collides with a continuity ID."
            }
            $continuityAliases[$aliasKey] = $continuityId
        }
        $continuities[$continuityId] = [pscustomobject]@{
            id = $continuityId
            lifecycle = $lifecycle
            label = Get-RequiredSourceString $continuity "label" $context
            short_label = Get-RequiredSourceString $continuity "short_label" $context
            continuity_type = $continuityType
            aliases = @($aliases)
        }
    }
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.continuity-type" @($continuities.Values | ForEach-Object { $_.continuity_type }) "continuities.*.continuity_type"

    $continuityRelationshipTypes = ConvertTo-RelationshipTypeRegistry (Get-ProjectMapValue $registry "continuity_relationship_types") "continuity_relationship_types"
    $workRelationshipTypes = ConvertTo-RelationshipTypeRegistry (Get-ProjectMapValue $registry "work_relationship_types") "work_relationship_types"
    $sourceRelationshipTypes = ConvertTo-RelationshipTypeRegistry (Get-ProjectMapValue $registry "source_relationship_types") "source_relationship_types"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.continuity-relationship-type" @($continuityRelationshipTypes.Keys) "continuity_relationship_types"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-relationship-type" @($workRelationshipTypes.Keys) "work_relationship_types"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.source-relationship-type" @($sourceRelationshipTypes.Keys) "source_relationship_types"

    $seenRelationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $continuityRelationships = @()
    $rawContinuityRelationships = @(Get-ProjectMapValue $registry "continuity_relationships")
    for ($index = 0; $index -lt $rawContinuityRelationships.Count; $index += 1) {
        $context = "continuity_relationships[$index]"
        $relationship = $rawContinuityRelationships[$index]
        if ($relationship -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$context' must be a mapping."
        }
        Assert-KnowledgeMapKeys $relationship @("id", "source_continuity_id", "target_continuity_id", "relationship_type", "status") "Source registry '$context'"
        $id = Get-RequiredSourceString $relationship "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenRelationshipIds.Add($id)) {
            throw "Source registry relationship ID '$id' is duplicated."
        }
        $sourceId = Get-RequiredSourceString $relationship "source_continuity_id" $context
        $targetId = Get-RequiredSourceString $relationship "target_continuity_id" $context
        $type = Get-RequiredSourceString $relationship "relationship_type" $context
        if (-not $continuities.Contains($sourceId) -or -not $continuities.Contains($targetId)) {
            throw "Source registry '$context' references an unknown continuity."
        }
        if ($sourceId -eq $targetId) {
            throw "Source registry '$context' cannot relate a continuity to itself."
        }
        if (-not $continuityRelationshipTypes.Contains($type)) {
            throw "Source registry '$context.relationship_type' references unknown type '$type'."
        }
        $status = Get-RequiredSourceString $relationship "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')."
        }
        $continuityRelationships += [pscustomobject]@{ id=$id
            source_continuity_id=$sourceId
            relationship_type=$type
            target_continuity_id=$targetId
            status=$status
        }
    }

    $rawProfiles = Get-ProjectMapValue $registry "authority_profiles"
    if ($null -eq $rawProfiles -or -not ($rawProfiles -is [System.Collections.IDictionary])) {
        throw "Source registry 'authority_profiles' must be a mapping."
    }
    $authorityProfiles = [ordered]@{}
    foreach ($profileId in $rawProfiles.Keys) {
        $context = "authority_profiles.$profileId"
        Test-StableSourceId $profileId $context
        $profile = $rawProfiles[$profileId]
        if ($profile -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$context' must be a mapping."
        }
        $authorityProfileKeys = @(
            "lifecycle"
            "label"
            "continuity_order"
            "accepted_membership_statuses"
            "source_priority_order"
            "comparison_work_relationship_types"
            "cross_source_conflict"
            "derivative_deviation_owner"
            "preserve_source_scoped_claims"
            "claim_authority_rules"
        )
        Assert-KnowledgeMapKeys $profile $authorityProfileKeys "Source registry '$context'"
        $lifecycle = Get-RequiredSourceString $profile "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $continuityOrder = @(Get-SourceStringList $profile "continuity_order" $context)
        if (@($continuityOrder | Sort-Object -Unique).Count -ne $continuityOrder.Count) {
            throw "Source registry '$context.continuity_order' contains duplicates."
        }
        foreach ($continuityId in $continuityOrder) {
            if (-not $continuities.Contains($continuityId)) {
                throw "Source registry '$context.continuity_order' references unknown continuity '$continuityId'."
            }
        }
        $acceptedStatuses = @(Get-SourceStringList $profile "accepted_membership_statuses" $context)
        foreach ($status in $acceptedStatuses) {
            if ($allowedMembershipStatuses -cnotcontains $status) {
                throw "Source registry '$context.accepted_membership_statuses' contains unknown value '$status'."
            }
        }
        $priorityOrder = Get-RequiredSourceString $profile "source_priority_order" $context
        if ($script:AllowedPriorityOrders -cnotcontains $priorityOrder) {
            throw "Source registry '$context.source_priority_order' must be one of: $($script:AllowedPriorityOrders -join ', ')."
        }
        $comparisonTypes = @(Get-SourceStringListAllowEmpty $profile "comparison_work_relationship_types" $context)
        foreach ($type in $comparisonTypes) {
            if (-not $workRelationshipTypes.Contains($type)) {
                throw "Source registry '$context.comparison_work_relationship_types' references unknown type '$type'."
            }
        }
        $conflict = Get-RequiredSourceString $profile "cross_source_conflict" $context
        if ($script:AllowedConflictBehaviors -cnotcontains $conflict) {
            throw "Source registry '$context.cross_source_conflict' must be one of: $($script:AllowedConflictBehaviors -join ', ')."
        }
        $deviationOwner = Get-RequiredSourceString $profile "derivative_deviation_owner" $context
        if ($script:AllowedDeviationOwners -cnotcontains $deviationOwner) {
            throw "Source registry '$context.derivative_deviation_owner' must be one of: $($script:AllowedDeviationOwners -join ', ')."
        }
        $rules = @()
        $seenRuleIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $rawRules = @(Get-ProjectMapValue $profile "claim_authority_rules")
        for ($ruleIndex = 0; $ruleIndex -lt $rawRules.Count; $ruleIndex++) {
            $ruleContext = "$context.claim_authority_rules[$ruleIndex]"
            $rule = $rawRules[$ruleIndex]
            if ($rule -isnot [System.Collections.IDictionary]) {
                throw "Source registry '$ruleContext' must be a mapping."
            }
            Assert-KnowledgeMapKeys $rule @("id", "claim_namespace", "precedence", "source_ids", "source_roles", "medium_ids", "evidence_modes", "rank") "Source registry '$ruleContext'"
            $ruleId = Get-RequiredSourceString $rule "id" $ruleContext
            Test-StableSourceId $ruleId "$ruleContext.id"
            if (-not $seenRuleIds.Add($ruleId)) {
                throw "Source registry '$context.claim_authority_rules' repeats ID '$ruleId'."
            }
            $claimNamespace = Get-RequiredSourceString $rule "claim_namespace" $ruleContext
            Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.claim-namespace" @($claimNamespace) "$ruleContext.claim_namespace"
            $precedence = Get-ProjectMapValue $rule "precedence"
            if ($precedence -is [bool] -or $precedence -isnot [int] -or [int]$precedence -lt 1) {
                throw "Source registry '$ruleContext.precedence' must be a positive integer."
            }
            $sourceIds = @(Get-SourceStringListAllowEmpty $rule "source_ids" $ruleContext)
            $sourceRoles = @(Get-SourceStringListAllowEmpty $rule "source_roles" $ruleContext)
            $mediumIds = @(Get-SourceStringListAllowEmpty $rule "medium_ids" $ruleContext)
            $evidenceModes = @(Get-SourceStringListAllowEmpty $rule "evidence_modes" $ruleContext)
            if ($sourceIds.Count + $sourceRoles.Count + $mediumIds.Count + $evidenceModes.Count -eq 0) {
                throw "Source registry '$ruleContext' must declare at least one source selector."
            }
            foreach ($sourceId in $sourceIds) {
                Test-StableSourceId $sourceId "$ruleContext.source_ids"
            }
            Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.evidence-mode" @($evidenceModes) "$ruleContext.evidence_modes"
            Assert-SourceSchemaPackValues $SchemaPackRegistry "source.source-role" $sourceRoles "$ruleContext.source_roles"
            $unknownRuleMediums = @($mediumIds | Where-Object { -not $mediums.Contains($_) })
            if ($unknownRuleMediums.Count -gt 0) {
                throw "Source registry '$ruleContext.medium_ids' references unknown media: $($unknownRuleMediums -join ', ')."
            }
            $rank = Get-ProjectMapValue $rule "rank"
            if ($rank -is [bool] -or $rank -isnot [int] -or [int]$rank -lt 1) {
                throw "Source registry '$ruleContext.rank' must be a positive integer."
            }
            $rules += [pscustomobject]@{id=$ruleId
                claim_namespace=$claimNamespace
                precedence=[int]$precedence
                source_ids=@($sourceIds)
                source_roles=@($sourceRoles)
                medium_ids=@($mediumIds)
                evidence_modes=@($evidenceModes)
                rank=[int]$rank
            }
        }
        $authorityProfiles[$profileId] = [pscustomobject]@{
            id=$profileId
            lifecycle=$lifecycle
            label=Get-RequiredSourceString $profile "label" $context
            continuity_order=@($continuityOrder)
            accepted_membership_statuses=@($acceptedStatuses)
            source_priority_order=$priorityOrder
            comparison_work_relationship_types=@($comparisonTypes)
            cross_source_conflict=$conflict
            derivative_deviation_owner=$deviationOwner
            preserve_source_scoped_claims=Get-RequiredSourceBoolean $profile "preserve_source_scoped_claims" $context
            claim_authority_rules=@($rules)
        }
    }
    $defaultAuthorityProfileId = Get-RequiredSourceString $registry "default_authority_profile_id" "root"
    if (-not $authorityProfiles.Contains($defaultAuthorityProfileId)) {
        throw "Source registry 'default_authority_profile_id' references unknown authority profile '$defaultAuthorityProfileId'."
    }

    $rawWorks = Get-ProjectMapValue $registry "works"
    if ($null -eq $rawWorks -or -not ($rawWorks -is [System.Collections.IDictionary])) {
        throw "Source registry 'works' must be a mapping."
    }
    $works = [ordered]@{}
    $workAliases = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    $workIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($workId in $rawWorks.Keys) {
        [void]$workIdKeys.Add((ConvertTo-KnowledgeLookupKey $workId $lookupKeys))
    }
    $seenOrdinals = @{}
    foreach ($workId in $rawWorks.Keys) {
        $context = "works.$workId"
        Test-StableSourceId $workId $context
        $work = $rawWorks[$workId]
        if ($work -isnot [System.Collections.IDictionary]) {
            throw "Source registry '$context' must be a mapping."
        }
        $workKeys = @(
            "lifecycle"
            "label"
            "short_label"
            "parent_work_id"
            "work_type"
            "medium_id"
            "release_form_id"
            "work_status"
            "aliases"
            "localized_titles"
            "group_memberships"
            "continuity_memberships"
            "chapter_numbering"
            "volume_catalog_status"
            "volumes"
        )
        Assert-KnowledgeMapKeys $work $workKeys "Source registry '$context'"
        $lifecycle = Get-RequiredSourceString $work "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $mediumId = Get-RequiredSourceString $work "medium_id" $context
        if (-not $mediums.Contains($mediumId)) {
            throw "Source registry '$context.medium_id' references unknown medium '$mediumId'."
        }
        $workType = Get-RequiredSourceString $work "work_type" $context
        Test-StableSourceId $workType "$context.work_type"
        $releaseFormId = Get-RequiredSourceString $work "release_form_id" $context
        if (-not $releaseForms.Contains($releaseFormId)) {
            throw "Source registry '$context.release_form_id' references unknown release form '$releaseFormId'."
        }
        $workStatus = Get-RequiredSourceString $work "work_status" $context
        Test-StableSourceId $workStatus "$context.work_status"
        $chapterNumbering = Get-RequiredSourceString $work "chapter_numbering" $context
        if ($script:AllowedChapterNumberingModes -cnotcontains $chapterNumbering) {
            throw "Source registry '$context.chapter_numbering' must be one of: $($script:AllowedChapterNumberingModes -join ', ')."
        }
        $volumeStatus = Get-RequiredSourceString $work "volume_catalog_status" $context
        if ($script:AllowedVolumeCatalogStatuses -cnotcontains $volumeStatus) {
            throw "Source registry '$context.volume_catalog_status' must be one of: $($script:AllowedVolumeCatalogStatuses -join ', ')."
        }
        $aliases = @(Get-SourceStringList $work "aliases" $context)
        foreach ($alias in $aliases) {
            Test-StableSourceId $alias "$context.aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($workAliases.ContainsKey($aliasKey) -or $workIdKeys.Contains($aliasKey)) {
                throw "Source registry work alias '$alias' is duplicated or collides with a work ID."
            }
            $workAliases[$aliasKey] = $workId
        }
        $groupMemberships = @()
        $seenGroups = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        foreach ($membership in @(Get-ProjectMapValue $work "group_memberships")) {
            if ($membership -isnot [System.Collections.IDictionary]) {
                throw "Source registry '$context.group_memberships' entries must be mappings."
            }
            Assert-KnowledgeMapKeys $membership @("group_id", "role", "ordinal") "Source registry '$context.group_memberships'"
            $groupId = Get-RequiredSourceString $membership "group_id" "$context.group_memberships"
            if (-not $workGroups.Contains($groupId)) {
                throw "Source registry '$context.group_memberships.group_id' references unknown work group '$groupId'."
            }
            if (-not $seenGroups.Add($groupId)) {
                throw "Source registry '$context' repeats work group '$groupId'."
            }
            $role = Get-RequiredSourceString $membership "role" "$context.group_memberships"
            Test-StableSourceId $role "$context.group_memberships.role"
            $ordinal = Get-ProjectMapValue $membership "ordinal"
            $ordered = $workGroupTypes[$workGroups[$groupId].group_type].ordered
            if ($ordered -and ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1)) {
                throw "Source registry '$context.group_memberships.ordinal' must be a positive integer for an ordered work group."
            }
            if (-not $ordered -and $null -ne $ordinal) {
                throw "Source registry '$context.group_memberships.ordinal' is only valid for ordered work groups."
            }
            if ($ordered) {
                $ordinalKey = "$groupId|$ordinal"
                if ($seenOrdinals.ContainsKey($ordinalKey)) {
                    throw "Source registry duplicates ordinal $ordinal in work group '$groupId' between '$($seenOrdinals[$ordinalKey])' and '$workId'."
                }
                $seenOrdinals[$ordinalKey] = $workId
            }
            $groupMemberships += [pscustomobject]@{ group_id=$groupId
                role=$role
                ordinal=if ($null -eq $ordinal) {
                    $null
                }
                else {
                    [int]$ordinal
                }
            }
        }
        if ($groupMemberships.Count -eq 0) {
            throw "Source registry '$context.group_memberships' must be a non-empty list."
        }
        $continuityMemberships = @()
        $seenContinuities = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        foreach ($membership in @(Get-ProjectMapValue $work "continuity_memberships")) {
            if ($membership -isnot [System.Collections.IDictionary]) {
                throw "Source registry '$context.continuity_memberships' entries must be mappings."
            }
            Assert-KnowledgeMapKeys $membership @("continuity_id", "status") "Source registry '$context.continuity_memberships'"
            $continuityId = Get-RequiredSourceString $membership "continuity_id" "$context.continuity_memberships"
            if (-not $continuities.Contains($continuityId)) {
                throw "Source registry '$context.continuity_memberships.continuity_id' references unknown continuity '$continuityId'."
            }
            if (-not $seenContinuities.Add($continuityId)) {
                throw "Source registry '$context' repeats continuity '$continuityId'."
            }
            $status = Get-RequiredSourceString $membership "status" "$context.continuity_memberships"
            if ($allowedMembershipStatuses -cnotcontains $status) {
                throw "Source registry '$context.continuity_memberships.status' must be one of: $($allowedMembershipStatuses -join ', ')."
            }
            $continuityMemberships += [pscustomobject]@{ continuity_id=$continuityId
                status=$status
            }
        }
        if ($continuityMemberships.Count -eq 0) {
            throw "Source registry '$context.continuity_memberships' must be a non-empty list."
        }
        $rawVolumes = @(Get-ProjectMapValue $work "volumes")
        if ($volumeStatus -eq "verified" -and $rawVolumes.Count -eq 0) {
            throw "Source registry verified work '$workId' requires volume records."
        }
        $volumes = @()
        $seenVolumeIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $seenVolumeNumbers = New-Object 'System.Collections.Generic.HashSet[int]'
        foreach ($volume in $rawVolumes) {
            if ($volume -isnot [System.Collections.IDictionary]) {
                throw "Source registry '$context.volumes' entries must be mappings."
            }
            Assert-KnowledgeMapKeys $volume @("id", "number", "label", "chapter_start", "chapter_end") "Source registry '$context.volumes'"
            $volumeId = Get-RequiredSourceString $volume "id" "$context.volumes"
            Test-StableSourceId $volumeId "$context.volumes.id"
            if (-not $seenVolumeIds.Add($volumeId)) {
                throw "Source registry '$context' duplicates volume ID '$volumeId'."
            }
            $number = Get-ProjectMapValue $volume "number"
            $chapterStart = Get-ProjectMapValue $volume "chapter_start"
            $chapterEnd = Get-ProjectMapValue $volume "chapter_end"
            foreach ($value in @($number, $chapterStart, $chapterEnd)) {
                if ($value -is [bool] -or $value -isnot [int] -or [int]$value -lt 1) {
                    throw "Source registry '$context.volumes' numeric fields must be positive integers."
                }
            }
            if (-not $seenVolumeNumbers.Add([int]$number)) {
                throw "Source registry '$context' duplicates volume number $number."
            }
            if ([int]$chapterEnd -lt [int]$chapterStart) {
                throw "Source registry '$context.volumes' chapter range is reversed."
            }
            $volumes += [pscustomobject]@{ id=$volumeId
                number=[int]$number
                label=Get-RequiredSourceString $volume "label" "$context.volumes"
                chapter_start=[int]$chapterStart
                chapter_end=[int]$chapterEnd
            }
        }
        $volumes = @($volumes | Sort-Object number)
        if ($volumeStatus -eq "verified") {
            for ($i = 0; $i -lt $volumes.Count; $i++) {
                if ($volumes[$i].number -ne $i + 1) {
                    throw "Source registry '$context' verified volume numbers must be contiguous from 1."
                }
                if ($i -gt 0 -and $volumes[$i].chapter_start -ne $volumes[$i - 1].chapter_end + 1) {
                    throw "Source registry '$context' verified chapter ranges must be contiguous and non-overlapping."
                }
            }
        }
        $works[$workId] = [pscustomobject]@{
            id=$workId
            lifecycle=$lifecycle
            label=Get-RequiredSourceString $work "label" $context
            short_label=Get-RequiredSourceString $work "short_label" $context
            work_type=$workType
            parent_work_id=Get-OptionalSourceString $work "parent_work_id" $context
            medium_id=$mediumId
            release_form_id=$releaseFormId
            work_status=$workStatus
            aliases=@($aliases)
            group_memberships=@($groupMemberships)
            localized_titles=@(ConvertTo-SourceLocalizedTitles $work $context $SchemaPackRegistry)
            continuity_memberships=@($continuityMemberships)
            chapter_numbering=$chapterNumbering
            volume_catalog_status=$volumeStatus
            volumes=@($volumes)
        }
    }
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-type" @($works.Values | ForEach-Object { $_.work_type }) "works.*.work_type"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-lifecycle-status" @($works.Values | ForEach-Object { $_.work_status }) "works.*.work_status"
    foreach ($work in $works.Values) {
        if ($null -eq $work.parent_work_id) {
            continue
        }
        if (-not $works.Contains($work.parent_work_id)) {
            throw "Source registry 'works.$($work.id).parent_work_id' references unknown work '$($work.parent_work_id)'."
        }
        if ($work.parent_work_id -eq $work.id) {
            throw "Source registry work '$($work.id)' cannot parent itself."
        }
    }
    foreach ($workId in $works.Keys) {
        $activeWorks = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $currentWorkId = $workId
        while ($null -ne $currentWorkId) {
            if (-not $activeWorks.Add($currentWorkId)) {
                throw "Source registry contains a work-parent cycle involving '$currentWorkId'."
            }
            $currentWorkId = $works[$currentWorkId].parent_work_id
        }
    }

    $rawSegments = Get-ProjectMapValue $registry "segments"
    if ($null -eq $rawSegments -or -not ($rawSegments -is [System.Collections.IDictionary])) {
        throw "Source registry 'segments' must be a mapping."
    }
    $segments = [ordered]@{}
    foreach ($segmentId in $rawSegments.Keys) {
        $context = "segments.$segmentId"
        Test-StableSourceId $segmentId $context
        $segment = $rawSegments[$segmentId]
        $workId = Get-RequiredSourceString $segment "work_id" $context
        if (-not $works.Contains($workId)) {
            throw "Source registry '$context.work_id' references unknown work '$workId'."
        }
        $parentSegmentId = ([string](Get-ProjectMapValue $segment "parent_segment_id" "")).Trim()
        $segmentType = Get-RequiredSourceString $segment "segment_type" $context
        Test-StableSourceId $segmentType "$context.segment_type"
        $ordinal = Get-ProjectMapValue $segment "ordinal"
        if ($null -ne $ordinal -and ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1)) {
            throw "Source registry '$context.ordinal' must be a positive integer when present."
        }
        $segments[$segmentId] = [pscustomobject]@{
            id=$segmentId
            work_id=$workId
            parent_segment_id=if ([string]::IsNullOrWhiteSpace($parentSegmentId)) {
                $null
            }
            else {
                $parentSegmentId
            }
            segment_type=$segmentType
            label=Get-RequiredSourceString $segment "label" $context
            aliases=@(Get-SourceStringListAllowEmpty $segment "aliases" $context)
            localized_titles=@(ConvertTo-SourceLocalizedTitles $segment $context $SchemaPackRegistry)
            ordinal=if ($null -eq $ordinal) {
                $null
            }
            else {
                [int]$ordinal
            }
        }
    }
    if ($segments.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.segment-type" @($segments.Values | ForEach-Object { $_.segment_type }) "segments.*.segment_type"
    }
    foreach ($segment in $segments.Values) {
        if ($null -eq $segment.parent_segment_id) {
            continue
        }
        if (-not $segments.Contains($segment.parent_segment_id)) {
            throw "Source registry 'segments.$($segment.id).parent_segment_id' references unknown segment '$($segment.parent_segment_id)'."
        }
        $parent = $segments[$segment.parent_segment_id]
        if ($parent.id -eq $segment.id) {
            throw "Source registry segment '$($segment.id)' cannot parent itself."
        }
        if ($parent.work_id -ne $segment.work_id) {
            throw "Source registry segment '$($segment.id)' and its parent must belong to the same work."
        }
    }
    foreach ($segmentId in $segments.Keys) {
        $activeSegments = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $currentSegmentId = $segmentId
        while ($null -ne $currentSegmentId) {
            if (-not $activeSegments.Add($currentSegmentId)) {
                throw "Source registry contains a segment-parent cycle involving '$currentSegmentId'."
            }
            $currentSegmentId = $segments[$currentSegmentId].parent_segment_id
        }
    }

    $segmentAliasesByWork = @{}
    foreach ($segment in $segments.Values) {
        if (-not $segmentAliasesByWork.ContainsKey($segment.work_id)) {
            $segmentAliasesByWork[$segment.work_id] = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        }
        $workSegmentIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        foreach ($item in $segments.Values) {
            if ($item.work_id -eq $segment.work_id) {
                [void]$workSegmentIdKeys.Add((ConvertTo-KnowledgeLookupKey $item.id $lookupKeys))
            }
        }
        foreach ($alias in $segment.aliases) {
            Test-StableSourceId $alias "segments.$($segment.id).aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($workSegmentIdKeys.Contains($aliasKey) -or -not $segmentAliasesByWork[$segment.work_id].Add($aliasKey)) {
                throw "Source registry segment alias '$alias' is duplicated or collides inside work '$($segment.work_id)'."
            }
        }
    }

    $rawNumberingSchemes = Get-ProjectMapValue $registry "numbering_schemes"
    if ($null -eq $rawNumberingSchemes -or -not ($rawNumberingSchemes -is [System.Collections.IDictionary])) {
        throw "Source registry 'numbering_schemes' must be a mapping."
    }
    $numberingSchemes = [ordered]@{}
    foreach ($schemeId in $rawNumberingSchemes.Keys) {
        $context = "numbering_schemes.$schemeId"
        Test-StableSourceId $schemeId $context
        $scheme = $rawNumberingSchemes[$schemeId]
        $targetType = Get-RequiredSourceString $scheme "target_type" $context
        $scopeType = Get-RequiredSourceString $scheme "scope_type" $context
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.numbering-target-type" @($targetType) "$context.target_type"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.numbering-scope-type" @($scopeType) "$context.scope_type"
        $scopeId = Get-OptionalSourceString $scheme "scope_id" $context
        if ($scopeType -eq "none" -and $null -ne $scopeId) {
            throw "Source registry '$context.scope_id' must be omitted for none scope."
        }
        if ($scopeType -eq "work") {
            if ($null -eq $scopeId -or -not $works.Contains($scopeId)) {
                throw "Source registry '$context.scope_id' references unknown work '$scopeId'."
            }
            if ($targetType -ne "segment") {
                throw "Source registry '$context' work scope requires segment targets."
            }
        }
        if ($scopeType -eq "work-group") {
            if ($null -eq $scopeId -or -not $workGroups.Contains($scopeId)) {
                throw "Source registry '$context.scope_id' references unknown work group '$scopeId'."
            }
            if ($targetType -ne "work") {
                throw "Source registry '$context' work-group scope requires work targets."
            }
        }
        $rawEntries = @(Get-ProjectMapValue $scheme "entries")
        if ($rawEntries.Count -eq 0) {
            throw "Source registry '$context.entries' must be a non-empty list."
        }
        $entries = @()
        $seenTargets = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $seenNumbers = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        foreach ($entry in $rawEntries) {
            $targetId = Get-RequiredSourceString $entry "target_id" "$context.entries"
            $targets = if ($targetType -eq "work") {
                $works
            }
            else {
                $segments
            }
            if (-not $targets.Contains($targetId)) {
                throw "Source registry '$context.entries.target_id' references unknown $targetType '$targetId'."
            }
            if ($scopeType -eq "work" -and $segments[$targetId].work_id -ne $scopeId) {
                throw "Source registry '$context.entries' target falls outside work scope '$scopeId'."
            }
            if ($scopeType -eq "work-group") {
                $insideGroup = @($works[$targetId].group_memberships | Where-Object { $_.group_id -eq $scopeId }).Count -gt 0
                if (-not $insideGroup) {
                    throw "Source registry '$context.entries' target falls outside work group scope '$scopeId'."
                }
            }
            $displayNumber = Get-RequiredSourceString $entry "display_number" "$context.entries"
            $aliases = @(Get-SourceStringListAllowEmpty $entry "aliases" "$context.entries")
            if (-not $seenTargets.Add($targetId) -or -not $seenNumbers.Add((ConvertTo-KnowledgeLookupKey $displayNumber $lookupKeys))) {
                throw "Source registry '$context.entries' repeats a target or number."
            }
            foreach ($alias in $aliases) {
                if (-not $seenNumbers.Add((ConvertTo-KnowledgeLookupKey $alias $lookupKeys))) {
                    throw "Source registry '$context.entries' repeats number alias '$alias'."
                }
            }
            $entries += [pscustomobject]@{ target_id=$targetId
                display_number=$displayNumber
                aliases=@($aliases)
            }
        }
        $lifecycle = Get-RequiredSourceString $scheme "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $numberingSchemes[$schemeId] = [pscustomobject]@{ id=$schemeId
            lifecycle=$lifecycle
            label=Get-RequiredSourceString $scheme "label" $context
            target_type=$targetType
            scope_type=$scopeType
            scope_id=$scopeId
            entries=@($entries)
        }
    }

    $rawOrderingSchemes = Get-ProjectMapValue $registry "ordering_schemes"
    if ($null -eq $rawOrderingSchemes -or -not ($rawOrderingSchemes -is [System.Collections.IDictionary])) {
        throw "Source registry 'ordering_schemes' must be a mapping."
    }
    $orderingSchemes = [ordered]@{}
    foreach ($schemeId in $rawOrderingSchemes.Keys) {
        $context = "ordering_schemes.$schemeId"
        Test-StableSourceId $schemeId $context
        $scheme = $rawOrderingSchemes[$schemeId]
        $orderingType = Get-RequiredSourceString $scheme "ordering_type" $context
        Test-StableSourceId $orderingType "$context.ordering_type"
        $orderingMode = Get-RequiredSourceString $scheme "ordering_mode" $context
        if ($script:AllowedOrderingModes -cnotcontains $orderingMode) {
            throw "Source registry '$context.ordering_mode' must be one of: $($script:AllowedOrderingModes -join ', ')."
        }
        $rawEntries = @(Get-ProjectMapValue $scheme "entries")
        if ($rawEntries.Count -eq 0) {
            throw "Source registry '$context.entries' must be a non-empty list."
        }
        $entries = @()
        $seenEntryIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $seenTargets = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $seenOrderingOrdinals = New-Object 'System.Collections.Generic.HashSet[int]'
        for ($index = 0; $index -lt $rawEntries.Count; $index++) {
            $entryContext = "$context.entries[$index]"
            $entry = $rawEntries[$index]
            $entryId = Get-RequiredSourceString $entry "id" $entryContext
            Test-StableSourceId $entryId "$entryContext.id"
            if (-not $seenEntryIds.Add($entryId)) {
                throw "Source registry '$context.entries' repeats entry ID '$entryId'."
            }
            $targetType = Get-RequiredSourceString $entry "target_type" $entryContext
            if ($targetType -notin @("work", "segment", "content-group")) {
                throw "Source registry '$entryContext.target_type' must be 'work', 'segment', or 'content-group'."
            }
            $targetId = Get-RequiredSourceString $entry "target_id" $entryContext
            $targetRegistry = if ($targetType -eq "work") {
                $works
            }
            elseif ($targetType -eq "segment") {
                $segments
            }
            else {
                Get-ProjectMapValue $registry "content_groups"
            }
            if (-not $targetRegistry.Contains($targetId)) {
                throw "Source registry '$entryContext.target_id' references unknown $targetType '$targetId'."
            }
            $ordinal = Get-ProjectMapValue $entry "ordinal"
            $afterEntryIds = @(Get-SourceStringListAllowEmpty $entry "after_entry_ids" $entryContext)
            foreach ($predecessorId in $afterEntryIds) {
                Test-StableSourceId $predecessorId "$entryContext.after_entry_ids"
            }
            if ($orderingMode -eq "total") {
                if ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1) {
                    throw "Source registry '$entryContext.ordinal' must be a positive integer for total ordering."
                }
                if ($afterEntryIds.Count -gt 0) {
                    throw "Source registry '$entryContext.after_entry_ids' must be empty for total ordering."
                }
            }
            elseif ($null -ne $ordinal) {
                throw "Source registry '$entryContext.ordinal' must be omitted for partial ordering."
            }
            if (-not $seenTargets.Add("$targetType|$targetId")) {
                throw "Source registry '$context.entries' repeats a target."
            }
            if ($null -ne $ordinal -and -not $seenOrderingOrdinals.Add([int]$ordinal)) {
                throw "Source registry '$context.entries' repeats an ordinal."
            }
            $entries += [pscustomobject]@{ id=$entryId
                target_type=$targetType
                target_id=$targetId
                ordinal=if ($null -eq $ordinal) {
                    $null
                }
                else {
                    [int]$ordinal
                }
                after_entry_ids=@($afterEntryIds)
            }
        }
        if ($orderingMode -eq "partial") {
            foreach ($entry in $entries) {
                foreach ($predecessorId in $entry.after_entry_ids) {
                    if (-not $seenEntryIds.Contains($predecessorId)) {
                        throw "Source registry '$context' entry '$($entry.id)' references unknown predecessor '$predecessorId'."
                    }
                    if ($predecessorId -eq $entry.id) {
                        throw "Source registry '$context' entry '$($entry.id)' cannot follow itself."
                    }
                }
            }
            $remainingPredecessors = @{}
            foreach ($entry in $entries) {
                $remainingPredecessors[$entry.id] = [int]$entry.after_entry_ids.Count
            }
            $readyEntries = New-Object System.Collections.Queue
            foreach ($entry in $entries) {
                if ($remainingPredecessors[$entry.id] -eq 0) {
                    $readyEntries.Enqueue($entry.id)
                }
            }
            $processedEntries = 0
            while ($readyEntries.Count -gt 0) {
                $currentEntryId = [string]$readyEntries.Dequeue()
                $processedEntries++
                foreach ($dependent in @($entries | Where-Object { $_.after_entry_ids -ccontains $currentEntryId })) {
                    $remainingPredecessors[$dependent.id]--
                    if ($remainingPredecessors[$dependent.id] -eq 0) {
                        $readyEntries.Enqueue($dependent.id)
                    }
                }
            }
            if ($processedEntries -ne $entries.Count) {
                throw "Source registry '$context' contains a partial-order cycle."
            }
        }
        $orderingSchemes[$schemeId] = [pscustomobject]@{
            id=$schemeId
            label=Get-RequiredSourceString $scheme "label" $context
            ordering_type=$orderingType
            ordering_mode=$orderingMode
            entries=@(if ($orderingMode -eq "total") {
                    $entries | Sort-Object ordinal
                }
                else {
                    $entries
                })
        }
    }
    if ($orderingSchemes.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.ordering-type" @($orderingSchemes.Values | ForEach-Object { $_.ordering_type }) "ordering_schemes.*.ordering_type"
    }

    $rawContentGroups = Get-ProjectMapValue $registry "content_groups"
    if ($null -eq $rawContentGroups -or -not ($rawContentGroups -is [System.Collections.IDictionary])) {
        throw "Source registry 'content_groups' must be a mapping."
    }
    $contentGroups = [ordered]@{}
    $contentGroupAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $contentGroupIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($groupId in $rawContentGroups.Keys) {
        [void]$contentGroupIdKeys.Add((ConvertTo-KnowledgeLookupKey $groupId $lookupKeys))
    }
    foreach ($groupId in $rawContentGroups.Keys) {
        $context = "content_groups.$groupId"
        Test-StableSourceId $groupId $context
        $group = $rawContentGroups[$groupId]
        $rawMembers = @(Get-ProjectMapValue $group "members")
        if ($rawMembers.Count -eq 0) {
            throw "Source registry '$context.members' must be a non-empty list."
        }
        $members = @()
        $seenMembers = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $seenMemberIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        for ($memberIndex = 0; $memberIndex -lt $rawMembers.Count; $memberIndex++) {
            $memberContext = "$context.members[$memberIndex]"
            $member = $rawMembers[$memberIndex]
            $memberId = Get-RequiredSourceString $member "id" $memberContext
            Test-StableSourceId $memberId "$memberContext.id"
            if (-not $seenMemberIds.Add($memberId)) {
                throw "Source registry '$context.members' repeats ID '$memberId'."
            }
            $targetType = Get-RequiredSourceString $member "target_type" $memberContext
            $targetId = Get-RequiredSourceString $member "target_id" $memberContext
            $exists = if ($targetType -eq "work") {
                $works.Contains($targetId)
            }
            elseif ($targetType -eq "segment") {
                $segments.Contains($targetId)
            }
            elseif ($targetType -eq "content-group") {
                $rawContentGroups.Contains($targetId)
            }
            else {
                $false
            }
            if (-not $exists) {
                throw "Source registry '$memberContext' references unknown or unsupported $targetType '$targetId'."
            }
            if (-not $seenMembers.Add("$targetType|$targetId")) {
                throw "Source registry '$context.members' contains duplicates."
            }
            $role = Get-RequiredSourceString $member "role" $memberContext
            Assert-SourceSchemaPackValues $SchemaPackRegistry "source.content-group-member-role" @($role) "$memberContext.role"
            $members += [pscustomobject]@{id=$memberId
                target_type=$targetType
                target_id=$targetId
                role=$role
            }
        }
        $parentGroupIds = @(Get-SourceStringListAllowEmpty $group "parent_group_ids" $context)
        if ($parentGroupIds -ccontains $groupId -or @($parentGroupIds | Sort-Object -Unique).Count -ne $parentGroupIds.Count) {
            throw "Source registry '$context.parent_group_ids' contains a self reference or duplicate."
        }
        $orderingSchemeId = Get-OptionalSourceString $group "ordering_scheme_id" $context
        if ($null -ne $orderingSchemeId) {
            if (-not $orderingSchemes.Contains($orderingSchemeId)) {
                throw "Source registry '$context.ordering_scheme_id' references unknown ordering scheme '$orderingSchemeId'."
            }
            $orderedEntries = @($orderingSchemes[$orderingSchemeId].entries)
            $orderedMembers = @($orderedEntries | ForEach-Object { "$($_.target_type)|$($_.target_id)" } | Sort-Object)
            $memberKeys = @($members | ForEach-Object { "$($_.target_type)|$($_.target_id)" } | Sort-Object)
            if (Compare-Object $memberKeys $orderedMembers) {
                throw "Source registry '$context.ordering_scheme_id' must order exactly the group's members."
            }
        }
        $aliases = @(Get-SourceStringListAllowEmpty $group "aliases" $context)
        foreach ($alias in $aliases) {
            Test-StableSourceId $alias "$context.aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($contentGroupIdKeys.Contains($aliasKey) -or -not $contentGroupAliasKeys.Add($aliasKey)) {
                throw "Source registry content-group alias '$alias' is duplicated or collides with a group ID."
            }
        }
        $lifecycle = Get-RequiredSourceString $group "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $contentGroups[$groupId] = [pscustomobject]@{id=$groupId
            lifecycle=$lifecycle
            label=Get-RequiredSourceString $group "label" $context
            group_type=Get-RequiredSourceString $group "group_type" $context
            members=@($members)
            parent_group_ids=@($parentGroupIds)
            ordering_scheme_id=$orderingSchemeId
            localized_titles=@(ConvertTo-SourceLocalizedTitles $group $context $SchemaPackRegistry)
            aliases=@($aliases)
        }
    }
    if ($contentGroups.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.content-group-type" @($contentGroups.Values | ForEach-Object { $_.group_type }) "content_groups.*.group_type"
    }
    foreach ($group in $contentGroups.Values) {
        foreach ($parentId in $group.parent_group_ids) {
            if (-not $contentGroups.Contains($parentId)) {
                throw "Source registry content group '$($group.id)' references unknown parent '$parentId'."
            }
        }
    }
    $remainingGroupParents = @{}
    $readyGroups = New-Object System.Collections.Queue
    foreach ($group in $contentGroups.Values) {
        $deps = @($group.parent_group_ids) + @($group.members | Where-Object { $_.target_type -eq "content-group" } | ForEach-Object { $_.target_id })
        $remainingGroupParents[$group.id] = [int]$deps.Count
        if ($deps.Count -eq 0) {
            $readyGroups.Enqueue($group.id)
        }
    }
    $processedGroups = 0
    while ($readyGroups.Count -gt 0) {
        $currentGroupId = [string]$readyGroups.Dequeue()
        $processedGroups++
        $childGroups = @(
            $contentGroups.Values | Where-Object {
                $containsParent = $_.parent_group_ids -ccontains $currentGroupId
                $containsMember = @(
                    $_.members | Where-Object {
                        $_.target_type -eq "content-group" -and
                        $_.target_id -eq $currentGroupId
                    }
                ).Count -gt 0
                $containsParent -or $containsMember
            }
        )
        foreach ($child in $childGroups) {
            $remainingGroupParents[$child.id]--
            if ($remainingGroupParents[$child.id] -eq 0) {
                $readyGroups.Enqueue($child.id)
            }
        }
    }
    if ($processedGroups -ne $contentGroups.Count) {
        throw "Source registry contains a content-group cycle."
    }

    $workRelationships = @()
    $rawWorkRelationships = @(Get-ProjectMapValue $registry "work_relationships")
    for ($index = 0; $index -lt $rawWorkRelationships.Count; $index++) {
        $context = "work_relationships[$index]"
        $relationship = $rawWorkRelationships[$index]
        $id = Get-RequiredSourceString $relationship "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenRelationshipIds.Add($id)) {
            throw "Source registry relationship ID '$id' is duplicated."
        }
        $sourceId = Get-RequiredSourceString $relationship "source_work_id" $context
        $targetId = Get-RequiredSourceString $relationship "target_work_id" $context
        $type = Get-RequiredSourceString $relationship "relationship_type" $context
        if (-not $works.Contains($sourceId) -or -not $works.Contains($targetId)) {
            throw "Source registry '$context' references an unknown work."
        }
        if ($sourceId -eq $targetId) {
            throw "Source registry '$context' cannot relate a work to itself."
        }
        if (-not $workRelationshipTypes.Contains($type)) {
            throw "Source registry '$context.relationship_type' references unknown type '$type'."
        }
        $continuityIds = @(Get-SourceStringList $relationship "continuity_ids" $context)
        foreach ($continuityId in $continuityIds) {
            if (-not $continuities.Contains($continuityId)) {
                throw "Source registry '$context.continuity_ids' references unknown continuity '$continuityId'."
            }
        }
        $status = Get-RequiredSourceString $relationship "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')."
        }
        $workRelationships += [pscustomobject]@{ id=$id
            source_work_id=$sourceId
            relationship_type=$type
            target_work_id=$targetId
            continuity_ids=@($continuityIds)
            status=$status
            applicability_scope_id=Get-OptionalSourceString $relationship "applicability_scope_id" $context
        }
    }

    $adaptationMappings = @()
    $rawAdaptationMappings = @(Get-ProjectMapValue $registry "adaptation_mappings")
    $seenAdaptationMappingIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawAdaptationMappings.Count; $index++) {
        $context = "adaptation_mappings[$index]"
        $mapping = $rawAdaptationMappings[$index]
        $id = Get-RequiredSourceString $mapping "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenAdaptationMappingIds.Add($id)) {
            throw "Source registry adaptation mapping ID '$id' is duplicated."
        }
        $targetWorkId = Get-RequiredSourceString $mapping "target_work_id" $context
        if (-not $works.Contains($targetWorkId)) {
            throw "Source registry '$context.target_work_id' references an unknown work."
        }
        $targetSegmentIds = @(Get-SourceStringListAllowEmpty $mapping "target_segment_ids" $context)
        foreach ($segmentId in $targetSegmentIds) {
            if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $targetWorkId) {
                throw "Source registry '$context.target_segment_ids' references segment '$segmentId' outside target work '$targetWorkId'."
            }
        }
        $rawBasisInputs = @(Get-ProjectMapValue $mapping "basis_inputs")
        if ($rawBasisInputs.Count -eq 0) {
            throw "Source registry '$context.basis_inputs' must be a non-empty list."
        }
        $basisInputs = @()
        $seenBasisWorks = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        foreach ($basis in $rawBasisInputs) {
            $workId = Get-RequiredSourceString $basis "work_id" "$context.basis_inputs"
            if (-not $works.Contains($workId)) {
                throw "Source registry '$context.basis_inputs.work_id' references unknown work '$workId'."
            }
            if ($workId -eq $targetWorkId -or -not $seenBasisWorks.Add($workId)) {
                throw "Source registry '$context.basis_inputs' repeats a work or uses the target as its own basis."
            }
            $segmentIds = @(Get-SourceStringListAllowEmpty $basis "segment_ids" "$context.basis_inputs")
            foreach ($segmentId in $segmentIds) {
                if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $workId) {
                    throw "Source registry '$context.basis_inputs.segment_ids' references segment '$segmentId' outside work '$workId'."
                }
            }
            $basisInputs += [pscustomobject]@{ work_id=$workId
                segment_ids=@($segmentIds)
                basis_role=Get-RequiredSourceString $basis "basis_role" "$context.basis_inputs"
            }
        }
        $mappingType = Get-RequiredSourceString $mapping "mapping_type" $context
        $status = Get-RequiredSourceString $mapping "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')."
        }
        $adaptationMappings += [pscustomobject]@{
            id=$id
            basis_inputs=@($basisInputs)
            target_work_id=$targetWorkId
            target_segment_ids=@($targetSegmentIds)
            mapping_type=$mappingType
            status=$status
        }
    }
    if ($adaptationMappings.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.adaptation-mapping-type" @($adaptationMappings | ForEach-Object { $_.mapping_type }) "adaptation_mappings.*.mapping_type"
        $adaptationBasisRoles = @(
            $adaptationMappings |
                ForEach-Object { $_.basis_inputs } |
                ForEach-Object { $_.basis_role }
        )
        Assert-SourceSchemaPackValues `
            $SchemaPackRegistry `
            "source.adaptation-basis-role" `
            $adaptationBasisRoles `
            "adaptation_mappings.*.basis_inputs.*.basis_role"
    }

    $rawTerritories = Get-ProjectMapValue $registry "territories"
    if ($null -eq $rawTerritories -or -not ($rawTerritories -is [System.Collections.IDictionary])) {
        throw "Source registry 'territories' must be a mapping."
    }
    $territories = [ordered]@{}
    foreach ($territoryId in $rawTerritories.Keys) {
        $context = "territories.$territoryId"
        Test-StableSourceId $territoryId $context
        $territory = $rawTerritories[$territoryId]
        $lifecycle = Get-RequiredSourceString $territory "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $codes = [ordered]@{}
        $rawCodes = Get-ProjectMapValue $territory "codes"
        if ($null -eq $rawCodes -or -not ($rawCodes -is [System.Collections.IDictionary])) {
            throw "Source registry '$context.codes' must be a mapping."
        }
        foreach ($schemeId in $rawCodes.Keys) {
            Test-StableSourceId $schemeId "$context.codes"
            if ($rawCodes[$schemeId] -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$rawCodes[$schemeId])) {
                throw "Source registry '$context.codes.$schemeId' must be a non-empty string."
            }
            $codes[$schemeId] = ([string]$rawCodes[$schemeId]).Trim()
        }
        $territories[$territoryId] = [pscustomobject]@{
            id=$territoryId
            lifecycle=$lifecycle
            label=Get-RequiredSourceString $territory "label" $context
            territory_type=Get-RequiredSourceString $territory "territory_type" $context
            parent_territory_id=Get-OptionalSourceString $territory "parent_territory_id" $context
            codes=$codes
        }
    }
    if ($territories.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.territory-type" @($territories.Values | ForEach-Object { $_.territory_type }) "territories.*.territory_type"
    }
    foreach ($territory in $territories.Values) {
        if ($null -eq $territory.parent_territory_id) {
            continue
        }
        if (-not $territories.Contains($territory.parent_territory_id)) {
            throw "Source registry territory '$($territory.id)' references unknown parent '$($territory.parent_territory_id)'."
        }
        if ($territory.parent_territory_id -eq $territory.id) {
            throw "Source registry territory '$($territory.id)' cannot parent itself."
        }
    }
    foreach ($territoryId in $territories.Keys) {
        $seenTerritories = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $currentTerritoryId = $territoryId
        while ($null -ne $currentTerritoryId) {
            if (-not $seenTerritories.Add($currentTerritoryId)) {
                throw "Source registry contains a territory cycle involving '$currentTerritoryId'."
            }
            $currentTerritoryId = $territories[$currentTerritoryId].parent_territory_id
        }
    }
    $seenTerritoryCodes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($territory in $territories.Values) {
        foreach ($schemeId in $territory.codes.Keys) {
            $codeKey = ConvertTo-KnowledgeLookupKey ([string]$territory.codes[$schemeId]) $lookupKeys
            if (-not $seenTerritoryCodes.Add("$schemeId|$codeKey")) {
                throw "Source registry repeats territory code '${schemeId}:$($territory.codes[$schemeId])'."
            }
        }
    }

    if (-not $registry.Contains("work_production_contexts")) {
        throw "Source registry 'work_production_contexts' must be a list."
    }
    $rawWorkProductionContexts = $registry["work_production_contexts"]
    if ($null -eq $rawWorkProductionContexts) {
        $rawWorkProductionContexts = @()
    }
    elseif ($rawWorkProductionContexts -isnot [System.Collections.IList]) {
        throw "Source registry 'work_production_contexts' must be a list."
    }
    $workProductionContexts = [ordered]@{}
    for ($index = 0; $index -lt $rawWorkProductionContexts.Count; $index++) {
        $context = "work_production_contexts[$index]"
        $productionContext = $rawWorkProductionContexts[$index]
        $id = Get-RequiredSourceString $productionContext "id" $context
        Test-StableSourceId $id "$context.id"
        if ($workProductionContexts.Contains($id)) {
            throw "Source registry work-production-context ID '$id' is duplicated."
        }
        $workId = Get-RequiredSourceString $productionContext "work_id" $context
        if (-not $works.Contains($workId)) {
            throw "Source registry '$context.work_id' references unknown work '$workId'."
        }
        $productionOrigin = Get-RequiredSourceString $productionContext "production_origin" $context
        $authorizationStatus = Get-RequiredSourceString $productionContext "authorization_status" $context
        $rightsBasis = Get-RequiredSourceString $productionContext "rights_basis" $context
        $commerciality = Get-RequiredSourceString $productionContext "commerciality" $context
        $applicabilityScopeId = Get-RequiredSourceString $productionContext "applicability_scope_id" $context
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.production-origin" @($productionOrigin) "$context.production_origin"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.authorization-status" @($authorizationStatus) "$context.authorization_status"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.rights-basis" @($rightsBasis) "$context.rights_basis"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.commerciality" @($commerciality) "$context.commerciality"
        $workProductionContexts[$id] = [pscustomobject]@{id=$id
            work_id=$workId
            production_origin=$productionOrigin
            authorization_status=$authorizationStatus
            rights_basis=$rightsBasis
            commerciality=$commerciality
            applicability_scope_id=$applicabilityScopeId
        }
    }
    foreach ($owner in @($works.Values) + @($segments.Values) + @($contentGroups.Values)) {
        foreach ($localizedTitle in $owner.localized_titles) {
            foreach ($territoryId in $localizedTitle.territory_ids) {
                if (-not $territories.Contains($territoryId)) {
                    throw "Source registry localized title references unknown territory '$territoryId'."
                }
            }
        }
    }

    $rawPlatforms = Get-ProjectMapValue $registry "platforms"
    if ($null -eq $rawPlatforms -or -not ($rawPlatforms -is [System.Collections.IDictionary])) {
        throw "Source registry 'platforms' must be a mapping."
    }
    $platforms = [ordered]@{}
    $platformAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $platformIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($platformId in $rawPlatforms.Keys) {
        [void]$platformIdKeys.Add((ConvertTo-KnowledgeLookupKey $platformId $lookupKeys))
    }
    foreach ($platformId in $rawPlatforms.Keys) {
        $context = "platforms.$platformId"
        Test-StableSourceId $platformId $context
        $platform = $rawPlatforms[$platformId]
        $aliases = @(Get-SourceStringListAllowEmpty $platform "aliases" $context)
        foreach ($alias in $aliases) {
            Test-StableSourceId $alias "$context.aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($platformIdKeys.Contains($aliasKey) -or -not $platformAliasKeys.Add($aliasKey)) {
                throw "Source registry platform alias '$alias' is duplicated or collides with a platform ID."
            }
        }
        $platforms[$platformId] = [pscustomobject]@{
            id=$platformId
            lifecycle=Get-RequiredSourceString $platform "lifecycle" $context
            label=Get-RequiredSourceString $platform "label" $context
            platform_type=Get-RequiredSourceString $platform "platform_type" $context
            aliases=@($aliases)
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $platforms[$platformId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }
    if ($platforms.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.platform-type" @($platforms.Values | ForEach-Object { $_.platform_type }) "platforms.*.platform_type"
    }

    $manifestationRelationshipTypes = ConvertTo-RelationshipTypeRegistry (Get-ProjectMapValue $registry "manifestation_relationship_types") "manifestation_relationship_types"
    if ($manifestationRelationshipTypes.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.manifestation-relationship-type" @($manifestationRelationshipTypes.Keys) "manifestation_relationship_types"
    }

    $rawManifestations = Get-ProjectMapValue $registry "manifestations"
    if ($null -eq $rawManifestations -or -not ($rawManifestations -is [System.Collections.IDictionary])) {
        throw "Source registry 'manifestations' must be a mapping."
    }
    $manifestations = [ordered]@{}
    $manifestationAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $manifestationIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($manifestationId in $rawManifestations.Keys) {
        [void]$manifestationIdKeys.Add((ConvertTo-KnowledgeLookupKey $manifestationId $lookupKeys))
    }
    foreach ($manifestationId in $rawManifestations.Keys) {
        $context = "manifestations.$manifestationId"
        Test-StableSourceId $manifestationId $context
        $manifestation = $rawManifestations[$manifestationId]
        $workId = Get-RequiredSourceString $manifestation "work_id" $context
        if (-not $works.Contains($workId)) {
            throw "Source registry '$context.work_id' references unknown work '$workId'."
        }
        $manifestationSegmentIds = @(Get-SourceStringListAllowEmpty $manifestation "segment_ids" $context)
        foreach ($segmentId in $manifestationSegmentIds) {
            if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $workId) {
                throw "Source registry '$context.segment_ids' references segment '$segmentId' outside work '$workId'."
            }
        }
        $containerFormatIds = @(Get-SourceStringListAllowEmpty $manifestation "container_format_ids" $context)
        foreach ($formatId in $containerFormatIds) {
            if (-not $containerFormats.Contains($formatId)) {
                throw "Source registry '$context.container_format_ids' references unknown format '$formatId'."
            }
        }
        $localizedTitles = @(ConvertTo-SourceLocalizedTitles $manifestation $context $SchemaPackRegistry)
        foreach ($localizedTitle in $localizedTitles) {
            foreach ($territoryId in $localizedTitle.territory_ids) {
                if (-not $territories.Contains($territoryId)) {
                    throw "Source registry '$context.localized_titles' references unknown territory '$territoryId'."
                }
            }
        }
        $aliases = @(Get-SourceStringListAllowEmpty $manifestation "aliases" $context)
        foreach ($alias in $aliases) {
            Test-StableSourceId $alias "$context.aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($manifestationIdKeys.Contains($aliasKey) -or -not $manifestationAliasKeys.Add($aliasKey)) {
                throw "Source registry manifestation alias '$alias' is duplicated or collides with a manifestation ID."
            }
        }
        $languageTags = @(Get-SourceStringListAllowEmpty $manifestation "language_tags" $context)
        foreach ($languageTag in $languageTags) {
            Test-SourceLanguageTag $languageTag "$context.language_tags"
        }
        $territoryIds = @(Get-SourceStringListAllowEmpty $manifestation "territory_ids" $context)
        foreach ($territoryId in $territoryIds) {
            if (-not $territories.Contains($territoryId)) {
                throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'."
            }
        }
        $manifestations[$manifestationId] = [pscustomobject]@{
            id=$manifestationId
            lifecycle=Get-RequiredSourceString $manifestation "lifecycle" $context
            label=Get-RequiredSourceString $manifestation "label" $context
            work_id=$workId
            segment_ids=@($manifestationSegmentIds)
            manifestation_type=Get-RequiredSourceString $manifestation "manifestation_type" $context
            language_tags=@($languageTags)
            territory_ids=@($territoryIds)
            container_format_ids=@($containerFormatIds)
            localized_titles=@($localizedTitles)
            aliases=@($aliases)
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $manifestations[$manifestationId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }
    if ($manifestations.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.manifestation-type" @($manifestations.Values | ForEach-Object { $_.manifestation_type }) "manifestations.*.manifestation_type"
    }

    $manifestationRelationships = @()
    $seenManifestationRelationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($relationship in @(Get-ProjectMapValue $registry "manifestation_relationships")) {
        $context = "manifestation_relationships"
        $id = Get-RequiredSourceString $relationship "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenManifestationRelationshipIds.Add($id)) {
            throw "Source registry manifestation relationship ID '$id' is duplicated."
        }
        $sourceId = Get-RequiredSourceString $relationship "source_manifestation_id" $context
        $targetId = Get-RequiredSourceString $relationship "target_manifestation_id" $context
        $type = Get-RequiredSourceString $relationship "relationship_type" $context
        $status = Get-RequiredSourceString $relationship "status" $context
        if (-not $manifestations.Contains($sourceId) -or -not $manifestations.Contains($targetId)) {
            throw "Source registry '$context' references an unknown manifestation."
        }
        if ($sourceId -eq $targetId) {
            throw "Source registry '$context' cannot relate a manifestation to itself."
        }
        if (-not $manifestationRelationshipTypes.Contains($type)) {
            throw "Source registry '$context.relationship_type' references unknown type '$type'."
        }
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')."
        }
        $manifestationRelationships += [pscustomobject]@{ id=$id
            source_manifestation_id=$sourceId
            relationship_type=$type
            target_manifestation_id=$targetId
            status=$status
        }
    }

    $relatedManifestationPairs = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($relationship in $manifestationRelationships) {
        [void]$relatedManifestationPairs.Add((@($relationship.source_manifestation_id, $relationship.target_manifestation_id) | Sort-Object) -join "|")
    }
    $manifestationSegmentMappings = @()
    $seenManifestationMappingIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawManifestationSegmentMappings = @(Get-ProjectMapValue $registry "manifestation_segment_mappings")
    for ($index = 0; $index -lt $rawManifestationSegmentMappings.Count; $index++) {
        $context = "manifestation_segment_mappings[$index]"
        $mapping = $rawManifestationSegmentMappings[$index]
        $id = Get-RequiredSourceString $mapping "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenManifestationMappingIds.Add($id)) {
            throw "Source registry manifestation segment mapping ID '$id' is duplicated."
        }
        $sourceId = Get-RequiredSourceString $mapping "source_manifestation_id" $context
        $targetId = Get-RequiredSourceString $mapping "target_manifestation_id" $context
        if (-not $manifestations.Contains($sourceId) -or -not $manifestations.Contains($targetId)) {
            throw "Source registry '$context' references an unknown manifestation."
        }
        if ($sourceId -eq $targetId) {
            throw "Source registry '$context' cannot map a manifestation to itself."
        }
        if ($manifestations[$sourceId].work_id -ne $manifestations[$targetId].work_id) {
            throw "Source registry '$context' must map manifestations of the same work."
        }
        if (-not $relatedManifestationPairs.Contains((@($sourceId, $targetId) | Sort-Object) -join "|")) {
            throw "Source registry '$context' requires a manifestation relationship between its source and target."
        }
        $sourceSegmentIds = @(Get-SourceStringListAllowEmpty $mapping "source_segment_ids" $context)
        $targetSegmentIds = @(Get-SourceStringListAllowEmpty $mapping "target_segment_ids" $context)
        foreach ($scope in @([pscustomobject]@{name="source_segment_ids"
                    ids=$sourceSegmentIds
                    manifestation_id=$sourceId
                }, [pscustomobject]@{name="target_segment_ids"
                    ids=$targetSegmentIds
                    manifestation_id=$targetId
                })) {
            foreach ($segmentId in $scope.ids) {
                $scopeManifestation = $manifestations[$scope.manifestation_id]
                $isOutsideManifestation = (
                    $scopeManifestation.segment_ids.Count -gt 0 -and
                    $scopeManifestation.segment_ids -cnotcontains $segmentId
                )
                if (
                    -not $segments.Contains($segmentId) -or
                    $segments[$segmentId].work_id -ne $scopeManifestation.work_id -or
                    $isOutsideManifestation
                ) {
                    throw "Source registry '$context.$($scope.name)' references segment '$segmentId' outside manifestation scope."
                }
            }
        }
        $mappingType = Get-RequiredSourceString $mapping "mapping_type" $context
        $validShape = if ($mappingType -eq "omitted") {
            $sourceSegmentIds.Count -gt 0 -and $targetSegmentIds.Count -eq 0
        }
        elseif ($mappingType -eq "added") {
            $sourceSegmentIds.Count -eq 0 -and $targetSegmentIds.Count -gt 0
        }
        else {
            $sourceSegmentIds.Count -gt 0 -and $targetSegmentIds.Count -gt 0
        }
        if (-not $validShape) {
            throw "Source registry '$context' has segment lists incompatible with mapping type '$mappingType'."
        }
        $status = Get-RequiredSourceString $mapping "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')."
        }
        $manifestationSegmentMappings += [pscustomobject]@{id=$id
            source_manifestation_id=$sourceId
            source_segment_ids=@($sourceSegmentIds)
            target_manifestation_id=$targetId
            target_segment_ids=@($targetSegmentIds)
            mapping_type=$mappingType
            status=$status
        }
    }
    if ($manifestationSegmentMappings.Count -gt 0) {
        $manifestationMappingTypes = @(
            $manifestationSegmentMappings | ForEach-Object { $_.mapping_type }
        )
        Assert-SourceSchemaPackValues `
            $SchemaPackRegistry `
            "source.manifestation-segment-mapping-type" `
            $manifestationMappingTypes `
            "manifestation_segment_mappings.*.mapping_type"
    }

    $rawReleaseComponents = Get-ProjectMapValue $registry "release_components"
    if ($null -eq $rawReleaseComponents -or -not ($rawReleaseComponents -is [System.Collections.IDictionary])) {
        throw "Source registry 'release_components' must be a mapping."
    }
    $releaseComponents = [ordered]@{}
    foreach ($componentId in $rawReleaseComponents.Keys) {
        $context = "release_components.$componentId"
        Test-StableSourceId $componentId $context
        $component = $rawReleaseComponents[$componentId]
        $manifestationId = Get-OptionalSourceString $component "manifestation_id" $context
        if ($null -ne $manifestationId -and -not $manifestations.Contains($manifestationId)) {
            throw "Source registry '$context.manifestation_id' references unknown manifestation '$manifestationId'."
        }
        $segmentIds = @(Get-SourceStringListAllowEmpty $component "segment_ids" $context)
        foreach ($segmentId in $segmentIds) {
            if (-not $segments.Contains($segmentId)) {
                throw "Source registry '$context.segment_ids' references unknown segment '$segmentId'."
            }
            $mappingManifestation = if ($null -ne $manifestationId) {
                $manifestations[$manifestationId]
            }
            else {
                $null
            }
            $isOutsideManifestation = (
                $null -ne $mappingManifestation -and
                $mappingManifestation.segment_ids.Count -gt 0 -and
                $mappingManifestation.segment_ids -cnotcontains $segmentId
            )
            if (
                $null -ne $mappingManifestation -and
                (
                    $segments[$segmentId].work_id -ne $mappingManifestation.work_id -or
                    $isOutsideManifestation
                )
            ) {
                throw "Source registry '$context.segment_ids' references segment '$segmentId' outside manifestation scope."
            }
        }
        $languageTag = Get-OptionalSourceString $component "language_tag" $context
        if ($null -ne $languageTag) {
            Test-SourceLanguageTag $languageTag "$context.language_tag"
        }
        $releaseComponents[$componentId] = [pscustomobject]@{
            id=$componentId
            lifecycle=Get-RequiredSourceString $component "lifecycle" $context
            label=Get-RequiredSourceString $component "label" $context
            manifestation_id=$manifestationId
            component_type=Get-RequiredSourceString $component "component_type" $context
            segment_ids=@($segmentIds)
            language_tag=$languageTag
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $releaseComponents[$componentId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }
    if ($releaseComponents.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-component-type" @($releaseComponents.Values | ForEach-Object { $_.component_type }) "release_components.*.component_type"
    }

    $releaseComponentRelationshipTypes = ConvertTo-RelationshipTypeRegistry (Get-ProjectMapValue $registry "release_component_relationship_types") "release_component_relationship_types"
    if ($releaseComponentRelationshipTypes.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-component-relationship-type" @($releaseComponentRelationshipTypes.Keys) "release_component_relationship_types"
    }
    $releaseComponentRelationships = @()
    $seenComponentRelationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $rawComponentRelationships = @(Get-ProjectMapValue $registry "release_component_relationships")
    for ($index = 0; $index -lt $rawComponentRelationships.Count; $index++) {
        $context = "release_component_relationships[$index]"
        $relationship = $rawComponentRelationships[$index]
        $id = Get-RequiredSourceString $relationship "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenComponentRelationshipIds.Add($id)) {
            throw "Source registry release-component relationship ID '$id' is duplicated."
        }
        $sourceComponentId = Get-RequiredSourceString $relationship "source_component_id" $context
        $targetComponentId = Get-RequiredSourceString $relationship "target_component_id" $context
        if (-not $releaseComponents.Contains($sourceComponentId) -or -not $releaseComponents.Contains($targetComponentId)) {
            throw "Source registry '$context' references an unknown release component."
        }
        if ($sourceComponentId -eq $targetComponentId) {
            throw "Source registry '$context' cannot relate a component to itself."
        }
        $relationshipType = Get-RequiredSourceString $relationship "relationship_type" $context
        if (-not $releaseComponentRelationshipTypes.Contains($relationshipType)) {
            throw "Source registry '$context.relationship_type' references unknown type '$relationshipType'."
        }
        $releaseComponentRelationships += [pscustomobject]@{id=$id
            source_component_id=$sourceComponentId
            relationship_type=$relationshipType
            target_component_id=$targetComponentId
        }
    }

    $rawReleasePackages = Get-ProjectMapValue $registry "release_packages"
    if ($null -eq $rawReleasePackages -or -not ($rawReleasePackages -is [System.Collections.IDictionary])) {
        throw "Source registry 'release_packages' must be a mapping."
    }
    $releasePackages = [ordered]@{}
    $releasePackageAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $releasePackageIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($packageId in $rawReleasePackages.Keys) {
        [void]$releasePackageIdKeys.Add((ConvertTo-KnowledgeLookupKey $packageId $lookupKeys))
    }
    foreach ($packageId in $rawReleasePackages.Keys) {
        $context = "release_packages.$packageId"
        Test-StableSourceId $packageId $context
        $package = $rawReleasePackages[$packageId]
        $manifestationIds = @(Get-SourceStringListAllowEmpty $package "manifestation_ids" $context)
        $segmentIds = @(Get-SourceStringListAllowEmpty $package "segment_ids" $context)
        $componentIds = @(Get-SourceStringListAllowEmpty $package "release_component_ids" $context)
        $containerFormatIds = @(Get-SourceStringListAllowEmpty $package "container_format_ids" $context)
        if ($manifestationIds.Count -eq 0 -and $segmentIds.Count -eq 0 -and $componentIds.Count -eq 0) {
            throw "Source registry '$context' must identify at least one manifestation, segment, or release component."
        }
        foreach ($manifestationId in $manifestationIds) {
            if (-not $manifestations.Contains($manifestationId)) {
                throw "Source registry '$context.manifestation_ids' references unknown manifestation '$manifestationId'."
            }
        }
        $packageWorkIds = @($manifestationIds | ForEach-Object { $manifestations[$_].work_id } | Sort-Object -Unique)
        foreach ($segmentId in $segmentIds) {
            if (-not $segments.Contains($segmentId)) {
                throw "Source registry '$context.segment_ids' references unknown segment '$segmentId'."
            }
            if ($packageWorkIds.Count -gt 0 -and $packageWorkIds -cnotcontains $segments[$segmentId].work_id) {
                throw "Source registry '$context.segment_ids' references segment '$segmentId' outside the package manifestations."
            }
        }
        foreach ($componentId in $componentIds) {
            if (-not $releaseComponents.Contains($componentId)) {
                throw "Source registry '$context.release_component_ids' references unknown component '$componentId'."
            }
            if ($manifestationIds.Count -gt 0 -and $null -ne $releaseComponents[$componentId].manifestation_id -and $manifestationIds -cnotcontains $releaseComponents[$componentId].manifestation_id) {
                throw "Source registry '$context.release_component_ids' references component '$componentId' outside the package manifestations."
            }
        }
        $effectiveManifestationIds = @($manifestationIds + @($componentIds | ForEach-Object { $releaseComponents[$_].manifestation_id } | Where-Object { $null -ne $_ }) | Sort-Object -Unique)
        $packageWorkIds = @($effectiveManifestationIds | ForEach-Object { $manifestations[$_].work_id } | Sort-Object -Unique)
        foreach ($segmentId in $segmentIds) {
            if ($packageWorkIds.Count -gt 0 -and $packageWorkIds -cnotcontains $segments[$segmentId].work_id) {
                throw "Source registry '$context.segment_ids' references segment '$segmentId' outside the package manifestations."
            }
        }
        foreach ($containerFormatId in $containerFormatIds) {
            if (-not $containerFormats.Contains($containerFormatId)) {
                throw "Source registry '$context.container_format_ids' references unknown container format '$containerFormatId'."
            }
        }
        $aliases = @(Get-SourceStringListAllowEmpty $package "aliases" $context)
        foreach ($alias in $aliases) {
            Test-StableSourceId $alias "$context.aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($releasePackageIdKeys.Contains($aliasKey) -or -not $releasePackageAliasKeys.Add($aliasKey)) {
                throw "Source registry release-package alias '$alias' is duplicated or collides with a package ID."
            }
        }
        $localizedTitles = @(ConvertTo-SourceLocalizedTitles $package $context $SchemaPackRegistry)
        foreach ($localizedTitle in $localizedTitles) {
            foreach ($territoryId in $localizedTitle.territory_ids) {
                if (-not $territories.Contains($territoryId)) {
                    throw "Source registry '$context.localized_titles' references unknown territory '$territoryId'."
                }
            }
        }
        $releasePackages[$packageId] = [pscustomobject]@{
            id=$packageId
            lifecycle=Get-RequiredSourceString $package "lifecycle" $context
            label=Get-RequiredSourceString $package "label" $context
            package_type=Get-RequiredSourceString $package "package_type" $context
            manifestation_ids=@($manifestationIds)
            segment_ids=@($segmentIds)
            release_component_ids=@($componentIds)
            container_format_ids=@($containerFormatIds)
            localized_titles=@($localizedTitles)
            aliases=@($aliases)
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $releasePackages[$packageId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }
    if ($releasePackages.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-package-type" @($releasePackages.Values | ForEach-Object { $_.package_type }) "release_packages.*.package_type"
    }

    $packagesByComponent = @{}
    foreach ($componentId in $releaseComponents.Keys) {
        $packagesByComponent[$componentId] = @()
    }
    foreach ($package in $releasePackages.Values) {
        foreach ($componentId in $package.release_component_ids) {
            $packagesByComponent[$componentId] = @($packagesByComponent[$componentId] + $package.id)
        }
    }
    foreach ($component in $releaseComponents.Values) {
        if ($null -eq $component.manifestation_id -and $packagesByComponent[$component.id].Count -eq 0) {
            throw "Source registry release component '$($component.id)' has no manifestation and is not included in a release package."
        }
        foreach ($packageId in $packagesByComponent[$component.id]) {
            $package = $releasePackages[$packageId]
            $packageWorkIds = @($package.manifestation_ids | ForEach-Object { $manifestations[$_].work_id })
            $packageWorkIds += @($package.segment_ids | ForEach-Object { $segments[$_].work_id })
            if ($null -ne $component.manifestation_id) {
                $packageWorkIds += @($manifestations[$component.manifestation_id].work_id)
            }
            $packageWorkIds = @($packageWorkIds | Sort-Object -Unique)
            $componentWorkIds = @($component.segment_ids | ForEach-Object { $segments[$_].work_id } | Sort-Object -Unique)
            if ($packageWorkIds.Count -gt 0 -and @($componentWorkIds | Where-Object { $packageWorkIds -cnotcontains $_ }).Count -gt 0) {
                throw "Source registry release component '$($component.id)' has segment scope outside package '$packageId'."
            }
        }
    }
    $getReleasePackageWorkIds = {
        param([string]$PackageId)
        $package = $releasePackages[$PackageId]
        $workIds = @($package.manifestation_ids | ForEach-Object { $manifestations[$_].work_id })
        $workIds += @($package.segment_ids | ForEach-Object { $segments[$_].work_id })
        foreach ($componentId in $package.release_component_ids) {
            $component = $releaseComponents[$componentId]
            if ($null -ne $component.manifestation_id) {
                $workIds += @($manifestations[$component.manifestation_id].work_id)
            }
            $workIds += @($component.segment_ids | ForEach-Object { $segments[$_].work_id })
        }
        return @($workIds | Sort-Object -Unique)
    }

    $validateDistributionScope = {
        param([string]$SubjectType, [string]$SubjectId, [object[]]$SegmentIds, [string]$Context)
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.distribution-subject-type" @($SubjectType) "$Context.subject_type"
        if ($SubjectType -eq "manifestation") {
            if (-not $manifestations.Contains($SubjectId)) {
                throw "Source registry '$Context.subject_id' references unknown manifestation '$SubjectId'."
            }
            foreach ($segmentId in $SegmentIds) {
                if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $manifestations[$SubjectId].work_id) {
                    throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside manifestation work."
                }
                if ($manifestations[$SubjectId].segment_ids.Count -gt 0 -and $manifestations[$SubjectId].segment_ids -cnotcontains $segmentId) {
                    throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside manifestation scope."
                }
            }
            return
        }
        if ($SubjectType -eq "release-package") {
            if (-not $releasePackages.Contains($SubjectId)) {
                throw "Source registry '$Context.subject_id' references unknown release package '$SubjectId'."
            }
            foreach ($segmentId in $SegmentIds) {
                if (-not $segments.Contains($segmentId)) {
                    throw "Source registry '$Context.segment_ids' references unknown segment '$segmentId'."
                }
                if ($releasePackages[$SubjectId].segment_ids.Count -gt 0 -and $releasePackages[$SubjectId].segment_ids -cnotcontains $segmentId) {
                    throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside release-package scope."
                }
                if ($releasePackages[$SubjectId].segment_ids.Count -eq 0) {
                    $packageWorkIds = @(& $getReleasePackageWorkIds $SubjectId)
                    if ($packageWorkIds.Count -gt 0 -and $packageWorkIds -cnotcontains $segments[$segmentId].work_id) {
                        throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside release-package manifestations."
                    }
                }
            }
            return
        }
        throw "Source registry '$Context.subject_type' has unsupported value '$SubjectType'."
    }

    $rawReleaseRuns = Get-ProjectMapValue $registry "release_runs"
    if ($null -eq $rawReleaseRuns -or -not ($rawReleaseRuns -is [System.Collections.IDictionary])) {
        throw "Source registry 'release_runs' must be a mapping."
    }
    $releaseRuns = [ordered]@{}
    foreach ($runId in $rawReleaseRuns.Keys) {
        $context = "release_runs.$runId"
        Test-StableSourceId $runId $context
        $run = $rawReleaseRuns[$runId]
        $subjectType = Get-RequiredSourceString $run "subject_type" $context
        $subjectId = Get-RequiredSourceString $run "subject_id" $context
        $segmentIds = @(Get-SourceStringList $run "segment_ids" $context)
        if ($segmentIds.Count -eq 0 -or @($segmentIds | Sort-Object -Unique).Count -ne $segmentIds.Count) {
            throw "Source registry '$context.segment_ids' must be a non-empty duplicate-free list."
        }
        & $validateDistributionScope $subjectType $subjectId $segmentIds $context
        $orderingSchemeId = Get-RequiredSourceString $run "ordering_scheme_id" $context
        if (-not $orderingSchemes.Contains($orderingSchemeId)) {
            throw "Source registry '$context.ordering_scheme_id' references unknown ordering scheme '$orderingSchemeId'."
        }
        $ordering = $orderingSchemes[$orderingSchemeId]
        $orderedEntries = @($ordering.entries)
        $orderedSegmentIds = @($orderedEntries | Where-Object { $_.target_type -eq "segment" } | ForEach-Object { $_.target_id } | Sort-Object -Unique)
        if ($ordering.ordering_mode -ne "total" -or $orderedSegmentIds.Count -ne $orderedEntries.Count -or (Compare-Object @($segmentIds | Sort-Object) @($orderedSegmentIds | Sort-Object))) {
            throw "Source registry '$context.ordering_scheme_id' must be a total ordering of exactly the run's segments."
        }
        $rawPhases = @(Get-ProjectMapValue $run "phases")
        if ($rawPhases.Count -eq 0) {
            throw "Source registry '$context.phases' must be a non-empty list."
        }
        $phases = @()
        $seenPhaseIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $flattenedPhaseSegments = @()
        for ($phaseIndex = 0; $phaseIndex -lt $rawPhases.Count; $phaseIndex++) {
            $phaseContext = "$context.phases[$phaseIndex]"
            $phase = $rawPhases[$phaseIndex]
            $phaseId = Get-RequiredSourceString $phase "id" $phaseContext
            Test-StableSourceId $phaseId "$phaseContext.id"
            if (-not $seenPhaseIds.Add($phaseId)) {
                throw "Source registry '$context.phases' repeats phase ID '$phaseId'."
            }
            $phaseSegmentIds = @(Get-SourceStringList $phase "segment_ids" $phaseContext)
            if ($phaseSegmentIds.Count -eq 0) {
                throw "Source registry '$phaseContext.segment_ids' must not be empty."
            }
            $flattenedPhaseSegments += @($phaseSegmentIds)
            $firstReleaseWindow = ConvertTo-KnowledgeTemporalWindow $phase "first_release_window" $phaseContext $SchemaPackRegistry
            if ($null -eq $firstReleaseWindow) {
                throw "Source registry '$phaseContext.first_release_window' is required."
            }
            $cadence = Get-ProjectMapValue $phase "cadence"
            if ($null -eq $cadence -or -not ($cadence -is [System.Collections.IDictionary])) {
                throw "Source registry '$phaseContext.cadence' must be a mapping."
            }
            Assert-KnowledgeMapKeys $cadence @("unit", "interval") "Source registry '$phaseContext.cadence'"
            $cadenceUnit = Get-RequiredSourceString $cadence "unit" "$phaseContext.cadence"
            $cadenceInterval = Get-ProjectMapValue $cadence "interval"
            if ($cadenceInterval -is [bool] -or $cadenceInterval -isnot [int] -or [int]$cadenceInterval -lt 1) {
                throw "Source registry '$phaseContext.cadence.interval' must be a positive integer."
            }
            Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-run-cadence-unit" @($cadenceUnit) "$phaseContext.cadence.unit"
            $batchSize = Get-ProjectMapValue $phase "batch_size"
            if ($batchSize -is [bool] -or $batchSize -isnot [int] -or [int]$batchSize -lt 1 -or [int]$batchSize -gt $phaseSegmentIds.Count) {
                throw "Source registry '$phaseContext.batch_size' must be between 1 and the number of phase segments."
            }
            $phases += [pscustomobject]@{id=$phaseId
                segment_ids=@($phaseSegmentIds)
                first_release_window=$firstReleaseWindow
                cadence_unit=$cadenceUnit
                cadence_interval=[int]$cadenceInterval
                batch_size=[int]$batchSize
            }
        }
        $orderedRunSegments = @($orderedEntries | ForEach-Object { $_.target_id })
        if ((Compare-Object @($flattenedPhaseSegments) @($orderedRunSegments) -SyncWindow 0)) {
            throw "Source registry '$context.phases' must partition the run's segments exactly in ordering-scheme order."
        }
        $territoryIds = @(Get-SourceStringListAllowEmpty $run "territory_ids" $context)
        foreach ($territoryId in $territoryIds) {
            if (-not $territories.Contains($territoryId)) {
                throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'."
            }
        }
        $platformIds = @(Get-SourceStringListAllowEmpty $run "platform_ids" $context)
        foreach ($platformId in $platformIds) {
            if (-not $platforms.Contains($platformId)) {
                throw "Source registry '$context.platform_ids' references unknown platform '$platformId'."
            }
        }
        $rawExceptions = @(Get-ProjectMapValue $run "exceptions")
        $exceptions = @()
        $seenExceptions = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        for ($index = 0; $index -lt $rawExceptions.Count; $index++) {
            $exceptionContext = "$context.exceptions[$index]"
            $exception = $rawExceptions[$index]
            $exceptionType = Get-RequiredSourceString $exception "exception_type" $exceptionContext
            Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-run-exception-type" @($exceptionType) "$exceptionContext.exception_type"
            $segmentId = Get-RequiredSourceString $exception "segment_id" $exceptionContext
            if ($segmentIds -cnotcontains $segmentId) {
                throw "Source registry '$exceptionContext.segment_id' falls outside the release run."
            }
            if (-not $seenExceptions.Add("$exceptionType|$segmentId")) {
                throw "Source registry '$context.exceptions' repeats an exception."
            }
            $releaseWindow = ConvertTo-KnowledgeTemporalWindow $exception "release_window" $exceptionContext $SchemaPackRegistry
            $intervalCount = Get-ProjectMapValue $exception "interval_count"
            if ($null -ne $intervalCount -and ($intervalCount -is [bool] -or $intervalCount -isnot [int] -or [int]$intervalCount -lt 1)) {
                throw "Source registry '$exceptionContext.interval_count' must be a positive integer when present."
            }
            $validShape = if ($exceptionType -eq "rescheduled") {
                $null -ne $releaseWindow -and $null -eq $intervalCount
            }
            elseif ($exceptionType -eq "pause") {
                $null -eq $releaseWindow -and $null -ne $intervalCount
            }
            else {
                $null -eq $releaseWindow -and $null -eq $intervalCount
            }
            if (-not $validShape) {
                throw "Source registry '$exceptionContext' fields are incompatible with exception type '$exceptionType'."
            }
            $exceptions += [pscustomobject]@{exception_type=$exceptionType
                segment_id=$segmentId
                release_window=$releaseWindow
                interval_count=if ($null -eq $intervalCount) {
                    $null
                }
                else {
                    [int]$intervalCount
                }
            }
        }
        $lifecycle = Get-RequiredSourceString $run "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $releaseRuns[$runId] = [pscustomobject]@{id=$runId
            lifecycle=$lifecycle
            label=Get-RequiredSourceString $run "label" $context
            subject_type=$subjectType
            subject_id=$subjectId
            segment_ids=@($segmentIds)
            ordering_scheme_id=$orderingSchemeId
            release_event_type=Get-RequiredSourceString $run "release_event_type" $context
            phases=@($phases)
            territory_ids=@($territoryIds)
            platform_ids=@($platformIds)
            availability_status=Get-RequiredSourceString $run "availability_status" $context
            exceptions=@($exceptions)
        }
    }
    if ($releaseRuns.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-event-type" @($releaseRuns.Values | ForEach-Object { $_.release_event_type }) "release_runs.*.release_event_type"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.availability-status" @($releaseRuns.Values | ForEach-Object { $_.availability_status }) "release_runs.*.availability_status"
    }

    $rawReleaseEvents = Get-ProjectMapValue $registry "release_events"
    if ($null -eq $rawReleaseEvents -or -not ($rawReleaseEvents -is [System.Collections.IDictionary])) {
        throw "Source registry 'release_events' must be a mapping."
    }
    $releaseEvents = [ordered]@{}
    foreach ($eventId in $rawReleaseEvents.Keys) {
        $context = "release_events.$eventId"
        Test-StableSourceId $eventId $context
        $event = $rawReleaseEvents[$eventId]
        $subjectType = Get-RequiredSourceString $event "subject_type" $context
        $subjectId = Get-RequiredSourceString $event "subject_id" $context
        $segmentIds = @(Get-SourceStringListAllowEmpty $event "segment_ids" $context)
        & $validateDistributionScope $subjectType $subjectId $segmentIds $context
        $platformIds = @(Get-SourceStringListAllowEmpty $event "platform_ids" $context)
        foreach ($platformId in $platformIds) {
            if (-not $platforms.Contains($platformId)) {
                throw "Source registry '$context.platform_ids' references unknown platform '$platformId'."
            }
        }
        $territoryIds = @(Get-SourceStringListAllowEmpty $event "territory_ids" $context)
        foreach ($territoryId in $territoryIds) {
            if (-not $territories.Contains($territoryId)) {
                throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'."
            }
        }
        $releaseRunId = Get-OptionalSourceString $event "release_run_id" $context
        if ($null -ne $releaseRunId) {
            if (-not $releaseRuns.Contains($releaseRunId)) {
                throw "Source registry '$context.release_run_id' references unknown release run '$releaseRunId'."
            }
            $releaseRun = $releaseRuns[$releaseRunId]
            $hasUnknownSegments = @(
                $segmentIds | Where-Object { $releaseRun.segment_ids -cnotcontains $_ }
            ).Count -gt 0
            $hasUnknownPlatforms = (
                $releaseRun.platform_ids.Count -gt 0 -and
                @($platformIds | Where-Object { $releaseRun.platform_ids -cnotcontains $_ }).Count -gt 0
            )
            $hasUnknownTerritories = (
                $releaseRun.territory_ids.Count -gt 0 -and
                @($territoryIds | Where-Object { $releaseRun.territory_ids -cnotcontains $_ }).Count -gt 0
            )
            if (
                $releaseRun.subject_type -ne $subjectType -or
                $releaseRun.subject_id -ne $subjectId -or
                $hasUnknownSegments -or
                $hasUnknownPlatforms -or
                $hasUnknownTerritories
            ) {
                throw "Source registry '$context' falls outside its release run."
            }
        }
        $releaseEvents[$eventId] = [pscustomobject]@{
            id=$eventId
            lifecycle=Get-RequiredSourceString $event "lifecycle" $context
            label=Get-RequiredSourceString $event "label" $context
            subject_type=$subjectType
            subject_id=$subjectId
            segment_ids=@($segmentIds)
            release_event_type=Get-RequiredSourceString $event "release_event_type" $context
            release_window=ConvertTo-KnowledgeTemporalWindow $event "release_window" $context $SchemaPackRegistry
            territory_ids=@($territoryIds)
            platform_ids=@($platformIds)
            availability_status=Get-RequiredSourceString $event "availability_status" $context
            release_run_id=$releaseRunId
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $releaseEvents[$eventId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }
    if ($releaseEvents.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-event-type" @($releaseEvents.Values | ForEach-Object { $_.release_event_type }) "release_events.*.release_event_type"
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.availability-status" @($releaseEvents.Values | ForEach-Object { $_.availability_status }) "release_events.*.availability_status"
    }

    $rawCatalogPlacements = Get-ProjectMapValue $registry "catalog_placements"
    if ($null -eq $rawCatalogPlacements -or -not ($rawCatalogPlacements -is [System.Collections.IDictionary])) {
        throw "Source registry 'catalog_placements' must be a mapping."
    }
    $catalogPlacements = [ordered]@{}
    foreach ($placementId in $rawCatalogPlacements.Keys) {
        $context = "catalog_placements.$placementId"
        Test-StableSourceId $placementId $context
        $placement = $rawCatalogPlacements[$placementId]
        $platformId = Get-RequiredSourceString $placement "platform_id" $context
        if (-not $platforms.Contains($platformId)) {
            throw "Source registry '$context.platform_id' references unknown platform '$platformId'."
        }
        $targetType = Get-RequiredSourceString $placement "target_type" $context
        $targetId = Get-RequiredSourceString $placement "target_id" $context
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.catalog-target-type" @($targetType) "$context.target_type"
        $targetExists = switch ($targetType) {
            "work" {
                $works.Contains($targetId)
            }
            "segment" {
                $segments.Contains($targetId)
            }
            "content-group" {
                $contentGroups.Contains($targetId)
            }
            "manifestation" {
                $manifestations.Contains($targetId)
            }
            "release-package" {
                $releasePackages.Contains($targetId)
            }
            default {
                $false
            }
        }
        if (-not $targetExists) {
            throw "Source registry '$context.target_id' references unknown $targetType '$targetId'."
        }
        $ordinal = Get-ProjectMapValue $placement "ordinal"
        if ($null -ne $ordinal -and ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1)) {
            throw "Source registry '$context.ordinal' must be a positive integer when present."
        }
        $localizedTitles = @(ConvertTo-SourceLocalizedTitles $placement $context $SchemaPackRegistry)
        foreach ($localizedTitle in $localizedTitles) {
            foreach ($territoryId in $localizedTitle.territory_ids) {
                if (-not $territories.Contains($territoryId)) {
                    throw "Source registry '$context.localized_titles' references unknown territory '$territoryId'."
                }
            }
        }
        $catalogPlacements[$placementId] = [pscustomobject]@{
            id=$placementId
            lifecycle=Get-RequiredSourceString $placement "lifecycle" $context
            label=Get-RequiredSourceString $placement "label" $context
            platform_id=$platformId
            placement_type=Get-RequiredSourceString $placement "placement_type" $context
            parent_placement_id=Get-OptionalSourceString $placement "parent_placement_id" $context
            target_type=$targetType
            target_id=$targetId
            ordinal=if ($null -eq $ordinal) {
                $null
            }
            else {
                [int]$ordinal
            }
            provider_key=Get-OptionalSourceString $placement "provider_key" $context
            localized_titles=@($localizedTitles)
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $catalogPlacements[$placementId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }
    foreach ($placement in $catalogPlacements.Values) {
        if ($null -eq $placement.parent_placement_id) {
            continue
        }
        if (-not $catalogPlacements.Contains($placement.parent_placement_id)) {
            throw "Source registry catalog placement '$($placement.id)' references unknown parent '$($placement.parent_placement_id)'."
        }
        if ($placement.parent_placement_id -eq $placement.id) {
            throw "Source registry catalog placement '$($placement.id)' cannot parent itself."
        }
        if ($catalogPlacements[$placement.parent_placement_id].platform_id -ne $placement.platform_id) {
            throw "Source registry catalog placement '$($placement.id)' and its parent must belong to the same platform."
        }
    }
    foreach ($placementId in $catalogPlacements.Keys) {
        $activePlacements = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $currentPlacementId = $placementId
        while ($null -ne $currentPlacementId) {
            if (-not $activePlacements.Add($currentPlacementId)) {
                throw "Source registry contains a catalog-placement cycle involving '$currentPlacementId'."
            }
            $currentPlacementId = $catalogPlacements[$currentPlacementId].parent_placement_id
        }
    }
    if ($catalogPlacements.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.catalog-placement-type" @($catalogPlacements.Values | ForEach-Object { $_.placement_type }) "catalog_placements.*.placement_type"
    }

    $rawPlatformOfferings = Get-ProjectMapValue $registry "platform_offerings"
    if ($null -eq $rawPlatformOfferings -or -not ($rawPlatformOfferings -is [System.Collections.IDictionary])) {
        throw "Source registry 'platform_offerings' must be a mapping."
    }
    $platformOfferings = [ordered]@{}
    foreach ($offeringId in $rawPlatformOfferings.Keys) {
        $context = "platform_offerings.$offeringId"
        Test-StableSourceId $offeringId $context
        $offering = $rawPlatformOfferings[$offeringId]
        $platformId = Get-RequiredSourceString $offering "platform_id" $context
        $subjectType = Get-RequiredSourceString $offering "subject_type" $context
        $subjectId = Get-RequiredSourceString $offering "subject_id" $context
        $segmentIds = @(Get-SourceStringListAllowEmpty $offering "segment_ids" $context)
        if (-not $platforms.Contains($platformId)) {
            throw "Source registry '$context.platform_id' references unknown platform '$platformId'."
        }
        & $validateDistributionScope $subjectType $subjectId $segmentIds $context
        $releaseEventId = Get-OptionalSourceString $offering "release_event_id" $context
        if ($null -ne $releaseEventId -and -not $releaseEvents.Contains($releaseEventId)) {
            throw "Source registry '$context.release_event_id' references unknown release event '$releaseEventId'."
        }
        $offeringReleaseEvent = if ($null -ne $releaseEventId) {
            $releaseEvents[$releaseEventId]
        }
        else {
            $null
        }
        if (
            $null -ne $offeringReleaseEvent -and
            (
                $offeringReleaseEvent.subject_type -ne $subjectType -or
                $offeringReleaseEvent.subject_id -ne $subjectId -or
                $offeringReleaseEvent.platform_ids -cnotcontains $platformId
            )
        ) {
            throw "Source registry '$context' release event does not match its subject and platform."
        }
        if ($null -ne $releaseEventId -and $segmentIds.Count -gt 0 -and $releaseEvents[$releaseEventId].segment_ids.Count -gt 0) {
            foreach ($segmentId in $segmentIds) {
                if ($releaseEvents[$releaseEventId].segment_ids -cnotcontains $segmentId) {
                    throw "Source registry '$context.segment_ids' extends beyond its release-event scope."
                }
            }
        }
        $placementIds = @(Get-SourceStringListAllowEmpty $offering "catalog_placement_ids" $context)
        foreach ($placementId in $placementIds) {
            if (-not $catalogPlacements.Contains($placementId) -or $catalogPlacements[$placementId].platform_id -ne $platformId) {
                throw "Source registry '$context.catalog_placement_ids' references placement '$placementId' outside platform '$platformId'."
            }
        }
        $territoryIds = @(Get-SourceStringListAllowEmpty $offering "territory_ids" $context)
        foreach ($territoryId in $territoryIds) {
            if (-not $territories.Contains($territoryId)) {
                throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'."
            }
        }
        $languageTags = @(Get-SourceStringListAllowEmpty $offering "language_tags" $context)
        foreach ($languageTag in $languageTags) {
            Test-SourceLanguageTag $languageTag "$context.language_tags"
        }
        $platformOfferings[$offeringId] = [pscustomobject]@{
            id=$offeringId
            lifecycle=Get-RequiredSourceString $offering "lifecycle" $context
            label=Get-RequiredSourceString $offering "label" $context
            platform_id=$platformId
            subject_type=$subjectType
            subject_id=$subjectId
            segment_ids=@($segmentIds)
            release_event_id=$releaseEventId
            offering_type=Get-RequiredSourceString $offering "offering_type" $context
            availability_status=Get-RequiredSourceString $offering "availability_status" $context
            territory_ids=@($territoryIds)
            language_tags=@($languageTags)
            availability_window=ConvertTo-KnowledgeTemporalWindow $offering "availability_window" $context $SchemaPackRegistry
            catalog_placement_ids=@($placementIds)
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $platformOfferings[$offeringId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }
    if ($platformOfferings.Count -gt 0) {
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.platform-offering-type" @($platformOfferings.Values | ForEach-Object { $_.offering_type }) "platform_offerings.*.offering_type"
        $offeringAvailabilityStatuses = @(
            $platformOfferings.Values | ForEach-Object { $_.availability_status }
        )
        Assert-SourceSchemaPackValues `
            $SchemaPackRegistry `
            "source.availability-status" `
            $offeringAvailabilityStatuses `
            "platform_offerings.*.availability_status"
    }

    $rawIdentifierSchemes = Get-ProjectMapValue $registry "identifier_schemes"
    if ($null -eq $rawIdentifierSchemes -or -not ($rawIdentifierSchemes -is [System.Collections.IDictionary])) {
        throw "Source registry 'identifier_schemes' must be a mapping."
    }
    $identifierSchemes = [ordered]@{}
    foreach ($schemeId in $rawIdentifierSchemes.Keys) {
        $context = "identifier_schemes.$schemeId"
        Test-StableSourceId $schemeId $context
        $scheme = $rawIdentifierSchemes[$schemeId]
        $targetTypes = @(Get-SourceStringList $scheme "target_types" $context)
        if ($targetTypes.Count -eq 0) {
            throw "Source registry '$context.target_types' must not be empty."
        }
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.identifier-target-type" $targetTypes "$context.target_types"
        $identifierSchemes[$schemeId] = [pscustomobject]@{
            id=$schemeId
            lifecycle=Get-RequiredSourceString $scheme "lifecycle" $context
            label=Get-RequiredSourceString $scheme "label" $context
            target_types=@($targetTypes)
            case_sensitive=Get-RequiredSourceBoolean $scheme "case_sensitive" $context
        }
        if ($script:AllowedSourceLifecycles -cnotcontains $identifierSchemes[$schemeId].lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
    }

    $rawSources = Get-ProjectMapValue $registry "sources"
    if ($null -eq $rawSources -or -not ($rawSources -is [System.Collections.IDictionary])) {
        throw "Source registry 'sources' must be a mapping."
    }
    $sources = [ordered]@{}
    $sourceAliases = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    $sourceIdKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($sourceId in $rawSources.Keys) {
        [void]$sourceIdKeys.Add((ConvertTo-KnowledgeLookupKey $sourceId $lookupKeys))
    }
    foreach ($sourceId in $rawSources.Keys) {
        $context = "sources.$sourceId"
        Test-StableSourceId $sourceId $context
        $source = $rawSources[$sourceId]
        $lifecycle = Get-RequiredSourceString $source "lifecycle" $context
        if ($script:AllowedSourceLifecycles -cnotcontains $lifecycle) {
            throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
        }
        $workIds = @(Get-SourceStringList $source "work_ids" $context)
        $mediumId = Get-RequiredSourceString $source "medium_id" $context
        if ($workIds.Count -eq 0 -or @($workIds | Sort-Object -Unique).Count -ne $workIds.Count) {
            throw "Source registry '$context.work_ids' must be a non-empty duplicate-free list."
        }
        foreach ($workId in $workIds) {
            if (-not $works.Contains($workId)) {
                throw "Source registry '$context.work_ids' references unknown work '$workId'."
            }
        }
        if (-not $mediums.Contains($mediumId)) {
            throw "Source registry '$context.medium_id' references unknown medium '$mediumId'."
        }
        $locatorMediumIds = @(Get-SourceStringList $source "locator_medium_ids" $context)
        if ($locatorMediumIds -cnotcontains $mediumId -or @($locatorMediumIds | Sort-Object -Unique).Count -ne $locatorMediumIds.Count) {
            throw "Source registry '$context.locator_medium_ids' must be duplicate-free and include the source medium."
        }
        $unknownLocatorMedia = @($locatorMediumIds | Where-Object { -not $mediums.Contains($_) })
        if ($unknownLocatorMedia.Count -gt 0) {
            throw "Source registry '$context.locator_medium_ids' references unknown media: $($unknownLocatorMedia -join ', ')."
        }
        $manifestationId = Get-OptionalSourceString $source "manifestation_id" $context
        if ($null -ne $manifestationId) {
            if (-not $manifestations.Contains($manifestationId)) {
                throw "Source registry '$context.manifestation_id' references unknown manifestation '$manifestationId'."
            }
            if ($workIds -cnotcontains $manifestations[$manifestationId].work_id) {
                throw "Source registry '$context' manifestation belongs to a work outside the source scope."
            }
        }
        $releasePackageId = Get-OptionalSourceString $source "release_package_id" $context
        if ($null -ne $releasePackageId) {
            if (-not $releasePackages.Contains($releasePackageId)) {
                throw "Source registry '$context.release_package_id' references unknown release package '$releasePackageId'."
            }
            $componentManifestationIds = @(
                $releasePackages[$releasePackageId].release_component_ids |
                    ForEach-Object { $releaseComponents[$_].manifestation_id } |
                    Where-Object { $null -ne $_ }
            )
            $combinedManifestationIds = @($releasePackages[$releasePackageId].manifestation_ids) +
            @($componentManifestationIds)
            $packageManifestationIds = @($combinedManifestationIds | Sort-Object -Unique)
            if ($null -ne $manifestationId -and $packageManifestationIds -cnotcontains $manifestationId) {
                throw "Source registry '$context' manifestation is not contained by its release package."
            }
            $packageWorkIds = @(& $getReleasePackageWorkIds $releasePackageId)
            if ($packageWorkIds.Count -gt 0 -and @($workIds | Where-Object { $packageWorkIds -cnotcontains $_ }).Count -gt 0) {
                throw "Source registry '$context.work_ids' extends beyond its release package."
            }
        }
        $releaseEventId = Get-OptionalSourceString $source "release_event_id" $context
        if ($null -ne $releaseEventId) {
            if (-not $releaseEvents.Contains($releaseEventId)) {
                throw "Source registry '$context.release_event_id' references unknown release event '$releaseEventId'."
            }
            $expectedSubjectType = if ($null -ne $releasePackageId) {
                "release-package"
            }
            else {
                "manifestation"
            }
            $expectedSubjectId = if ($null -ne $releasePackageId) {
                $releasePackageId
            }
            else {
                $manifestationId
            }
            if ($releaseEvents[$releaseEventId].subject_type -ne $expectedSubjectType -or $releaseEvents[$releaseEventId].subject_id -ne $expectedSubjectId) {
                throw "Source registry '$context' release event does not belong to its manifestation or package."
            }
        }
        $releaseComponentIds = @(Get-SourceStringListAllowEmpty $source "release_component_ids" $context)
        foreach ($componentId in $releaseComponentIds) {
            if (-not $releaseComponents.Contains($componentId)) {
                throw "Source registry '$context.release_component_ids' references unknown component '$componentId'."
            }
            $componentMatches = ($null -ne $manifestationId -and $releaseComponents[$componentId].manifestation_id -eq $manifestationId)
            if ($null -ne $releasePackageId) {
                $componentMatches = $componentMatches -or ($releasePackages[$releasePackageId].release_component_ids -ccontains $componentId)
            }
            if (-not $componentMatches) {
                throw "Source registry '$context' component '$componentId' does not belong to its manifestation or package."
            }
            $componentWorkIds = @($releaseComponents[$componentId].segment_ids | ForEach-Object { $segments[$_].work_id })
            if ($null -ne $releaseComponents[$componentId].manifestation_id) {
                $componentWorkIds += @($manifestations[$releaseComponents[$componentId].manifestation_id].work_id)
            }
            $componentWorkIds = @($componentWorkIds | Sort-Object -Unique)
            if ($componentWorkIds.Count -gt 0 -and @($componentWorkIds | Where-Object { $workIds -ccontains $_ }).Count -eq 0) {
                throw "Source registry '$context' component '$componentId' falls outside the source work scope."
            }
        }
        $platformOfferingId = Get-OptionalSourceString $source "platform_offering_id" $context
        if ($null -ne $platformOfferingId) {
            if (-not $platformOfferings.Contains($platformOfferingId)) {
                throw "Source registry '$context.platform_offering_id' references unknown offering '$platformOfferingId'."
            }
            $expectedSubjectType = if ($null -ne $releasePackageId) {
                "release-package"
            }
            else {
                "manifestation"
            }
            $expectedSubjectId = if ($null -ne $releasePackageId) {
                $releasePackageId
            }
            else {
                $manifestationId
            }
            if ($platformOfferings[$platformOfferingId].subject_type -ne $expectedSubjectType -or $platformOfferings[$platformOfferingId].subject_id -ne $expectedSubjectId) {
                throw "Source registry '$context' platform offering does not belong to its manifestation or package."
            }
        }
        $containerFormatIds = @(Get-SourceStringList $source "container_format_ids" $context)
        if ($containerFormatIds.Count -eq 0) {
            throw "Source registry '$context.container_format_ids' must not be empty."
        }
        $unknownContainerFormats = @($containerFormatIds | Where-Object { -not $containerFormats.Contains($_) } | Sort-Object -Unique)
        if ($unknownContainerFormats.Count -gt 0) {
            throw "Source registry '$context.container_format_ids' references unknown container formats: $($unknownContainerFormats -join ', ')."
        }
        $role = Get-RequiredSourceString $source "role" $context
        if ($allowedSourceRoles -cnotcontains $role) {
            throw "Source registry '$context.role' must be one of: $($allowedSourceRoles -join ', ')."
        }
        $incompatibleWorkIds = @($workIds | Where-Object { $works[$_].medium_id -ne $mediumId })
        if ($incompatibleWorkIds.Count -gt 0 -and $role -notin @("supplemental", "reference", "extract")) {
            throw "Source registry '$context' medium does not match works: $($incompatibleWorkIds -join ', ')."
        }
        $comparisonGroup = Get-RequiredSourceString $source "comparison_group" $context
        Test-StableSourceId $comparisonGroup "$context.comparison_group"
        $priority = Get-ProjectMapValue $source "priority"
        if ($priority -is [bool] -or $priority -isnot [int] -or [int]$priority -lt 1) {
            throw "Source registry '$context.priority' must be a positive integer."
        }
        $aliases = @(Get-SourceStringListAllowEmpty $source "aliases" $context)
        foreach ($alias in $aliases) {
            Test-StableSourceId $alias "$context.aliases"
            $aliasKey = ConvertTo-KnowledgeLookupKey $alias $lookupKeys
            if ($sourceAliases.ContainsKey($aliasKey) -or $sourceIdKeys.Contains($aliasKey)) {
                throw "Source registry alias '$alias' is duplicated or collides with a source ID."
            }
            $sourceAliases[$aliasKey] = $sourceId
        }
        $evidenceModes = @(Get-SourceStringListAllowEmpty $source "evidence_modes" $context)
        Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.evidence-mode" @($evidenceModes) "$context.evidence_modes"
        $observations = @()
        $seenObservationIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $seenObservationTargets = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        $rawObservations = Get-ProjectMapValue $source "observations"
        if ($null -eq $rawObservations) {
            $rawObservations = @()
        }
        elseif ($rawObservations -is [System.Collections.IDictionary]) {
            $rawObservations = @($rawObservations)
        }
        elseif ($rawObservations -isnot [System.Collections.IList]) {
            throw "Source registry '$context.observations' must be a list."
        }
        for ($observationIndex = 0; $observationIndex -lt $rawObservations.Count; $observationIndex++) {
            $observationContext = "$context.observations[$observationIndex]"
            $observation = $rawObservations[$observationIndex]
            $observationId = Get-RequiredSourceString $observation "id" $observationContext
            Test-StableSourceId $observationId "$observationContext.id"
            if (-not $seenObservationIds.Add($observationId)) {
                throw "Source registry '$context.observations' repeats ID '$observationId'."
            }
            $observationType = Get-RequiredSourceString $observation "target_type" $observationContext
            $observationTargetId = Get-RequiredSourceString $observation "target_id" $observationContext
            $observationExists = switch ($observationType) {
                "manifestation" {
                    $manifestations.Contains($observationTargetId)
                }
                "release-package" {
                    $releasePackages.Contains($observationTargetId)
                }
                "release-event" {
                    $releaseEvents.Contains($observationTargetId)
                }
                "release-component" {
                    $releaseComponents.Contains($observationTargetId)
                }
                "platform-offering" {
                    $platformOfferings.Contains($observationTargetId)
                }
                default {
                    $false
                }
            }
            if (-not $observationExists) {
                throw "Source registry '$observationContext' references unknown $observationType '$observationTargetId'."
            }
            if (-not $seenObservationTargets.Add("$observationType|$observationTargetId")) {
                throw "Source registry '$context.observations' repeats a target."
            }
            $observationWorkIds = @()
            switch ($observationType) {
                "manifestation" {
                    $observationWorkIds = @($manifestations[$observationTargetId].work_id)
                }
                "release-package" {
                    $observationWorkIds = @(& $getReleasePackageWorkIds $observationTargetId)
                }
                "release-event" {
                    $event = $releaseEvents[$observationTargetId]
                    if ($event.subject_type -eq "manifestation") {
                        $observationWorkIds = @($manifestations[$event.subject_id].work_id)
                    }
                    elseif ($event.subject_type -eq "release-package") {
                        $observationWorkIds = @(& $getReleasePackageWorkIds $event.subject_id)
                    }
                }
                "platform-offering" {
                    $offering = $platformOfferings[$observationTargetId]
                    if ($offering.subject_type -eq "manifestation") {
                        $observationWorkIds = @($manifestations[$offering.subject_id].work_id)
                    }
                    elseif ($offering.subject_type -eq "release-package") {
                        $observationWorkIds = @(& $getReleasePackageWorkIds $offering.subject_id)
                    }
                }
                "release-component" {
                    $component = $releaseComponents[$observationTargetId]
                    $observationWorkIds = @($component.segment_ids | ForEach-Object { $segments[$_].work_id })
                    if ($null -ne $component.manifestation_id) {
                        $observationWorkIds += @($manifestations[$component.manifestation_id].work_id)
                    }
                    $observationWorkIds = @($observationWorkIds | Sort-Object -Unique)
                }
            }
            if ($observationWorkIds.Count -gt 0 -and @($observationWorkIds | Where-Object { $workIds -cnotcontains $_ }).Count -gt 0) {
                throw "Source registry '$context.observations' includes material outside the source work scope."
            }
            $observations += [pscustomobject]@{id=$observationId
                target_type=$observationType
                target_id=$observationTargetId
            }
        }
        $coverage = @()
        $rawCoverage = @(Get-ProjectMapValue $source "coverage")
        $seenCoverage = [ordered]@{}
        $seenCoverageIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
        for ($coverageIndex = 0; $coverageIndex -lt $rawCoverage.Count; $coverageIndex++) {
            $coverageContext = "$context.coverage[$coverageIndex]"
            $coverageEntry = $rawCoverage[$coverageIndex]
            $coverageId = Get-RequiredSourceString $coverageEntry "id" $coverageContext
            Test-StableSourceId $coverageId "$coverageContext.id"
            if (-not $seenCoverageIds.Add($coverageId)) {
                throw "Source registry '$context.coverage' repeats ID '$coverageId'."
            }
            $targetType = Get-RequiredSourceString $coverageEntry "target_type" $coverageContext
            Assert-SourceSchemaPackValues $SchemaPackRegistry "source.coverage-target-type" @($targetType) "$coverageContext.target_type"
            $targetId = Get-RequiredSourceString $coverageEntry "target_id" $coverageContext
            $targetExists = switch ($targetType) {
                "work" {
                    $works.Contains($targetId)
                }
                "segment" {
                    $segments.Contains($targetId)
                }
                "content-group" {
                    $contentGroups.Contains($targetId)
                }
                "manifestation" {
                    $manifestations.Contains($targetId)
                }
                "release-component" {
                    $releaseComponents.Contains($targetId)
                }
                "release-package" {
                    $releasePackages.Contains($targetId)
                }
                default {
                    $false
                }
            }
            if (-not $targetExists) {
                throw "Source registry '$coverageContext.target_id' references unknown $targetType '$targetId'."
            }
            $coverageType = Get-RequiredSourceString $coverageEntry "coverage_type" $coverageContext
            Assert-SourceSchemaPackValues $SchemaPackRegistry "source.coverage-type" @($coverageType) "$coverageContext.coverage_type"
            $coverageMediumId = Get-RequiredSourceString $coverageEntry "medium_id" $coverageContext
            if ($locatorMediumIds -cnotcontains $coverageMediumId) {
                throw "Source registry '$coverageContext.medium_id' is not allowed by the source."
            }
            $coverageEvidenceModes = @(Get-SourceStringList $coverageEntry "evidence_modes" $coverageContext)
            if ($coverageEvidenceModes.Count -eq 0) {
                throw "Source registry '$coverageContext.evidence_modes' must not be empty."
            }
            $unknownCoverageModes = @($coverageEvidenceModes | Where-Object { $evidenceModes -cnotcontains $_ } | Sort-Object -Unique)
            if ($unknownCoverageModes.Count -gt 0) {
                throw "Source registry '$coverageContext.evidence_modes' uses modes not declared by the source: $($unknownCoverageModes -join ', ')."
            }
            $targetWorkIds = @()
            switch ($targetType) {
                "work" {
                    $targetWorkIds = @($targetId)
                }
                "segment" {
                    $targetWorkIds = @($segments[$targetId].work_id)
                }
                "content-group" {
                    $pendingGroups = New-Object 'System.Collections.Generic.Queue[string]'
                    $pendingGroups.Enqueue($targetId)
                    $seenGroups = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
                    while ($pendingGroups.Count -gt 0) {
                        $groupId = $pendingGroups.Dequeue()
                        if (-not $seenGroups.Add($groupId)) {
                            continue
                        }
                        foreach ($member in $contentGroups[$groupId].members) {
                            if ($member.target_type -eq "work") {
                                $targetWorkIds += @($member.target_id)
                            }
                            elseif ($member.target_type -eq "segment") {
                                $targetWorkIds += @($segments[$member.target_id].work_id)
                            }
                            elseif ($member.target_type -eq "content-group") {
                                $pendingGroups.Enqueue($member.target_id)
                            }
                        }
                    }
                    $targetWorkIds = @($targetWorkIds | Sort-Object -Unique)
                }
                "manifestation" {
                    $targetWorkIds = @($manifestations[$targetId].work_id)
                }
                "release-package" {
                    $targetWorkIds = @(& $getReleasePackageWorkIds $targetId)
                }
                "release-component" {
                    $targetWorkIds = @($releaseComponents[$targetId].segment_ids | ForEach-Object { $segments[$_].work_id })
                    if ($null -ne $releaseComponents[$targetId].manifestation_id) {
                        $targetWorkIds += @($manifestations[$releaseComponents[$targetId].manifestation_id].work_id)
                    }
                    $targetWorkIds = @($targetWorkIds | Sort-Object -Unique)
                }
            }
            if ($targetWorkIds.Count -gt 0 -and @($targetWorkIds | Where-Object { $workIds -cnotcontains $_ }).Count -gt 0) {
                throw "Source registry '$coverageContext' extends beyond the source work scope."
            }
            $ranges = @()
            $seenRangeIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
            $rawRanges = Get-ProjectMapValue $coverageEntry "position_ranges"
            if ($null -eq $rawRanges) {
                $rawRanges = @()
            }
            elseif ($rawRanges -is [System.Collections.IDictionary]) {
                $rawRanges = @($rawRanges)
            }
            elseif ($rawRanges -isnot [System.Collections.IList]) {
                throw "Source registry '$coverageContext.position_ranges' must be a list."
            }
            for ($rangeIndex = 0; $rangeIndex -lt $rawRanges.Count; $rangeIndex++) {
                $rangeContext = "$coverageContext.position_ranges[$rangeIndex]"
                $range = $rawRanges[$rangeIndex]
                $rangeId = Get-RequiredSourceString $range "id" $rangeContext
                Test-StableSourceId $rangeId "$rangeContext.id"
                if (-not $seenRangeIds.Add($rangeId)) {
                    throw "Source registry '$coverageContext.position_ranges' repeats ID '$rangeId'."
                }
                $start = Get-ProjectMapValue $range "start"
                $end = Get-ProjectMapValue $range "end"
                if ($null -eq $start -or $start -isnot [System.Collections.IDictionary] -or $start.Count -eq 0) {
                    throw "Source registry '$rangeContext.start' must be a non-empty mapping."
                }
                if ($null -eq $end -or $end -isnot [System.Collections.IDictionary] -or $end.Count -eq 0) {
                    throw "Source registry '$rangeContext.end' must be a non-empty mapping."
                }
                $startKeys = @($start.Keys | ForEach-Object { [string]$_ } | Sort-Object)
                $endKeys = @($end.Keys | ForEach-Object { [string]$_ } | Sort-Object)
                if (($startKeys -join "|") -ne ($endKeys -join "|")) {
                    throw "Source registry '$rangeContext' start and end must use identical position fields."
                }
                $unknownRangeFields = @($startKeys | Where-Object { -not $mediums[$coverageMediumId].fields.Contains($_) })
                if ($unknownRangeFields.Count -gt 0) {
                    throw "Source registry '$rangeContext' references unknown position fields: $($unknownRangeFields -join ', ')."
                }
                $missingRangeFields = @($mediums[$coverageMediumId].required_fields | Where-Object { $startKeys -cnotcontains $_ })
                if ($missingRangeFields.Count -gt 0) {
                    throw "Source registry '$rangeContext' omits required position fields: $($missingRangeFields -join ', ')."
                }
                Assert-SourcePositionValues $start $mediums[$coverageMediumId].fields "$rangeContext.start"
                Assert-SourcePositionValues $end $mediums[$coverageMediumId].fields "$rangeContext.end"
                $workScopeField = $mediums[$coverageMediumId].work_scope_field
                if (-not $start.Contains($workScopeField)) {
                    throw "Source registry '$rangeContext' must include work-scope field '$workScopeField'."
                }
                $rangeWorkIds = @(@($start[$workScopeField], $end[$workScopeField]) | Sort-Object -Unique)
                if ($rangeWorkIds.Count -ne 1 -or @($rangeWorkIds | Where-Object { $targetWorkIds -cnotcontains $_ }).Count -gt 0) {
                    throw "Source registry '$rangeContext' falls outside its coverage target work scope."
                }
                Assert-SourceStructuralPosition $start $mediums[$coverageMediumId] $works $segments $orderingSchemes "$rangeContext.start"
                Assert-SourceStructuralPosition $end $mediums[$coverageMediumId] $works $segments $orderingSchemes "$rangeContext.end"
                if ((Compare-SourcePositions $start $end $mediums[$coverageMediumId] $orderingSchemes $rangeContext) -gt 0) {
                    throw "Source registry '$rangeContext' start must not follow end."
                }
                $ranges += [pscustomobject]@{id=$rangeId
                    start=$start
                    end=$end
                }
            }
            $newCoverage = [pscustomobject]@{id=$coverageId
                target_type=$targetType
                target_id=$targetId
                coverage_type=$coverageType
                medium_id=$coverageMediumId
                evidence_modes=@($coverageEvidenceModes)
                position_ranges=@($ranges)
            }
            foreach ($coverageEvidenceMode in $coverageEvidenceModes) {
                $coverageKey = "$targetType|$targetId|$coverageMediumId|$coverageEvidenceMode"
                $previousEntries = if ($seenCoverage.Contains($coverageKey)) {
                    @($seenCoverage[$coverageKey])
                }
                else {
                    @()
                }
                foreach ($previous in $previousEntries) {
                    $overlaps = ($previous.position_ranges.Count -eq 0 -or $newCoverage.position_ranges.Count -eq 0)
                    if (-not $overlaps) {
                        foreach ($left in $previous.position_ranges) {
                            foreach ($right in $newCoverage.position_ranges) {
                                $scopeField = $mediums[$coverageMediumId].work_scope_field
                                $sameScope = (
                                    [string]$left.start[$scopeField] -eq
                                    [string]$right.start[$scopeField]
                                )
                                $leftStartsBeforeRightEnds = (
                                    Compare-SourcePositions `
                                        $left.start `
                                        $right.end `
                                        $mediums[$coverageMediumId] `
                                        $orderingSchemes `
                                        $coverageContext
                                ) -le 0
                                $rightStartsBeforeLeftEnds = (
                                    Compare-SourcePositions `
                                        $right.start `
                                        $left.end `
                                        $mediums[$coverageMediumId] `
                                        $orderingSchemes `
                                        $coverageContext
                                ) -le 0
                                if ($sameScope -and $leftStartsBeforeRightEnds -and $rightStartsBeforeLeftEnds) {
                                    $overlaps = $true
                                    break
                                }
                            }
                            if ($overlaps) {
                                break
                            }
                        }
                    }
                    if ($overlaps) {
                        throw "Source registry '$context.coverage' overlaps target '$targetType`:$targetId' for medium '$coverageMediumId' and evidence mode '$coverageEvidenceMode'."
                    }
                }
                $seenCoverage[$coverageKey] = @($seenCoverage[$coverageKey]) + @($newCoverage)
            }
            $coverage += $newCoverage
        }
        $bindings = @()
        $rawBindings = @(Get-ProjectMapValue $source "resource_bindings")
        for ($i = 0; $i -lt $rawBindings.Count; $i++) {
            $bindings += Resolve-SourceResourceBinding $ProjectConfig $ResourceConfig $rawBindings[$i] "$context.resource_bindings[$i]"
        }
        $sources[$sourceId] = [pscustomobject]@{ id=$sourceId
            lifecycle=$lifecycle
            label=Get-RequiredSourceString $source "label" $context
            work_ids=@($workIds)
            manifestation_id=$manifestationId
            release_package_id=$releasePackageId
            release_event_id=$releaseEventId
            release_component_ids=@($releaseComponentIds)
            platform_offering_id=$platformOfferingId
            medium_id=$mediumId
            locator_medium_ids=@($locatorMediumIds)
            container_format_ids=@($containerFormatIds)
            role=$role
            comparison_group=$comparisonGroup
            priority=[int]$priority
            aliases=@($aliases)
            evidence_modes=@($evidenceModes)
            observations=@($observations)
            coverage=@($coverage)
            resource_bindings=@($bindings)
        }
    }
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.source-role" @($sources.Values | ForEach-Object { $_.role }) "sources.*.role"
    $seenAuthorityRuleIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($profile in $authorityProfiles.Values) {
        foreach ($rule in $profile.claim_authority_rules) {
            if (-not $seenAuthorityRuleIds.Add($rule.id)) {
                throw "Source registry authority-rule ID '$($rule.id)' is duplicated across profiles."
            }
            $unknownRuleSources = @($rule.source_ids | Where-Object { -not $sources.Contains($_) })
            if ($unknownRuleSources.Count -gt 0) {
                throw "Source registry authority rule '$($rule.id)' references unknown sources: $($unknownRuleSources -join ', ')."
            }
        }
        foreach ($claimNamespace in $claimNamespaceAncestors.Keys) {
            $ancestors = @($claimNamespaceAncestors[$claimNamespace])
            foreach ($source in $sources.Values) {
                foreach ($evidenceMode in @($null) + @($source.evidence_modes)) {
                    $matches = @(
                        $profile.claim_authority_rules | Where-Object {
                            $ancestors -ccontains $_.claim_namespace -and
                            (Test-SourceAuthorityRuleMatch $_ $source $evidenceMode $evidenceModeAncestors)
                        }
                    )
                    if ($matches.Count -eq 0) {
                        continue
                    }
                    $highest = [int](($matches | Measure-Object -Property precedence -Maximum).Maximum)
                    $winners = @($matches | Where-Object { $_.precedence -eq $highest })
                    if ($winners.Count -gt 1) {
                        $modeContext = if ($null -eq $evidenceMode) {
                            "unspecified"
                        }
                        else {
                            $evidenceMode
                        }
                        throw (
                            "Source registry authority profile '$($profile.id)' has ambiguous precedence " +
                            "'$highest' rules for source '$($source.id)', claim namespace '$claimNamespace', " +
                            "and evidence mode '$modeContext'."
                        )
                    }
                }
            }
        }
    }

    $sourceRelationships = @()
    $rawSourceRelationships = @(Get-ProjectMapValue $registry "source_relationships")
    for ($index = 0; $index -lt $rawSourceRelationships.Count; $index++) {
        $context = "source_relationships[$index]"
        $relationship = $rawSourceRelationships[$index]
        $id = Get-RequiredSourceString $relationship "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenRelationshipIds.Add($id)) {
            throw "Source registry relationship ID '$id' is duplicated."
        }
        $sourceId = Get-RequiredSourceString $relationship "source_source_id" $context
        $targetId = Get-RequiredSourceString $relationship "target_source_id" $context
        $type = Get-RequiredSourceString $relationship "relationship_type" $context
        if (-not $sources.Contains($sourceId) -or -not $sources.Contains($targetId)) {
            throw "Source registry '$context' references an unknown source."
        }
        if ($sourceId -eq $targetId) {
            throw "Source registry '$context' cannot relate a source to itself."
        }
        if (-not $sourceRelationshipTypes.Contains($type)) {
            throw "Source registry '$context.relationship_type' references unknown type '$type'."
        }
        $sourceRelationships += [pscustomobject]@{ id=$id
            source_source_id=$sourceId
            relationship_type=$type
            target_source_id=$targetId
        }
    }

    $workRelationshipMap = ConvertTo-SourceIdMap $workRelationships
    $adaptationMappingMap = ConvertTo-SourceIdMap $adaptationMappings
    $applicabilityTargets = [ordered]@{
        "work"=$works
        "segment"=$segments
        "content-group"=$contentGroups
        "work-relationship"=$workRelationshipMap
        "adaptation-mapping"=$adaptationMappingMap
        "manifestation"=$manifestations
        "release-component"=$releaseComponents
        "release-package"=$releasePackages
    }
    if (-not $registry.Contains("applicability_scopes")) {
        throw "Source registry 'applicability_scopes' must be a list."
    }
    $rawApplicabilityScopes = $registry["applicability_scopes"]
    if ($null -eq $rawApplicabilityScopes) {
        $rawApplicabilityScopes = @()
    }
    elseif ($rawApplicabilityScopes -isnot [System.Collections.IList]) {
        throw "Source registry 'applicability_scopes' must be a list."
    }
    $applicabilityScopes = [ordered]@{}
    $scopeWindows = [ordered]@{}
    for ($index = 0; $index -lt $rawApplicabilityScopes.Count; $index++) {
        $context = "applicability_scopes[$index]"
        $scope = $rawApplicabilityScopes[$index]
        $scopeId = Get-RequiredSourceString $scope "id" $context
        Test-StableSourceId $scopeId "$context.id"
        if ($applicabilityScopes.Contains($scopeId)) {
            throw "Source registry applicability-scope ID '$scopeId' is duplicated."
        }
        $targetType = Get-RequiredSourceString $scope "target_type" $context
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.applicability-target-type" @($targetType) "$context.target_type"
        $targetId = Get-RequiredSourceString $scope "target_id" $context
        if ($targetType -ne "provenance-claim" -and (-not $applicabilityTargets.Contains($targetType) -or -not $applicabilityTargets[$targetType].Contains($targetId))) {
            throw "Source registry '$context.target_id' references unknown $targetType '$targetId'."
        }
        $territoryIds = @(Get-SourceStringListAllowEmpty $scope "territory_ids" $context)
        $unknownTerritories = @($territoryIds | Where-Object { -not $territories.Contains($_) } | Sort-Object -Unique)
        if ($unknownTerritories.Count -gt 0) {
            throw "Source registry '$context.territory_ids' references unknown territories: $($unknownTerritories -join ', ')."
        }
        $precedence = Get-ProjectMapValue $scope "precedence"
        if ($precedence -is [bool] -or $precedence -isnot [int] -or [int]$precedence -lt 0) {
            throw "Source registry '$context.precedence' must be a non-negative integer."
        }
        $effectiveWindow = ConvertTo-KnowledgeTemporalWindow $scope "effective_window" $context $SchemaPackRegistry
        $windowKey = "$targetType|$targetId|$(@($territoryIds|Sort-Object) -join ',')|$precedence"
        $existingWindows = if ($scopeWindows.Contains($windowKey)) {
            @($scopeWindows[$windowKey])
        }
        else {
            @()
        }
        foreach ($existingWindow in $existingWindows) {
            if (Test-KnowledgeTemporalWindowsOverlap $effectiveWindow $existingWindow.window) {
                throw "Source registry '$context' overlaps another applicability scope with the same target, territory set, and precedence."
            }
        }
        $scopeWindows[$windowKey] = @($scopeWindows[$windowKey]) + @([pscustomobject]@{window = $effectiveWindow })
        $applicabilityScopes[$scopeId] = [pscustomobject]@{id=$scopeId
            target_type=$targetType
            target_id=$targetId
            territory_ids=@($territoryIds)
            effective_window=$effectiveWindow
            precedence=[int]$precedence
        }
    }
    $getApplicabilityWorkIds = {
        param([object]$Scope)
        if ($Scope.target_type -in @("work", "segment", "content-group", "manifestation", "release-component", "release-package")) {
            return @(Get-SourceTargetWorkScope $Scope.target_type $Scope.target_id $segments $contentGroups $manifestations $releaseComponents $releasePackages)
        }
        if ($Scope.target_type -eq "work-relationship") {
            $item = $workRelationshipMap[$Scope.target_id]
            return @(@($item.source_work_id, $item.target_work_id) | Sort-Object -Unique)
        }
        if ($Scope.target_type -eq "adaptation-mapping") {
            $item = $adaptationMappingMap[$Scope.target_id]
            return @(@(@($item.target_work_id) + @($item.basis_inputs | ForEach-Object { $_.work_id })) | Sort-Object -Unique)
        }
        return @()
    }
    foreach ($relationship in $workRelationships) {
        if ($null -eq $relationship.applicability_scope_id) {
            continue
        }
        if (-not $applicabilityScopes.Contains($relationship.applicability_scope_id)) {
            throw "Source registry work relationship '$($relationship.id)' references unknown applicability scope '$($relationship.applicability_scope_id)'."
        }
        $resolvedWorkIds = @(& $getApplicabilityWorkIds $applicabilityScopes[$relationship.applicability_scope_id])
        if ($resolvedWorkIds.Count -ne 1 -or $resolvedWorkIds[0] -ne $relationship.source_work_id) {
            throw "Source registry work relationship '$($relationship.id)' scope must resolve only to its source work."
        }
    }
    foreach ($productionContext in $workProductionContexts.Values) {
        if (-not $applicabilityScopes.Contains($productionContext.applicability_scope_id)) {
            throw "Source registry work production context '$($productionContext.id)' references unknown applicability scope '$($productionContext.applicability_scope_id)'."
        }
        $resolvedWorkIds = @(& $getApplicabilityWorkIds $applicabilityScopes[$productionContext.applicability_scope_id])
        if ($resolvedWorkIds -cnotcontains $productionContext.work_id) {
            throw "Source registry work production context '$($productionContext.id)' scope falls outside work '$($productionContext.work_id)'."
        }
    }

    if (-not $registry.Contains("scoped_continuity_assertions")) {
        throw "Source registry 'scoped_continuity_assertions' must be a list."
    }
    $rawContinuityAssertions = $registry["scoped_continuity_assertions"]
    if ($null -eq $rawContinuityAssertions) {
        $rawContinuityAssertions = @()
    }
    elseif ($rawContinuityAssertions -isnot [System.Collections.IList]) {
        throw "Source registry 'scoped_continuity_assertions' must be a list."
    }
    $scopedContinuityAssertions = [ordered]@{}
    $seenContinuityScopes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawContinuityAssertions.Count; $index++) {
        $context = "scoped_continuity_assertions[$index]"
        $assertion = $rawContinuityAssertions[$index]
        $assertionId = Get-RequiredSourceString $assertion "id" $context
        Test-StableSourceId $assertionId "$context.id"
        if ($scopedContinuityAssertions.Contains($assertionId)) {
            throw "Source registry scoped-continuity-assertion ID '$assertionId' is duplicated."
        }
        $scopeId = Get-RequiredSourceString $assertion "applicability_scope_id" $context
        if (-not $applicabilityScopes.Contains($scopeId)) {
            throw "Source registry '$context.applicability_scope_id' references unknown scope '$scopeId'."
        }
        $scope = $applicabilityScopes[$scopeId]
        if ($scope.target_type -notin @("work", "segment", "content-group", "provenance-claim")) {
            throw "Source registry '$context' scope target type '$($scope.target_type)' cannot carry continuity."
        }
        $continuityId = Get-RequiredSourceString $assertion "continuity_id" $context
        if (-not $continuities.Contains($continuityId)) {
            throw "Source registry '$context.continuity_id' references unknown continuity '$continuityId'."
        }
        $status = Get-RequiredSourceString $assertion "status" $context
        if ($allowedMembershipStatuses -cnotcontains $status) {
            throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')."
        }
        if (-not $seenContinuityScopes.Add("$continuityId|$scopeId")) {
            throw "Source registry repeats continuity '$continuityId' for applicability scope '$scopeId'."
        }
        $scopedContinuityAssertions[$assertionId] = [pscustomobject]@{id=$assertionId
            applicability_scope_id=$scopeId
            continuity_id=$continuityId
            status=$status
        }
    }

    $rawExternalIdentifiers = @(Get-ProjectMapValue $registry "external_identifiers")
    $externalIdentifiers = @()
    $seenExternalIdentifierIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $seenSchemeValues = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawExternalIdentifiers.Count; $index++) {
        $context = "external_identifiers[$index]"
        $identifier = $rawExternalIdentifiers[$index]
        $id = Get-RequiredSourceString $identifier "id" $context
        Test-StableSourceId $id "$context.id"
        if (-not $seenExternalIdentifierIds.Add($id)) {
            throw "Source registry external identifier ID '$id' is duplicated."
        }
        $schemeId = Get-RequiredSourceString $identifier "scheme_id" $context
        if (-not $identifierSchemes.Contains($schemeId)) {
            throw "Source registry '$context.scheme_id' references unknown scheme '$schemeId'."
        }
        $targetType = Get-RequiredSourceString $identifier "target_type" $context
        if ($identifierSchemes[$schemeId].target_types -cnotcontains $targetType) {
            throw "Source registry '$context.target_type' is not allowed by identifier scheme '$schemeId'."
        }
        $targetId = Get-RequiredSourceString $identifier "target_id" $context
        $targetExists = switch ($targetType) {
            "work" {
                $works.Contains($targetId)
            }
            "segment" {
                $segments.Contains($targetId)
            }
            "content-group" {
                $contentGroups.Contains($targetId)
            }
            "manifestation" {
                $manifestations.Contains($targetId)
            }
            "release-package" {
                $releasePackages.Contains($targetId)
            }
            "release-run" {
                $releaseRuns.Contains($targetId)
            }
            "release-event" {
                $releaseEvents.Contains($targetId)
            }
            "platform" {
                $platforms.Contains($targetId)
            }
            "catalog-placement" {
                $catalogPlacements.Contains($targetId)
            }
            "source" {
                $sources.Contains($targetId)
            }
            default {
                $false
            }
        }
        if (-not $targetExists) {
            throw "Source registry '$context.target_id' references unknown $targetType '$targetId'."
        }
        $value = Get-RequiredSourceString $identifier "value" $context
        $normalizedValue = if ($identifierSchemes[$schemeId].case_sensitive) {
            $value
        }
        else {
            ConvertTo-KnowledgeLookupKey $value $lookupKeys
        }
        if (-not $seenSchemeValues.Add("$schemeId|$normalizedValue")) {
            throw "Source registry repeats value '$value' in identifier scheme '$schemeId'."
        }
        $territoryIds = @(Get-SourceStringListAllowEmpty $identifier "territory_ids" $context)
        foreach ($territoryId in $territoryIds) {
            if (-not $territories.Contains($territoryId)) {
                throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'."
            }
        }
        $languageTag = Get-OptionalSourceString $identifier "language_tag" $context
        if ($null -ne $languageTag) {
            Test-SourceLanguageTag $languageTag "$context.language_tag"
        }
        $status = Get-RequiredSourceString $identifier "status" $context
        Assert-SourceSchemaPackValues $SchemaPackRegistry "source.identifier-status" @($status) "$context.status"
        $externalIdentifiers += [pscustomobject]@{ id=$id
            scheme_id=$schemeId
            target_type=$targetType
            target_id=$targetId
            value=$value
            territory_ids=@($territoryIds)
            language_tag=$languageTag
            status=$status
        }
    }

    $nestedIdCollections = [ordered]@{
        "content-group-member"=@($contentGroups.Values | ForEach-Object { $_.members } | ForEach-Object { $_.id })
        "localized-title"=@(
            @(
                @($works.Values) +
                @($segments.Values) +
                @($contentGroups.Values) +
                @($manifestations.Values) +
                @($releasePackages.Values) +
                @($catalogPlacements.Values)
            ) | ForEach-Object { $_.localized_titles } | ForEach-Object { $_.id }
        )
        "release-run-phase"=@($releaseRuns.Values | ForEach-Object { $_.phases } | ForEach-Object { $_.id })
        "source-coverage"=@($sources.Values | ForEach-Object { $_.coverage } | ForEach-Object { $_.id })
        "source-observation"=@($sources.Values | ForEach-Object { $_.observations } | ForEach-Object { $_.id })
        "coverage-position-range"=@($sources.Values | ForEach-Object { $_.coverage } | ForEach-Object { $_.position_ranges } | ForEach-Object { $_.id })
        "authority-rule"=@($authorityProfiles.Values | ForEach-Object { $_.claim_authority_rules } | ForEach-Object { $_.id })
    }
    foreach ($subjectType in $nestedIdCollections.Keys) {
        $ids = @($nestedIdCollections[$subjectType])
        if (@($ids | Sort-Object -Unique).Count -ne $ids.Count) {
            throw "Source registry $subjectType IDs must be unique across owners."
        }
    }

    return [pscustomobject]@{
        path=$registryPath
        schema_version=[int]$schemaVersion
        lookup_keys=$lookupKeys
        default_authority_profile_id=$defaultAuthorityProfileId
        claim_namespace_ancestors=$claimNamespaceAncestors
        evidence_mode_ancestors=$evidenceModeAncestors
        media_modalities=$mediaModalities
        cultural_forms=$culturalForms
        release_forms=$releaseForms
        container_formats=$containerFormats
        mediums=$mediums
        work_group_types=$workGroupTypes
        work_groups=$workGroups
        continuities=$continuities
        continuity_relationship_types=$continuityRelationshipTypes
        continuity_relationships=@($continuityRelationships)
        authority_profiles=$authorityProfiles
        work_relationship_types=$workRelationshipTypes
        works=$works
        work_production_contexts=$workProductionContexts
        applicability_scopes=$applicabilityScopes
        scoped_continuity_assertions=$scopedContinuityAssertions
        segments=$segments
        content_groups=$contentGroups
        ordering_schemes=$orderingSchemes
        numbering_schemes=$numberingSchemes
        work_relationships=@($workRelationships)
        adaptation_mappings=@($adaptationMappings)
        territories=$territories
        platforms=$platforms
        manifestation_relationship_types=$manifestationRelationshipTypes
        manifestations=$manifestations
        manifestation_relationships=@($manifestationRelationships)
        manifestation_segment_mappings=@($manifestationSegmentMappings)
        release_components=$releaseComponents
        release_component_relationship_types=$releaseComponentRelationshipTypes
        release_component_relationships=@($releaseComponentRelationships)
        release_packages=$releasePackages
        release_runs=$releaseRuns
        release_events=$releaseEvents
        catalog_placements=$catalogPlacements
        platform_offerings=$platformOfferings
        identifier_schemes=$identifierSchemes
        external_identifiers=@($externalIdentifiers)
        work_aliases=$workAliases
        source_relationship_types=$sourceRelationshipTypes
        sources=$sources
        source_relationships=@($sourceRelationships)
        source_aliases=$sourceAliases
    }
}

function Get-KnowledgeSourceProvenanceSubjectTypes {
    return @(
        "work"
        "work-production-context"
        "applicability-scope"
        "scoped-continuity-assertion"
        "segment"
        "content-group"
        "work-relationship"
        "adaptation-mapping"
        "manifestation"
        "manifestation-relationship"
        "manifestation-segment-mapping"
        "release-component"
        "release-component-relationship"
        "release-package"
        "release-run"
        "release-event"
        "catalog-placement"
        "platform-offering"
        "source"
        "source-relationship"
        "content-group-member"
        "localized-title"
        "release-run-phase"
        "source-coverage"
        "source-observation"
        "coverage-position-range"
        "authority-rule"
    )
}

function Get-KnowledgeSourceReconciliationTargetTypes {
    return @(
        "medium"
        "work-group"
        "continuity"
        "authority-profile"
        "work"
        "segment"
        "content-group"
        "manifestation"
        "release-component"
        "release-package"
        "release-run"
        "release-event"
        "territory"
        "platform"
        "catalog-placement"
        "platform-offering"
        "source"
    )
}

function Get-KnowledgeSourceReconciliationTargets {
    param([object]$SourceRegistry)
    return [ordered]@{
        medium=$SourceRegistry.mediums
        "work-group"=$SourceRegistry.work_groups
        continuity=$SourceRegistry.continuities
        "authority-profile"=$SourceRegistry.authority_profiles
        work=$SourceRegistry.works
        segment=$SourceRegistry.segments
        "content-group"=$SourceRegistry.content_groups
        manifestation=$SourceRegistry.manifestations
        "release-component"=$SourceRegistry.release_components
        "release-package"=$SourceRegistry.release_packages
        "release-run"=$SourceRegistry.release_runs
        "release-event"=$SourceRegistry.release_events
        territory=$SourceRegistry.territories
        platform=$SourceRegistry.platforms
        "catalog-placement"=$SourceRegistry.catalog_placements
        "platform-offering"=$SourceRegistry.platform_offerings
        source=$SourceRegistry.sources
    }
}

function Get-KnowledgeSourceReconciliationProvider {
    param([object]$SourceRegistry)
    return [pscustomobject]@{
        provider_id="source"
        targets=(Get-KnowledgeSourceReconciliationTargets $SourceRegistry)
        aliases=[ordered]@{work=$SourceRegistry.work_aliases
            source=$SourceRegistry.source_aliases
        }
    }
}

function Get-KnowledgeSourceReconciliationTarget {
    param([object]$SourceRegistry, [string]$TargetType, [string]$TargetId)
    $targets = switch ($TargetType) {
        "medium" {
            $SourceRegistry.mediums
            break
        }
        "work-group" {
            $SourceRegistry.work_groups
            break
        }
        "continuity" {
            $SourceRegistry.continuities
            break
        }
        "authority-profile" {
            $SourceRegistry.authority_profiles
            break
        }
        "work" {
            $SourceRegistry.works
            break
        }
        "segment" {
            $SourceRegistry.segments
            break
        }
        "content-group" {
            $SourceRegistry.content_groups
            break
        }
        "manifestation" {
            $SourceRegistry.manifestations
            break
        }
        "release-component" {
            $SourceRegistry.release_components
            break
        }
        "release-package" {
            $SourceRegistry.release_packages
            break
        }
        "release-run" {
            $SourceRegistry.release_runs
            break
        }
        "release-event" {
            $SourceRegistry.release_events
            break
        }
        "territory" {
            $SourceRegistry.territories
            break
        }
        "platform" {
            $SourceRegistry.platforms
            break
        }
        "catalog-placement" {
            $SourceRegistry.catalog_placements
            break
        }
        "platform-offering" {
            $SourceRegistry.platform_offerings
            break
        }
        "source" {
            $SourceRegistry.sources
            break
        }
        default {
            throw "Unsupported source reconciliation target type '$TargetType'."
        }
    }
    if (-not $targets.Contains($TargetId)) {
        throw "Unknown $TargetType '$TargetId'."
    }
    return $targets[$TargetId]
}

function Get-KnowledgeSourceProvenanceTarget {
    param([object]$SourceRegistry, [string]$SubjectType, [string]$SubjectId)

    $targets = $null
    switch ($SubjectType) {
        "work" {
            $targets = $SourceRegistry.works
        }
        "work-production-context" {
            $targets = $SourceRegistry.work_production_contexts
        }
        "applicability-scope" {
            $targets = $SourceRegistry.applicability_scopes
        }
        "scoped-continuity-assertion" {
            $targets = $SourceRegistry.scoped_continuity_assertions
        }
        "segment" {
            $targets = $SourceRegistry.segments
        }
        "content-group" {
            $targets = $SourceRegistry.content_groups
        }
        "work-relationship" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.work_relationships)
        }
        "adaptation-mapping" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.adaptation_mappings)
        }
        "manifestation" {
            $targets = $SourceRegistry.manifestations
        }
        "manifestation-relationship" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.manifestation_relationships)
        }
        "manifestation-segment-mapping" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.manifestation_segment_mappings)
        }
        "release-component" {
            $targets = $SourceRegistry.release_components
        }
        "release-component-relationship" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.release_component_relationships)
        }
        "release-package" {
            $targets = $SourceRegistry.release_packages
        }
        "release-run" {
            $targets = $SourceRegistry.release_runs
        }
        "release-event" {
            $targets = $SourceRegistry.release_events
        }
        "catalog-placement" {
            $targets = $SourceRegistry.catalog_placements
        }
        "platform-offering" {
            $targets = $SourceRegistry.platform_offerings
        }
        "source" {
            $targets = $SourceRegistry.sources
        }
        "source-relationship" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.source_relationships)
        }
        "content-group-member" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.content_groups.Values | ForEach-Object { $_.members })
        }
        "localized-title" {
            $localizedTitleOwners = @(
                @($SourceRegistry.works.Values) +
                @($SourceRegistry.segments.Values) +
                @($SourceRegistry.content_groups.Values) +
                @($SourceRegistry.manifestations.Values) +
                @($SourceRegistry.release_packages.Values) +
                @($SourceRegistry.catalog_placements.Values)
            )
            $localizedTitles = @($localizedTitleOwners | ForEach-Object { $_.localized_titles })
            $targets = ConvertTo-SourceIdMap $localizedTitles
        }
        "release-run-phase" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.release_runs.Values | ForEach-Object { $_.phases })
        }
        "source-coverage" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.sources.Values | ForEach-Object { $_.coverage })
        }
        "source-observation" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.sources.Values | ForEach-Object { $_.observations })
        }
        "coverage-position-range" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.sources.Values | ForEach-Object { $_.coverage } | ForEach-Object { $_.position_ranges })
        }
        "authority-rule" {
            $targets = ConvertTo-SourceIdMap @($SourceRegistry.authority_profiles.Values | ForEach-Object { $_.claim_authority_rules })
        }
        default {
            throw "Unsupported source-registry subject type '$SubjectType'."
        }
    }
    if (-not $targets.Contains($SubjectId)) {
        throw "Unknown $SubjectType '$SubjectId'."
    }
    return $targets[$SubjectId]
}

function Get-KnowledgeSourceAuthorityDecision {
    param(
        [object]$SourceRegistry,
        [string]$ProfileId,
        [string]$ClaimNamespace,
        [string]$SourceId,
        [AllowNull()][object]$EvidenceMode = $null
    )
    if (-not $SourceRegistry.authority_profiles.Contains($ProfileId)) {
        throw "Unknown authority profile '$ProfileId'."
    }
    if (-not $SourceRegistry.sources.Contains($SourceId)) {
        throw "Unknown source '$SourceId'."
    }
    if (-not $SourceRegistry.claim_namespace_ancestors.Contains($ClaimNamespace)) {
        throw "Unknown claim namespace '$ClaimNamespace'."
    }
    $profile = $SourceRegistry.authority_profiles[$ProfileId]
    $source = $SourceRegistry.sources[$SourceId]
    if ($null -ne $EvidenceMode -and $source.evidence_modes -cnotcontains $EvidenceMode) {
        throw "Evidence mode '$EvidenceMode' is not declared by source '$SourceId'."
    }
    $ancestors = @($SourceRegistry.claim_namespace_ancestors[$ClaimNamespace])
    $matches = @(
        $profile.claim_authority_rules | Where-Object {
            $ancestors -ccontains $_.claim_namespace -and
            (
                Test-SourceAuthorityRuleMatch `
                    $_ $source $EvidenceMode $SourceRegistry.evidence_mode_ancestors
            )
        }
    )
    if ($matches.Count -eq 0) {
        return [pscustomobject]@{source_id=$SourceId
            evidence_mode=$EvidenceMode
            rank=[int]$source.priority
            winning_rule_id=$null
            winning_precedence=$null
            matched_claim_namespace=$ClaimNamespace
            inherited=$false
            claim_namespace_inherited=$false
            evidence_mode_inherited=$false
            priority_fallback=$true
        }
    }
    $highest = [int](($matches | Measure-Object -Property precedence -Maximum).Maximum)
    $winners = @($matches | Where-Object { $_.precedence -eq $highest })
    if ($winners.Count -gt 1) {
        throw "Authority profile '$ProfileId' has ambiguous precedence '$highest' rules for source '$SourceId' and claim namespace '$ClaimNamespace'."
    }
    $winner = $winners[0]
    $namespaceInherited = ([string]$winner.claim_namespace -ne $ClaimNamespace)
    $modeInherited = ($null -ne $EvidenceMode -and $winner.evidence_modes.Count -gt 0 -and $winner.evidence_modes -cnotcontains $EvidenceMode)
    return [pscustomobject]@{source_id=$SourceId
        evidence_mode=$EvidenceMode
        rank=[int]$winner.rank
        winning_rule_id=[string]$winner.id
        winning_precedence=[int]$winner.precedence
        matched_claim_namespace=[string]$winner.claim_namespace
        inherited=($namespaceInherited -or $modeInherited)
        claim_namespace_inherited=$namespaceInherited
        evidence_mode_inherited=$modeInherited
        priority_fallback=$false
    }
}

function Get-KnowledgeSourceAuthorityRank {
    param(
        [object]$SourceRegistry,
        [string]$ProfileId,
        [string]$ClaimNamespace,
        [string]$SourceId,
        [AllowNull()][object]$EvidenceMode = $null
    )
    return [int](Get-KnowledgeSourceAuthorityDecision $SourceRegistry $ProfileId $ClaimNamespace $SourceId $EvidenceMode).rank
}

function Compare-KnowledgeSourceAuthority {
    param([object]$SourceRegistry, [string]$ProfileId, [string]$ClaimNamespace, [object[]]$Candidates)
    if ($Candidates.Count -eq 0) {
        throw "Authority comparison requires at least one candidate."
    }
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $decisions = @()
    foreach ($candidate in $Candidates) {
        $candidateId = [string]$candidate.candidate_id
        if ([string]::IsNullOrWhiteSpace($candidateId) -or -not $seen.Add($candidateId)) {
            throw "Authority comparison candidate IDs must be unique."
        }
        $decision = Get-KnowledgeSourceAuthorityDecision $SourceRegistry $ProfileId $ClaimNamespace ([string]$candidate.source_id) $candidate.evidence_mode
        $decisions += [pscustomobject]@{candidate_id=$candidateId
            assertion_id=$null
            decision=$decision
        }
    }
    $groups = @($decisions | ForEach-Object { $SourceRegistry.sources[$_.decision.source_id].comparison_group } | Sort-Object -Unique)
    if ($groups.Count -ne 1) {
        return [pscustomobject]@{outcome="incomparable"
            profile_id=$ProfileId
            claim_namespace=$ClaimNamespace
            best_rank=$null
            winning_candidate_ids=@()
            decisions=@($decisions)
        }
    }
    $profile = $SourceRegistry.authority_profiles[$ProfileId]
    $bestRank = if ($profile.source_priority_order -eq "ascending") {
        [int](($decisions.decision | Measure-Object -Property rank -Minimum).Minimum)
    }
    else {
        [int](($decisions.decision | Measure-Object -Property rank -Maximum).Maximum)
    }
    $winners = @($decisions | Where-Object { $_.decision.rank -eq $bestRank } | ForEach-Object { $_.candidate_id })
    return [pscustomobject]@{outcome=if ($winners.Count -eq 1) {
            "winner"
        }
        else {
            "tie"
        }
        profile_id=$ProfileId
        claim_namespace=$ClaimNamespace
        best_rank=$bestRank
        winning_candidate_ids=@($winners)
        decisions=@($decisions)
    }
}
