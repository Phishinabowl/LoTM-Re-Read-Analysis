$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) {
  . $projectConfigHelper
}
$resourceConfigHelper = Join-Path $PSScriptRoot "Resource-Config.ps1"
if (-not (Get-Command Get-KnowledgeResourceConfig -ErrorAction SilentlyContinue)) {
  . $resourceConfigHelper
}
$schemaPackConfigHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-KnowledgeSchemaPackRegistry -ErrorAction SilentlyContinue)) {
  . $schemaPackConfigHelper
}

$script:SupportedSourceSchemaVersion = 7
$script:AllowedSourceLifecycles = @("active", "deferred")
$script:AllowedPositionFieldTypes = @("string", "integer", "number", "timestamp", "boolean")
$script:AllowedPriorityOrders = @("ascending", "descending")
$script:AllowedConflictBehaviors = @("flag")
$script:AllowedDeviationOwners = @("derivative-work")
$script:AllowedChapterNumberingModes = @("work-local", "series-global", "not-applicable")
$script:AllowedVolumeCatalogStatuses = @("verified", "pending-verification", "not-applicable")
$script:AllowedOrderingModes = @("total", "partial")
$script:SourceFieldIdPattern = "^[a-z][a-z0-9_]*$"
$script:SourceFieldPathPattern = "^[a-z][a-z0-9_]*(?:(?:\.[a-z][a-z0-9_]*)|(?:\[[0-9]+\]))*$"
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
  if ($null -eq $value) { return $null }
  if ($value -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$value)) {
    throw "Source registry '$Context.$Key' must be a non-empty string when present."
  }
  return ([string]$value).Trim()
}

function Get-SourceStringList {
  param([object]$Map, [string]$Key, [string]$Context)

  $value = Get-ProjectMapValue $Map $Key
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

  if ($Value -notmatch $script:StableProjectIdPattern) {
    throw "Source registry '$Context' must be a lowercase kebab-case stable ID: $Value"
  }
}

function Test-SourceFieldId {
  param([string]$Value, [string]$Context)

  if ($Value -notmatch $script:SourceFieldIdPattern) {
    throw "Source registry '$Context' must be a lowercase snake_case field ID: $Value"
  }
}

function Test-SourceLanguageTag {
  param([string]$Value, [string]$Context)

  if ($Value -notmatch $script:SourceLanguageTagPattern) {
    throw "Source registry '$Context' must be a BCP-47-style language tag: $Value"
  }
}

function ConvertTo-SourceLocalizedTitles {
  param([object]$Map, [string]$Context, [object]$SchemaPackRegistry)

  $titles = @()
  $seenScopes = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($rawTitle in @(Get-ProjectMapValue $Map "localized_titles")) {
    $languageTag = Get-RequiredSourceString $rawTitle "language_tag" "$Context.localized_titles"
    Test-SourceLanguageTag $languageTag "$Context.localized_titles.language_tag"
    $territoryIds = @(Get-SourceStringListAllowEmpty $rawTitle "territory_ids" "$Context.localized_titles")
    $titleType=Get-RequiredSourceString $rawTitle "title_type" "$Context.localized_titles"
    $status=Get-RequiredSourceString $rawTitle "status" "$Context.localized_titles"
    $romanizationScheme=Get-OptionalSourceString $rawTitle "romanization_scheme" "$Context.localized_titles"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.localized-title-type" @($titleType) "$Context.localized_titles.title_type"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.localized-title-status" @($status) "$Context.localized_titles.status"
    $scope = "$languageTag|$(($territoryIds | Sort-Object) -join ',')|$titleType|$romanizationScheme"
    if (-not $seenScopes.Add($scope)) { throw "Source registry '$Context.localized_titles' repeats a locale scope." }
    $titles += [pscustomobject]@{
      language_tag=$languageTag
      territory_ids=@($territoryIds)
      title=Get-RequiredSourceString $rawTitle "title" "$Context.localized_titles"
      title_type=$titleType
      status=$status
      is_primary=Get-RequiredSourceBoolean $rawTitle "is_primary" "$Context.localized_titles"
      romanization_scheme=$romanizationScheme
    }
  }
  return @($titles)
}

function ConvertTo-SourceTemporalWindow {
  param(
    [object]$Map,
    [string]$Key,
    [string]$Context,
    [object]$SchemaPackRegistry
  )

  $rawWindow = Get-ProjectMapValue $Map $Key
  if ($null -eq $rawWindow) { return $null }
  if ($rawWindow -isnot [System.Collections.IDictionary]) { throw "Source registry '$Context.$Key' must be a mapping." }
  $windowContext = "$Context.$Key"
  $precision = Get-RequiredSourceString $rawWindow "precision" $windowContext
  $certainty = Get-RequiredSourceString $rawWindow "certainty" $windowContext
  Assert-SourceSchemaPackValues $SchemaPackRegistry "source.temporal-precision" @($precision) "$windowContext.precision"
  Assert-SourceSchemaPackValues $SchemaPackRegistry "source.temporal-certainty" @($certainty) "$windowContext.certainty"
  $start = Get-OptionalSourceString $rawWindow "start" $windowContext
  $end = Get-OptionalSourceString $rawWindow "end" $windowContext
  $timezone = Get-OptionalSourceString $rawWindow "timezone" $windowContext
  if ($precision -eq "unknown") {
    if ($null -ne $start -or $null -ne $end -or $null -ne $timezone) { throw "Source registry '$windowContext' with unknown precision cannot declare start, end, or timezone." }
  } elseif ($null -eq $start) {
    throw "Source registry '$windowContext.start' is required unless precision is 'unknown'."
  }
  foreach ($entry in @(
    [pscustomobject]@{ name="start"; value=$start },
    [pscustomobject]@{ name="end"; value=$end }
  )) {
    if ($null -eq $entry.value) { continue }
    $valid = $false
    switch ($precision) {
      "year" { $valid = $entry.value -match "^\d{4}$" }
      "month" {
        $parsed = [datetime]::MinValue
        $valid = [datetime]::TryParseExact($entry.value, "yyyy-MM", [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$parsed)
      }
      "date" {
        $parsed = [datetime]::MinValue
        $valid = [datetime]::TryParseExact($entry.value, "yyyy-MM-dd", [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$parsed)
      }
      "datetime" {
        $parsedOffset = [datetimeoffset]::MinValue
        $valid = [datetimeoffset]::TryParse($entry.value, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$parsedOffset)
      }
      "unknown" { $valid = $true }
    }
    if (-not $valid) { throw "Source registry '$windowContext.$($entry.name)' does not match precision '$precision': $($entry.value)" }
  }
  if ($null -ne $timezone -and $precision -ne "datetime") { throw "Source registry '$windowContext.timezone' is only valid for datetime precision." }
  return [pscustomobject]@{ start=$start; end=$end; precision=$precision; certainty=$certainty; timezone=$timezone }
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
    [object]$CulturalForms
  )

  $context = "mediums.$MediumId"
  Test-StableSourceId $MediumId $context
  if ($null -eq $RawMedium -or -not ($RawMedium -is [System.Collections.IDictionary])) {
    throw "Source registry '$context' must be a mapping."
  }
  $lifecycle = Get-RequiredSourceString $RawMedium "lifecycle" $context
  if ($script:AllowedSourceLifecycles -notcontains $lifecycle) {
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
  $incompatibleForms = @($culturalFormIds | Where-Object { $modalityIds -notcontains $CulturalForms[$_].modality_id } | Sort-Object -Unique)
  if ($incompatibleForms.Count -gt 0) {
    throw "Source registry '$context.cultural_form_ids' contains forms whose modalities are absent from 'modality_ids': $($incompatibleForms -join ', ')."
  }
  $position = Get-ProjectMapValue $RawMedium "position"
  if ($null -eq $position -or -not ($position -is [System.Collections.IDictionary])) {
    throw "Source registry '$context.position' must be a mapping."
  }
  $rawFields = Get-ProjectMapValue $position "fields"
  if ($null -eq $rawFields -or -not ($rawFields -is [System.Collections.IDictionary])) {
    throw "Source registry '$context.position.fields' must be a mapping."
  }
  $fields = [ordered]@{}
  foreach ($fieldId in $rawFields.Keys) {
    Test-SourceFieldId $fieldId "$context.position.fields.$fieldId"
    $fieldType = [string]$rawFields[$fieldId]
    if ($script:AllowedPositionFieldTypes -notcontains $fieldType) {
      throw "Source registry '$context.position.fields.$fieldId' must be one of: $($script:AllowedPositionFieldTypes -join ', ')."
    }
    $fields[$fieldId] = $fieldType
  }
  $requiredFields = @(Get-SourceStringList $position "required_fields" "$context.position")
  $sortFields = @(Get-SourceStringList $position "sort_fields" "$context.position")
  foreach ($entry in @(
    [pscustomobject]@{ name = "required_fields"; values = $requiredFields },
    [pscustomobject]@{ name = "sort_fields"; values = $sortFields }
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
  $unknown = @($Values | Where-Object { $allowed -notcontains $_ } | Sort-Object -Unique)
  if ($unknown.Count -gt 0) {
    throw "Source registry '$Context' uses value(s) not provided by the selected schema packs in '$Namespace': $($unknown -join ', ')."
  }
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
  if ($allowedRoots -notcontains $rootId) {
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

  $normalized = $Value.Trim().ToLowerInvariant()
  foreach ($sourceId in $SourceRegistry.sources.Keys) {
    if ($sourceId.ToLowerInvariant() -eq $normalized) {
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

  $normalized = $Value.Trim().ToLowerInvariant()
  foreach ($workId in $SourceRegistry.works.Keys) {
    if ($workId.ToLowerInvariant() -eq $normalized) {
      return $workId
    }
  }
  if ($SourceRegistry.work_aliases.ContainsKey($normalized)) {
    return $SourceRegistry.work_aliases[$normalized]
  }
  return $null
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
  $allowedSourceRoles = @(Get-SchemaPackAllowedValues $SchemaPackRegistry "source.source-role")
  if ($allowedSourceRoles.Count -eq 0) {
    throw "Selected schema packs do not provide controlled namespace 'source.source-role' required by 'sources.*.role'."
  }
  $allowedMembershipStatuses = @(Get-SchemaPackAllowedValues $SchemaPackRegistry "source.membership-status")
  if ($allowedMembershipStatuses.Count -eq 0) {
    throw "Selected schema packs do not provide controlled namespace 'source.membership-status' required by continuity memberships and relationship statuses."
  }
  $registryPath = $ProjectConfig.sources_registry
  $registry = ConvertFrom-Yaml -Yaml ([System.IO.File]::ReadAllText($registryPath, [System.Text.UTF8Encoding]::new($true))) -Ordered
  if ($null -eq $registry -or -not ($registry -is [System.Collections.IDictionary])) {
    throw "Source registry root must be a mapping: $registryPath"
  }
  $schemaVersion = Get-ProjectMapValue $registry "schema_version"
  if ([int]$schemaVersion -ne $script:SupportedSourceSchemaVersion) {
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
    $mediums[$mediumId] = ConvertTo-MediumConfig $mediumId $rawMediums[$mediumId] $mediaModalities $culturalForms
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
    $lifecycle = Get-RequiredSourceString $group "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) {
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
      parent_group_id = if ([string]::IsNullOrWhiteSpace($parentGroupId)) { $null } else { $parentGroupId }
    }
  }
  foreach ($group in $workGroups.Values) {
    if ($null -eq $group.parent_group_id) { continue }
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
  $continuityAliases = @{}
  foreach ($continuityId in $rawContinuities.Keys) {
    $context = "continuities.$continuityId"
    Test-StableSourceId $continuityId $context
    $continuity = $rawContinuities[$continuityId]
    $lifecycle = Get-RequiredSourceString $continuity "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) {
      throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
    }
    $continuityType = Get-RequiredSourceString $continuity "continuity_type" $context
    Test-StableSourceId $continuityType "$context.continuity_type"
    $aliases = @(Get-SourceStringList $continuity "aliases" $context)
    foreach ($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"
      $aliasKey = $alias.ToLowerInvariant()
      if ($continuityAliases.ContainsKey($aliasKey) -or @($rawContinuities.Keys | Where-Object { $_.ToLowerInvariant() -eq $aliasKey }).Count -gt 0) {
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
    $id = Get-RequiredSourceString $relationship "id" $context
    Test-StableSourceId $id "$context.id"
    if (-not $seenRelationshipIds.Add($id)) { throw "Source registry relationship ID '$id' is duplicated." }
    $sourceId = Get-RequiredSourceString $relationship "source_continuity_id" $context
    $targetId = Get-RequiredSourceString $relationship "target_continuity_id" $context
    $type = Get-RequiredSourceString $relationship "relationship_type" $context
    if (-not $continuities.Contains($sourceId) -or -not $continuities.Contains($targetId)) { throw "Source registry '$context' references an unknown continuity." }
    if ($sourceId -eq $targetId) { throw "Source registry '$context' cannot relate a continuity to itself." }
    if (-not $continuityRelationshipTypes.Contains($type)) { throw "Source registry '$context.relationship_type' references unknown type '$type'." }
    $status = Get-RequiredSourceString $relationship "status" $context
    if ($allowedMembershipStatuses -notcontains $status) { throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')." }
    $continuityRelationships += [pscustomobject]@{ id=$id; source_continuity_id=$sourceId; relationship_type=$type; target_continuity_id=$targetId; status=$status }
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
    $lifecycle = Get-RequiredSourceString $profile "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $continuityOrder = @(Get-SourceStringList $profile "continuity_order" $context)
    if (@($continuityOrder | Sort-Object -Unique).Count -ne $continuityOrder.Count) { throw "Source registry '$context.continuity_order' contains duplicates." }
    foreach ($continuityId in $continuityOrder) { if (-not $continuities.Contains($continuityId)) { throw "Source registry '$context.continuity_order' references unknown continuity '$continuityId'." } }
    $acceptedStatuses = @(Get-SourceStringList $profile "accepted_membership_statuses" $context)
    foreach ($status in $acceptedStatuses) { if ($allowedMembershipStatuses -notcontains $status) { throw "Source registry '$context.accepted_membership_statuses' contains unknown value '$status'." } }
    $priorityOrder = Get-RequiredSourceString $profile "source_priority_order" $context
    if ($script:AllowedPriorityOrders -notcontains $priorityOrder) { throw "Source registry '$context.source_priority_order' must be one of: $($script:AllowedPriorityOrders -join ', ')." }
    $comparisonTypes = @(Get-SourceStringListAllowEmpty $profile "comparison_work_relationship_types" $context)
    foreach ($type in $comparisonTypes) { if (-not $workRelationshipTypes.Contains($type)) { throw "Source registry '$context.comparison_work_relationship_types' references unknown type '$type'." } }
    $conflict = Get-RequiredSourceString $profile "cross_source_conflict" $context
    if ($script:AllowedConflictBehaviors -notcontains $conflict) { throw "Source registry '$context.cross_source_conflict' must be one of: $($script:AllowedConflictBehaviors -join ', ')." }
    $deviationOwner = Get-RequiredSourceString $profile "derivative_deviation_owner" $context
    if ($script:AllowedDeviationOwners -notcontains $deviationOwner) { throw "Source registry '$context.derivative_deviation_owner' must be one of: $($script:AllowedDeviationOwners -join ', ')." }
    $authorityProfiles[$profileId] = [pscustomobject]@{
      id=$profileId; lifecycle=$lifecycle; label=Get-RequiredSourceString $profile "label" $context
      continuity_order=@($continuityOrder); accepted_membership_statuses=@($acceptedStatuses)
      source_priority_order=$priorityOrder; comparison_work_relationship_types=@($comparisonTypes)
      cross_source_conflict=$conflict; derivative_deviation_owner=$deviationOwner
      preserve_source_scoped_claims=Get-RequiredSourceBoolean $profile "preserve_source_scoped_claims" $context
    }
  }
  $defaultAuthorityProfileId = Get-RequiredSourceString $registry "default_authority_profile_id" "root"
  if (-not $authorityProfiles.Contains($defaultAuthorityProfileId)) { throw "Source registry 'default_authority_profile_id' references unknown authority profile '$defaultAuthorityProfileId'." }

  $rawWorks = Get-ProjectMapValue $registry "works"
  if ($null -eq $rawWorks -or -not ($rawWorks -is [System.Collections.IDictionary])) { throw "Source registry 'works' must be a mapping." }
  $works = [ordered]@{}
  $workAliases = @{}
  $seenOrdinals = @{}
  foreach ($workId in $rawWorks.Keys) {
    $context = "works.$workId"
    Test-StableSourceId $workId $context
    $work = $rawWorks[$workId]
    $lifecycle = Get-RequiredSourceString $work "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $mediumId = Get-RequiredSourceString $work "medium_id" $context
    if (-not $mediums.Contains($mediumId)) { throw "Source registry '$context.medium_id' references unknown medium '$mediumId'." }
    $workType = Get-RequiredSourceString $work "work_type" $context
    Test-StableSourceId $workType "$context.work_type"
    $releaseFormId = Get-RequiredSourceString $work "release_form_id" $context
    if (-not $releaseForms.Contains($releaseFormId)) { throw "Source registry '$context.release_form_id' references unknown release form '$releaseFormId'." }
    $workStatus = Get-RequiredSourceString $work "work_status" $context
    Test-StableSourceId $workStatus "$context.work_status"
    $chapterNumbering = Get-RequiredSourceString $work "chapter_numbering" $context
    if ($script:AllowedChapterNumberingModes -notcontains $chapterNumbering) { throw "Source registry '$context.chapter_numbering' must be one of: $($script:AllowedChapterNumberingModes -join ', ')." }
    $volumeStatus = Get-RequiredSourceString $work "volume_catalog_status" $context
    if ($script:AllowedVolumeCatalogStatuses -notcontains $volumeStatus) { throw "Source registry '$context.volume_catalog_status' must be one of: $($script:AllowedVolumeCatalogStatuses -join ', ')." }
    $aliases = @(Get-SourceStringList $work "aliases" $context)
    foreach ($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"
      $aliasKey = $alias.ToLowerInvariant()
      if ($workAliases.ContainsKey($aliasKey) -or @($rawWorks.Keys | Where-Object { $_.ToLowerInvariant() -eq $aliasKey }).Count -gt 0) { throw "Source registry work alias '$alias' is duplicated or collides with a work ID." }
      $workAliases[$aliasKey] = $workId
    }
    $groupMemberships = @()
    $seenGroups = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($membership in @(Get-ProjectMapValue $work "group_memberships")) {
      $groupId = Get-RequiredSourceString $membership "group_id" "$context.group_memberships"
      if (-not $workGroups.Contains($groupId)) { throw "Source registry '$context.group_memberships.group_id' references unknown work group '$groupId'." }
      if (-not $seenGroups.Add($groupId)) { throw "Source registry '$context' repeats work group '$groupId'." }
      $role = Get-RequiredSourceString $membership "role" "$context.group_memberships"
      Test-StableSourceId $role "$context.group_memberships.role"
      $ordinal = Get-ProjectMapValue $membership "ordinal"
      $ordered = $workGroupTypes[$workGroups[$groupId].group_type].ordered
      if ($ordered -and ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1)) { throw "Source registry '$context.group_memberships.ordinal' must be a positive integer for an ordered work group." }
      if (-not $ordered -and $null -ne $ordinal) { throw "Source registry '$context.group_memberships.ordinal' is only valid for ordered work groups." }
      if ($ordered) {
        $ordinalKey = "$groupId|$ordinal"
        if ($seenOrdinals.ContainsKey($ordinalKey)) { throw "Source registry duplicates ordinal $ordinal in work group '$groupId' between '$($seenOrdinals[$ordinalKey])' and '$workId'." }
        $seenOrdinals[$ordinalKey] = $workId
      }
      $groupMemberships += [pscustomobject]@{ group_id=$groupId; role=$role; ordinal=if($null -eq $ordinal){$null}else{[int]$ordinal} }
    }
    if ($groupMemberships.Count -eq 0) { throw "Source registry '$context.group_memberships' must be a non-empty list." }
    $continuityMemberships = @()
    $seenContinuities = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($membership in @(Get-ProjectMapValue $work "continuity_memberships")) {
      $continuityId = Get-RequiredSourceString $membership "continuity_id" "$context.continuity_memberships"
      if (-not $continuities.Contains($continuityId)) { throw "Source registry '$context.continuity_memberships.continuity_id' references unknown continuity '$continuityId'." }
      if (-not $seenContinuities.Add($continuityId)) { throw "Source registry '$context' repeats continuity '$continuityId'." }
      $status = Get-RequiredSourceString $membership "status" "$context.continuity_memberships"
      if ($allowedMembershipStatuses -notcontains $status) { throw "Source registry '$context.continuity_memberships.status' must be one of: $($allowedMembershipStatuses -join ', ')." }
      $continuityMemberships += [pscustomobject]@{ continuity_id=$continuityId; status=$status }
    }
    if ($continuityMemberships.Count -eq 0) { throw "Source registry '$context.continuity_memberships' must be a non-empty list." }
    $rawVolumes = @(Get-ProjectMapValue $work "volumes")
    if ($volumeStatus -eq "verified" -and $rawVolumes.Count -eq 0) { throw "Source registry verified work '$workId' requires volume records." }
    $volumes = @()
    $seenVolumeIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $seenVolumeNumbers = New-Object 'System.Collections.Generic.HashSet[int]'
    foreach ($volume in $rawVolumes) {
      $volumeId = Get-RequiredSourceString $volume "id" "$context.volumes"
      Test-StableSourceId $volumeId "$context.volumes.id"
      if (-not $seenVolumeIds.Add($volumeId)) { throw "Source registry '$context' duplicates volume ID '$volumeId'." }
      $number = Get-ProjectMapValue $volume "number"; $chapterStart = Get-ProjectMapValue $volume "chapter_start"; $chapterEnd = Get-ProjectMapValue $volume "chapter_end"
      foreach ($value in @($number,$chapterStart,$chapterEnd)) { if ($value -is [bool] -or $value -isnot [int] -or [int]$value -lt 1) { throw "Source registry '$context.volumes' numeric fields must be positive integers." } }
      if (-not $seenVolumeNumbers.Add([int]$number)) { throw "Source registry '$context' duplicates volume number $number." }
      if ([int]$chapterEnd -lt [int]$chapterStart) { throw "Source registry '$context.volumes' chapter range is reversed." }
      $volumes += [pscustomobject]@{ id=$volumeId; number=[int]$number; label=Get-RequiredSourceString $volume "label" "$context.volumes"; chapter_start=[int]$chapterStart; chapter_end=[int]$chapterEnd }
    }
    $volumes = @($volumes | Sort-Object number)
    if ($volumeStatus -eq "verified") {
      for ($i=0; $i -lt $volumes.Count; $i++) {
        if ($volumes[$i].number -ne $i+1) { throw "Source registry '$context' verified volume numbers must be contiguous from 1." }
        if ($i -gt 0 -and $volumes[$i].chapter_start -ne $volumes[$i-1].chapter_end+1) { throw "Source registry '$context' verified chapter ranges must be contiguous and non-overlapping." }
      }
    }
    $works[$workId] = [pscustomobject]@{
      id=$workId; lifecycle=$lifecycle; label=Get-RequiredSourceString $work "label" $context
      short_label=Get-RequiredSourceString $work "short_label" $context; work_type=$workType
      parent_work_id=Get-OptionalSourceString $work "parent_work_id" $context
      medium_id=$mediumId; release_form_id=$releaseFormId; work_status=$workStatus
      aliases=@($aliases); group_memberships=@($groupMemberships)
      localized_titles=@(ConvertTo-SourceLocalizedTitles $work $context $SchemaPackRegistry)
      continuity_memberships=@($continuityMemberships); chapter_numbering=$chapterNumbering
      volume_catalog_status=$volumeStatus; volumes=@($volumes)
    }
  }
  Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-type" @($works.Values | ForEach-Object { $_.work_type }) "works.*.work_type"
  Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-lifecycle-status" @($works.Values | ForEach-Object { $_.work_status }) "works.*.work_status"
  foreach ($work in $works.Values) {
    if ($null -eq $work.parent_work_id) { continue }
    if (-not $works.Contains($work.parent_work_id)) { throw "Source registry 'works.$($work.id).parent_work_id' references unknown work '$($work.parent_work_id)'." }
    if ($work.parent_work_id -eq $work.id) { throw "Source registry work '$($work.id)' cannot parent itself." }
  }
  foreach ($workId in $works.Keys) {
    $activeWorks = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $currentWorkId = $workId
    while ($null -ne $currentWorkId) {
      if (-not $activeWorks.Add($currentWorkId)) { throw "Source registry contains a work-parent cycle involving '$currentWorkId'." }
      $currentWorkId = $works[$currentWorkId].parent_work_id
    }
  }

  $rawSegments = Get-ProjectMapValue $registry "segments"
  if ($null -eq $rawSegments -or -not ($rawSegments -is [System.Collections.IDictionary])) { throw "Source registry 'segments' must be a mapping." }
  $segments = [ordered]@{}
  foreach ($segmentId in $rawSegments.Keys) {
    $context = "segments.$segmentId"
    Test-StableSourceId $segmentId $context
    $segment = $rawSegments[$segmentId]
    $workId = Get-RequiredSourceString $segment "work_id" $context
    if (-not $works.Contains($workId)) { throw "Source registry '$context.work_id' references unknown work '$workId'." }
    $parentSegmentId = ([string](Get-ProjectMapValue $segment "parent_segment_id" "")).Trim()
    $segmentType = Get-RequiredSourceString $segment "segment_type" $context
    Test-StableSourceId $segmentType "$context.segment_type"
    $ordinal = Get-ProjectMapValue $segment "ordinal"
    if ($null -ne $ordinal -and ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1)) { throw "Source registry '$context.ordinal' must be a positive integer when present." }
    $segments[$segmentId] = [pscustomobject]@{
      id=$segmentId; work_id=$workId
      parent_segment_id=if([string]::IsNullOrWhiteSpace($parentSegmentId)){$null}else{$parentSegmentId}
      segment_type=$segmentType; label=Get-RequiredSourceString $segment "label" $context
      aliases=@(Get-SourceStringListAllowEmpty $segment "aliases" $context)
      localized_titles=@(ConvertTo-SourceLocalizedTitles $segment $context $SchemaPackRegistry)
      ordinal=if($null -eq $ordinal){$null}else{[int]$ordinal}
    }
  }
  if ($segments.Count -gt 0) {
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.segment-type" @($segments.Values | ForEach-Object { $_.segment_type }) "segments.*.segment_type"
  }
  foreach ($segment in $segments.Values) {
    if ($null -eq $segment.parent_segment_id) { continue }
    if (-not $segments.Contains($segment.parent_segment_id)) { throw "Source registry 'segments.$($segment.id).parent_segment_id' references unknown segment '$($segment.parent_segment_id)'." }
    $parent = $segments[$segment.parent_segment_id]
    if ($parent.id -eq $segment.id) { throw "Source registry segment '$($segment.id)' cannot parent itself." }
    if ($parent.work_id -ne $segment.work_id) { throw "Source registry segment '$($segment.id)' and its parent must belong to the same work." }
  }
  foreach ($segmentId in $segments.Keys) {
    $activeSegments = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $currentSegmentId = $segmentId
    while ($null -ne $currentSegmentId) {
      if (-not $activeSegments.Add($currentSegmentId)) { throw "Source registry contains a segment-parent cycle involving '$currentSegmentId'." }
      $currentSegmentId = $segments[$currentSegmentId].parent_segment_id
    }
  }

  $segmentAliasesByWork = @{}
  foreach ($segment in $segments.Values) {
    if (-not $segmentAliasesByWork.ContainsKey($segment.work_id)) {
      $segmentAliasesByWork[$segment.work_id] = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    }
    foreach ($alias in $segment.aliases) {
      Test-StableSourceId $alias "segments.$($segment.id).aliases"
      $collides = @($segments.Values | Where-Object { $_.work_id -eq $segment.work_id -and $_.id -eq $alias }).Count -gt 0
      if ($collides -or -not $segmentAliasesByWork[$segment.work_id].Add($alias)) { throw "Source registry segment alias '$alias' is duplicated or collides inside work '$($segment.work_id)'." }
    }
  }

  $rawNumberingSchemes = Get-ProjectMapValue $registry "numbering_schemes"
  if ($null -eq $rawNumberingSchemes -or -not ($rawNumberingSchemes -is [System.Collections.IDictionary])) { throw "Source registry 'numbering_schemes' must be a mapping." }
  $numberingSchemes = [ordered]@{}
  foreach ($schemeId in $rawNumberingSchemes.Keys) {
    $context="numbering_schemes.$schemeId"; Test-StableSourceId $schemeId $context; $scheme=$rawNumberingSchemes[$schemeId]
    $targetType=Get-RequiredSourceString $scheme "target_type" $context
    $scopeType=Get-RequiredSourceString $scheme "scope_type" $context
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.numbering-target-type" @($targetType) "$context.target_type"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.numbering-scope-type" @($scopeType) "$context.scope_type"
    $scopeId=Get-OptionalSourceString $scheme "scope_id" $context
    if ($scopeType -eq "none" -and $null -ne $scopeId) { throw "Source registry '$context.scope_id' must be omitted for none scope." }
    if ($scopeType -eq "work") {
      if ($null -eq $scopeId -or -not $works.Contains($scopeId)) { throw "Source registry '$context.scope_id' references unknown work '$scopeId'." }
      if ($targetType -ne "segment") { throw "Source registry '$context' work scope requires segment targets." }
    }
    if ($scopeType -eq "work-group") {
      if ($null -eq $scopeId -or -not $workGroups.Contains($scopeId)) { throw "Source registry '$context.scope_id' references unknown work group '$scopeId'." }
      if ($targetType -ne "work") { throw "Source registry '$context' work-group scope requires work targets." }
    }
    $rawEntries=@(Get-ProjectMapValue $scheme "entries")
    if ($rawEntries.Count -eq 0) { throw "Source registry '$context.entries' must be a non-empty list." }
    $entries=@(); $seenTargets=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal); $seenNumbers=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($entry in $rawEntries) {
      $targetId=Get-RequiredSourceString $entry "target_id" "$context.entries"
      $targets=if($targetType -eq "work"){$works}else{$segments}
      if (-not $targets.Contains($targetId)) { throw "Source registry '$context.entries.target_id' references unknown $targetType '$targetId'." }
      if ($scopeType -eq "work" -and $segments[$targetId].work_id -ne $scopeId) { throw "Source registry '$context.entries' target falls outside work scope '$scopeId'." }
      if ($scopeType -eq "work-group") {
        $insideGroup=@($works[$targetId].group_memberships | Where-Object { $_.group_id -eq $scopeId }).Count -gt 0
        if (-not $insideGroup) { throw "Source registry '$context.entries' target falls outside work group scope '$scopeId'." }
      }
      $displayNumber=Get-RequiredSourceString $entry "display_number" "$context.entries"; $aliases=@(Get-SourceStringListAllowEmpty $entry "aliases" "$context.entries")
      if (-not $seenTargets.Add($targetId) -or -not $seenNumbers.Add($displayNumber)) { throw "Source registry '$context.entries' repeats a target or number." }
      foreach ($alias in $aliases) { if (-not $seenNumbers.Add($alias)) { throw "Source registry '$context.entries' repeats number alias '$alias'." } }
      $entries += [pscustomobject]@{ target_id=$targetId; display_number=$displayNumber; aliases=@($aliases) }
    }
    $lifecycle=Get-RequiredSourceString $scheme "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $numberingSchemes[$schemeId]=[pscustomobject]@{ id=$schemeId; lifecycle=$lifecycle; label=Get-RequiredSourceString $scheme "label" $context; target_type=$targetType; scope_type=$scopeType; scope_id=$scopeId; entries=@($entries) }
  }

  $rawOrderingSchemes = Get-ProjectMapValue $registry "ordering_schemes"
  if ($null -eq $rawOrderingSchemes -or -not ($rawOrderingSchemes -is [System.Collections.IDictionary])) { throw "Source registry 'ordering_schemes' must be a mapping." }
  $orderingSchemes = [ordered]@{}
  foreach ($schemeId in $rawOrderingSchemes.Keys) {
    $context = "ordering_schemes.$schemeId"
    Test-StableSourceId $schemeId $context
    $scheme = $rawOrderingSchemes[$schemeId]
    $orderingType = Get-RequiredSourceString $scheme "ordering_type" $context
    Test-StableSourceId $orderingType "$context.ordering_type"
    $orderingMode = Get-RequiredSourceString $scheme "ordering_mode" $context
    if ($script:AllowedOrderingModes -notcontains $orderingMode) { throw "Source registry '$context.ordering_mode' must be one of: $($script:AllowedOrderingModes -join ', ')." }
    $rawEntries = @(Get-ProjectMapValue $scheme "entries")
    if ($rawEntries.Count -eq 0) { throw "Source registry '$context.entries' must be a non-empty list." }
    $entries = @()
    $seenEntryIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $seenTargets = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $seenOrderingOrdinals = New-Object 'System.Collections.Generic.HashSet[int]'
    for ($index=0; $index -lt $rawEntries.Count; $index++) {
      $entryContext = "$context.entries[$index]"
      $entry = $rawEntries[$index]
      $entryId = Get-RequiredSourceString $entry "id" $entryContext
      Test-StableSourceId $entryId "$entryContext.id"
      if (-not $seenEntryIds.Add($entryId)) { throw "Source registry '$context.entries' repeats entry ID '$entryId'." }
      $targetType = Get-RequiredSourceString $entry "target_type" $entryContext
      if ($targetType -notin @("work","segment")) { throw "Source registry '$entryContext.target_type' must be 'work' or 'segment'." }
      $targetId = Get-RequiredSourceString $entry "target_id" $entryContext
      $targetRegistry = if ($targetType -eq "work") { $works } else { $segments }
      if (-not $targetRegistry.Contains($targetId)) { throw "Source registry '$entryContext.target_id' references unknown $targetType '$targetId'." }
      $ordinal = Get-ProjectMapValue $entry "ordinal"
      $afterEntryIds = @(Get-SourceStringListAllowEmpty $entry "after_entry_ids" $entryContext)
      foreach ($predecessorId in $afterEntryIds) { Test-StableSourceId $predecessorId "$entryContext.after_entry_ids" }
      if ($orderingMode -eq "total") {
        if ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1) { throw "Source registry '$entryContext.ordinal' must be a positive integer for total ordering." }
        if ($afterEntryIds.Count -gt 0) { throw "Source registry '$entryContext.after_entry_ids' must be empty for total ordering." }
      } elseif ($null -ne $ordinal) {
        throw "Source registry '$entryContext.ordinal' must be omitted for partial ordering."
      }
      if (-not $seenTargets.Add("$targetType|$targetId")) { throw "Source registry '$context.entries' repeats a target." }
      if ($null -ne $ordinal -and -not $seenOrderingOrdinals.Add([int]$ordinal)) { throw "Source registry '$context.entries' repeats an ordinal." }
      $entries += [pscustomobject]@{ id=$entryId; target_type=$targetType; target_id=$targetId; ordinal=if($null -eq $ordinal){$null}else{[int]$ordinal}; after_entry_ids=@($afterEntryIds) }
    }
    if ($orderingMode -eq "partial") {
      foreach ($entry in $entries) {
        foreach ($predecessorId in $entry.after_entry_ids) {
          if (-not $seenEntryIds.Contains($predecessorId)) { throw "Source registry '$context' entry '$($entry.id)' references unknown predecessor '$predecessorId'." }
          if ($predecessorId -eq $entry.id) { throw "Source registry '$context' entry '$($entry.id)' cannot follow itself." }
        }
      }
      $remainingPredecessors = @{}
      foreach ($entry in $entries) { $remainingPredecessors[$entry.id] = [int]$entry.after_entry_ids.Count }
      $readyEntries = New-Object System.Collections.Queue
      foreach ($entry in $entries) { if ($remainingPredecessors[$entry.id] -eq 0) { $readyEntries.Enqueue($entry.id) } }
      $processedEntries = 0
      while ($readyEntries.Count -gt 0) {
        $currentEntryId = [string]$readyEntries.Dequeue()
        $processedEntries++
        foreach ($dependent in @($entries | Where-Object { $_.after_entry_ids -contains $currentEntryId })) {
          $remainingPredecessors[$dependent.id]--
          if ($remainingPredecessors[$dependent.id] -eq 0) { $readyEntries.Enqueue($dependent.id) }
        }
      }
      if ($processedEntries -ne $entries.Count) {
        throw "Source registry '$context' contains a partial-order cycle."
      }
    }
    $orderingSchemes[$schemeId] = [pscustomobject]@{
      id=$schemeId; label=Get-RequiredSourceString $scheme "label" $context
      ordering_type=$orderingType; ordering_mode=$orderingMode
      entries=@(if($orderingMode -eq "total"){$entries | Sort-Object ordinal}else{$entries})
    }
  }
  if ($orderingSchemes.Count -gt 0) {
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.ordering-type" @($orderingSchemes.Values | ForEach-Object { $_.ordering_type }) "ordering_schemes.*.ordering_type"
  }

  $rawContentGroups=Get-ProjectMapValue $registry "content_groups"
  if ($null -eq $rawContentGroups -or -not ($rawContentGroups -is [System.Collections.IDictionary])) { throw "Source registry 'content_groups' must be a mapping." }
  $contentGroups=[ordered]@{}
  $contentGroupAliasKeys=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($groupId in $rawContentGroups.Keys) {
    $context="content_groups.$groupId"; Test-StableSourceId $groupId $context; $group=$rawContentGroups[$groupId]
    $rawMembers=@(Get-ProjectMapValue $group "members")
    if($rawMembers.Count -eq 0){throw "Source registry '$context.members' must be a non-empty list."}
    $members=@();$seenMembers=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for($memberIndex=0;$memberIndex -lt $rawMembers.Count;$memberIndex++){
      $memberContext="$context.members[$memberIndex]";$member=$rawMembers[$memberIndex]
      $targetType=Get-RequiredSourceString $member "target_type" $memberContext
      $targetId=Get-RequiredSourceString $member "target_id" $memberContext
      $exists=if($targetType -eq "work"){$works.Contains($targetId)}elseif($targetType -eq "segment"){$segments.Contains($targetId)}else{$false}
      if(-not $exists){throw "Source registry '$memberContext' references unknown or unsupported $targetType '$targetId'."}
      if(-not $seenMembers.Add("$targetType|$targetId")){throw "Source registry '$context.members' contains duplicates."}
      $members += [pscustomobject]@{target_type=$targetType;target_id=$targetId}
    }
    $parentGroupIds=@(Get-SourceStringListAllowEmpty $group "parent_group_ids" $context)
    if ($parentGroupIds -contains $groupId -or @($parentGroupIds | Sort-Object -Unique).Count -ne $parentGroupIds.Count) { throw "Source registry '$context.parent_group_ids' contains a self reference or duplicate." }
    $orderingSchemeId=Get-OptionalSourceString $group "ordering_scheme_id" $context
    if ($null -ne $orderingSchemeId) {
      if (-not $orderingSchemes.Contains($orderingSchemeId)) { throw "Source registry '$context.ordering_scheme_id' references unknown ordering scheme '$orderingSchemeId'." }
      $orderedEntries=@($orderingSchemes[$orderingSchemeId].entries)
      $orderedMembers=@($orderedEntries|ForEach-Object {"$($_.target_type)|$($_.target_id)"}|Sort-Object)
      $memberKeys=@($members|ForEach-Object {"$($_.target_type)|$($_.target_id)"}|Sort-Object)
      if(Compare-Object $memberKeys $orderedMembers){throw "Source registry '$context.ordering_scheme_id' must order exactly the group's members."}
    }
    $aliases=@(Get-SourceStringListAllowEmpty $group "aliases" $context)
    foreach($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"
      $collides=@($rawContentGroups.Keys | Where-Object {$_.ToLowerInvariant() -eq $alias.ToLowerInvariant()}).Count -gt 0
      if($collides -or -not $contentGroupAliasKeys.Add($alias)){throw "Source registry content-group alias '$alias' is duplicated or collides with a group ID."}
    }
    $lifecycle=Get-RequiredSourceString $group "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $contentGroups[$groupId]=[pscustomobject]@{id=$groupId;lifecycle=$lifecycle;label=Get-RequiredSourceString $group "label" $context;group_type=Get-RequiredSourceString $group "group_type" $context;members=@($members);parent_group_ids=@($parentGroupIds);ordering_scheme_id=$orderingSchemeId;localized_titles=@(ConvertTo-SourceLocalizedTitles $group $context $SchemaPackRegistry);aliases=@($aliases)}
  }
  if($contentGroups.Count -gt 0){Assert-SourceSchemaPackValues $SchemaPackRegistry "source.content-group-type" @($contentGroups.Values|ForEach-Object {$_.group_type}) "content_groups.*.group_type"}
  foreach($group in $contentGroups.Values){foreach($parentId in $group.parent_group_ids){if(-not $contentGroups.Contains($parentId)){throw "Source registry content group '$($group.id)' references unknown parent '$parentId'."}}}
  $remainingGroupParents=@{};$readyGroups=New-Object System.Collections.Queue
  foreach($group in $contentGroups.Values){$remainingGroupParents[$group.id]=[int]$group.parent_group_ids.Count;if($group.parent_group_ids.Count -eq 0){$readyGroups.Enqueue($group.id)}}
  $processedGroups=0
  while($readyGroups.Count -gt 0){$currentGroupId=[string]$readyGroups.Dequeue();$processedGroups++;foreach($child in @($contentGroups.Values|Where-Object {$_.parent_group_ids -contains $currentGroupId})){$remainingGroupParents[$child.id]--;if($remainingGroupParents[$child.id] -eq 0){$readyGroups.Enqueue($child.id)}}}
  if($processedGroups -ne $contentGroups.Count){throw "Source registry contains a content-group cycle."}

  $workRelationships = @()
  $rawWorkRelationships = @(Get-ProjectMapValue $registry "work_relationships")
  for ($index=0; $index -lt $rawWorkRelationships.Count; $index++) {
    $context = "work_relationships[$index]"; $relationship = $rawWorkRelationships[$index]
    $id = Get-RequiredSourceString $relationship "id" $context; Test-StableSourceId $id "$context.id"
    if (-not $seenRelationshipIds.Add($id)) { throw "Source registry relationship ID '$id' is duplicated." }
    $sourceId=Get-RequiredSourceString $relationship "source_work_id" $context; $targetId=Get-RequiredSourceString $relationship "target_work_id" $context
    $type=Get-RequiredSourceString $relationship "relationship_type" $context
    if (-not $works.Contains($sourceId) -or -not $works.Contains($targetId)) { throw "Source registry '$context' references an unknown work." }
    if ($sourceId -eq $targetId) { throw "Source registry '$context' cannot relate a work to itself." }
    if (-not $workRelationshipTypes.Contains($type)) { throw "Source registry '$context.relationship_type' references unknown type '$type'." }
    $continuityIds=@(Get-SourceStringList $relationship "continuity_ids" $context)
    foreach ($continuityId in $continuityIds) { if (-not $continuities.Contains($continuityId)) { throw "Source registry '$context.continuity_ids' references unknown continuity '$continuityId'." } }
    $status=Get-RequiredSourceString $relationship "status" $context
    if ($allowedMembershipStatuses -notcontains $status) { throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')." }
    $workRelationships += [pscustomobject]@{ id=$id; source_work_id=$sourceId; relationship_type=$type; target_work_id=$targetId; continuity_ids=@($continuityIds); status=$status }
  }

  $adaptationMappings = @()
  $rawAdaptationMappings = @(Get-ProjectMapValue $registry "adaptation_mappings")
  $seenAdaptationMappingIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for ($index=0; $index -lt $rawAdaptationMappings.Count; $index++) {
    $context = "adaptation_mappings[$index]"
    $mapping = $rawAdaptationMappings[$index]
    $id = Get-RequiredSourceString $mapping "id" $context
    Test-StableSourceId $id "$context.id"
    if (-not $seenAdaptationMappingIds.Add($id)) { throw "Source registry adaptation mapping ID '$id' is duplicated." }
    $targetWorkId = Get-RequiredSourceString $mapping "target_work_id" $context
    if (-not $works.Contains($targetWorkId)) { throw "Source registry '$context.target_work_id' references an unknown work." }
    $targetSegmentIds = @(Get-SourceStringListAllowEmpty $mapping "target_segment_ids" $context)
    foreach ($segmentId in $targetSegmentIds) {
      if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $targetWorkId) { throw "Source registry '$context.target_segment_ids' references segment '$segmentId' outside target work '$targetWorkId'." }
    }
    $rawBasisInputs=@(Get-ProjectMapValue $mapping "basis_inputs")
    if ($rawBasisInputs.Count -eq 0) { throw "Source registry '$context.basis_inputs' must be a non-empty list." }
    $basisInputs=@(); $seenBasisWorks=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($basis in $rawBasisInputs) {
      $workId=Get-RequiredSourceString $basis "work_id" "$context.basis_inputs"
      if (-not $works.Contains($workId)) { throw "Source registry '$context.basis_inputs.work_id' references unknown work '$workId'." }
      if ($workId -eq $targetWorkId -or -not $seenBasisWorks.Add($workId)) { throw "Source registry '$context.basis_inputs' repeats a work or uses the target as its own basis." }
      $segmentIds=@(Get-SourceStringListAllowEmpty $basis "segment_ids" "$context.basis_inputs")
      foreach ($segmentId in $segmentIds) {
        if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $workId) { throw "Source registry '$context.basis_inputs.segment_ids' references segment '$segmentId' outside work '$workId'." }
      }
      $basisInputs += [pscustomobject]@{ work_id=$workId; segment_ids=@($segmentIds); basis_role=Get-RequiredSourceString $basis "basis_role" "$context.basis_inputs" }
    }
    $mappingType = Get-RequiredSourceString $mapping "mapping_type" $context
    $status = Get-RequiredSourceString $mapping "status" $context
    if ($allowedMembershipStatuses -notcontains $status) { throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')." }
    $adaptationMappings += [pscustomobject]@{
      id=$id; basis_inputs=@($basisInputs); target_work_id=$targetWorkId
      target_segment_ids=@($targetSegmentIds); mapping_type=$mappingType; status=$status
    }
  }
  if ($adaptationMappings.Count -gt 0) {
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.adaptation-mapping-type" @($adaptationMappings | ForEach-Object { $_.mapping_type }) "adaptation_mappings.*.mapping_type"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.adaptation-basis-role" @($adaptationMappings | ForEach-Object { $_.basis_inputs | ForEach-Object { $_.basis_role } }) "adaptation_mappings.*.basis_inputs.*.basis_role"
  }

  $rawTerritories = Get-ProjectMapValue $registry "territories"
  if ($null -eq $rawTerritories -or -not ($rawTerritories -is [System.Collections.IDictionary])) { throw "Source registry 'territories' must be a mapping." }
  $territories = [ordered]@{}
  foreach ($territoryId in $rawTerritories.Keys) {
    $context = "territories.$territoryId"; Test-StableSourceId $territoryId $context; $territory = $rawTerritories[$territoryId]
    $lifecycle=Get-RequiredSourceString $territory "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $codes=[ordered]@{}; $rawCodes=Get-ProjectMapValue $territory "codes"
    if ($null -eq $rawCodes -or -not ($rawCodes -is [System.Collections.IDictionary])) { throw "Source registry '$context.codes' must be a mapping." }
    foreach ($schemeId in $rawCodes.Keys) {
      Test-StableSourceId $schemeId "$context.codes"
      if ($rawCodes[$schemeId] -isnot [string] -or [string]::IsNullOrWhiteSpace([string]$rawCodes[$schemeId])) { throw "Source registry '$context.codes.$schemeId' must be a non-empty string." }
      $codes[$schemeId]=([string]$rawCodes[$schemeId]).Trim()
    }
    $territories[$territoryId] = [pscustomobject]@{
      id=$territoryId; lifecycle=$lifecycle; label=Get-RequiredSourceString $territory "label" $context
      territory_type=Get-RequiredSourceString $territory "territory_type" $context
      parent_territory_id=Get-OptionalSourceString $territory "parent_territory_id" $context
      codes=$codes
    }
  }
  if ($territories.Count -gt 0) { Assert-SourceSchemaPackValues $SchemaPackRegistry "source.territory-type" @($territories.Values | ForEach-Object { $_.territory_type }) "territories.*.territory_type" }
  foreach ($territory in $territories.Values) {
    if ($null -eq $territory.parent_territory_id) { continue }
    if (-not $territories.Contains($territory.parent_territory_id)) { throw "Source registry territory '$($territory.id)' references unknown parent '$($territory.parent_territory_id)'." }
    if ($territory.parent_territory_id -eq $territory.id) { throw "Source registry territory '$($territory.id)' cannot parent itself." }
  }
  foreach ($territoryId in $territories.Keys) {
    $seenTerritories=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal); $currentTerritoryId=$territoryId
    while ($null -ne $currentTerritoryId) {
      if (-not $seenTerritories.Add($currentTerritoryId)) { throw "Source registry contains a territory cycle involving '$currentTerritoryId'." }
      $currentTerritoryId=$territories[$currentTerritoryId].parent_territory_id
    }
  }
  $seenTerritoryCodes=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($territory in $territories.Values) { foreach ($schemeId in $territory.codes.Keys) { if (-not $seenTerritoryCodes.Add("$schemeId|$($territory.codes[$schemeId])")) { throw "Source registry repeats territory code '${schemeId}:$($territory.codes[$schemeId])'." } } }
  foreach ($owner in @($works.Values)+@($segments.Values)+@($contentGroups.Values)) {
    foreach ($localizedTitle in $owner.localized_titles) { foreach ($territoryId in $localizedTitle.territory_ids) { if (-not $territories.Contains($territoryId)) { throw "Source registry localized title references unknown territory '$territoryId'." } } }
  }

  $rawPlatforms = Get-ProjectMapValue $registry "platforms"
  if ($null -eq $rawPlatforms -or -not ($rawPlatforms -is [System.Collections.IDictionary])) { throw "Source registry 'platforms' must be a mapping." }
  $platforms = [ordered]@{}
  $platformAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($platformId in $rawPlatforms.Keys) {
    $context = "platforms.$platformId"; Test-StableSourceId $platformId $context; $platform = $rawPlatforms[$platformId]
    $aliases = @(Get-SourceStringListAllowEmpty $platform "aliases" $context)
    foreach ($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"
      if ($rawPlatforms.Contains($alias) -or -not $platformAliasKeys.Add($alias)) { throw "Source registry platform alias '$alias' is duplicated or collides with a platform ID." }
    }
    $platforms[$platformId] = [pscustomobject]@{
      id=$platformId; lifecycle=Get-RequiredSourceString $platform "lifecycle" $context
      label=Get-RequiredSourceString $platform "label" $context
      platform_type=Get-RequiredSourceString $platform "platform_type" $context
      aliases=@($aliases)
    }
    if ($script:AllowedSourceLifecycles -notcontains $platforms[$platformId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }
  if ($platforms.Count -gt 0) { Assert-SourceSchemaPackValues $SchemaPackRegistry "source.platform-type" @($platforms.Values | ForEach-Object { $_.platform_type }) "platforms.*.platform_type" }

  $manifestationRelationshipTypes = ConvertTo-RelationshipTypeRegistry (Get-ProjectMapValue $registry "manifestation_relationship_types") "manifestation_relationship_types"
  if ($manifestationRelationshipTypes.Count -gt 0) { Assert-SourceSchemaPackValues $SchemaPackRegistry "source.manifestation-relationship-type" @($manifestationRelationshipTypes.Keys) "manifestation_relationship_types" }

  $rawManifestations = Get-ProjectMapValue $registry "manifestations"
  if ($null -eq $rawManifestations -or -not ($rawManifestations -is [System.Collections.IDictionary])) { throw "Source registry 'manifestations' must be a mapping." }
  $manifestations = [ordered]@{}
  $manifestationAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($manifestationId in $rawManifestations.Keys) {
    $context = "manifestations.$manifestationId"; Test-StableSourceId $manifestationId $context; $manifestation = $rawManifestations[$manifestationId]
    $workId = Get-RequiredSourceString $manifestation "work_id" $context
    if (-not $works.Contains($workId)) { throw "Source registry '$context.work_id' references unknown work '$workId'." }
    $manifestationSegmentIds=@(Get-SourceStringListAllowEmpty $manifestation "segment_ids" $context)
    foreach ($segmentId in $manifestationSegmentIds) { if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $workId) { throw "Source registry '$context.segment_ids' references segment '$segmentId' outside work '$workId'." } }
    $containerFormatIds = @(Get-SourceStringListAllowEmpty $manifestation "container_format_ids" $context)
    foreach ($formatId in $containerFormatIds) { if (-not $containerFormats.Contains($formatId)) { throw "Source registry '$context.container_format_ids' references unknown format '$formatId'." } }
    $localizedTitles=@(ConvertTo-SourceLocalizedTitles $manifestation $context $SchemaPackRegistry)
    foreach($localizedTitle in $localizedTitles){foreach($territoryId in $localizedTitle.territory_ids){if(-not $territories.Contains($territoryId)){throw "Source registry '$context.localized_titles' references unknown territory '$territoryId'."}}}
    $aliases = @(Get-SourceStringListAllowEmpty $manifestation "aliases" $context)
    foreach ($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"
      if ($rawManifestations.Contains($alias) -or -not $manifestationAliasKeys.Add($alias)) { throw "Source registry manifestation alias '$alias' is duplicated or collides with a manifestation ID." }
    }
    $languageTags = @(Get-SourceStringListAllowEmpty $manifestation "language_tags" $context)
    foreach ($languageTag in $languageTags) { Test-SourceLanguageTag $languageTag "$context.language_tags" }
    $territoryIds = @(Get-SourceStringListAllowEmpty $manifestation "territory_ids" $context)
    foreach ($territoryId in $territoryIds) { if (-not $territories.Contains($territoryId)) { throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'." } }
    $manifestations[$manifestationId] = [pscustomobject]@{
      id=$manifestationId; lifecycle=Get-RequiredSourceString $manifestation "lifecycle" $context
      label=Get-RequiredSourceString $manifestation "label" $context; work_id=$workId
      segment_ids=@($manifestationSegmentIds)
      manifestation_type=Get-RequiredSourceString $manifestation "manifestation_type" $context
      language_tags=@($languageTags)
      territory_ids=@($territoryIds)
      container_format_ids=@($containerFormatIds); localized_titles=@($localizedTitles); aliases=@($aliases)
    }
    if ($script:AllowedSourceLifecycles -notcontains $manifestations[$manifestationId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }
  if ($manifestations.Count -gt 0) { Assert-SourceSchemaPackValues $SchemaPackRegistry "source.manifestation-type" @($manifestations.Values | ForEach-Object { $_.manifestation_type }) "manifestations.*.manifestation_type" }

  $manifestationRelationships = @()
  $seenManifestationRelationshipIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach ($relationship in @(Get-ProjectMapValue $registry "manifestation_relationships")) {
    $context = "manifestation_relationships"; $id = Get-RequiredSourceString $relationship "id" $context; Test-StableSourceId $id "$context.id"
    if (-not $seenManifestationRelationshipIds.Add($id)) { throw "Source registry manifestation relationship ID '$id' is duplicated." }
    $sourceId=Get-RequiredSourceString $relationship "source_manifestation_id" $context; $targetId=Get-RequiredSourceString $relationship "target_manifestation_id" $context
    $type=Get-RequiredSourceString $relationship "relationship_type" $context; $status=Get-RequiredSourceString $relationship "status" $context
    if (-not $manifestations.Contains($sourceId) -or -not $manifestations.Contains($targetId)) { throw "Source registry '$context' references an unknown manifestation." }
    if ($sourceId -eq $targetId) { throw "Source registry '$context' cannot relate a manifestation to itself." }
    if (-not $manifestationRelationshipTypes.Contains($type)) { throw "Source registry '$context.relationship_type' references unknown type '$type'." }
    if ($allowedMembershipStatuses -notcontains $status) { throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')." }
    $manifestationRelationships += [pscustomobject]@{ id=$id; source_manifestation_id=$sourceId; relationship_type=$type; target_manifestation_id=$targetId; status=$status }
  }

  $relatedManifestationPairs=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach($relationship in $manifestationRelationships){[void]$relatedManifestationPairs.Add((@($relationship.source_manifestation_id,$relationship.target_manifestation_id)|Sort-Object)-join "|")}
  $manifestationSegmentMappings=@();$seenManifestationMappingIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $rawManifestationSegmentMappings=@(Get-ProjectMapValue $registry "manifestation_segment_mappings")
  for($index=0;$index -lt $rawManifestationSegmentMappings.Count;$index++){
    $context="manifestation_segment_mappings[$index]";$mapping=$rawManifestationSegmentMappings[$index]
    $id=Get-RequiredSourceString $mapping "id" $context;Test-StableSourceId $id "$context.id";if(-not $seenManifestationMappingIds.Add($id)){throw "Source registry manifestation segment mapping ID '$id' is duplicated."}
    $sourceId=Get-RequiredSourceString $mapping "source_manifestation_id" $context;$targetId=Get-RequiredSourceString $mapping "target_manifestation_id" $context
    if(-not $manifestations.Contains($sourceId) -or -not $manifestations.Contains($targetId)){throw "Source registry '$context' references an unknown manifestation."}
    if($sourceId -eq $targetId){throw "Source registry '$context' cannot map a manifestation to itself."}
    if($manifestations[$sourceId].work_id -ne $manifestations[$targetId].work_id){throw "Source registry '$context' must map manifestations of the same work."}
    if(-not $relatedManifestationPairs.Contains((@($sourceId,$targetId)|Sort-Object)-join "|")){throw "Source registry '$context' requires a manifestation relationship between its source and target."}
    $sourceSegmentIds=@(Get-SourceStringListAllowEmpty $mapping "source_segment_ids" $context);$targetSegmentIds=@(Get-SourceStringListAllowEmpty $mapping "target_segment_ids" $context)
    foreach($scope in @([pscustomobject]@{name="source_segment_ids";ids=$sourceSegmentIds;manifestation_id=$sourceId},[pscustomobject]@{name="target_segment_ids";ids=$targetSegmentIds;manifestation_id=$targetId})){
      foreach($segmentId in $scope.ids){if(-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $manifestations[$scope.manifestation_id].work_id -or ($manifestations[$scope.manifestation_id].segment_ids.Count -gt 0 -and $manifestations[$scope.manifestation_id].segment_ids -notcontains $segmentId)){throw "Source registry '$context.$($scope.name)' references segment '$segmentId' outside manifestation scope."}}
    }
    $mappingType=Get-RequiredSourceString $mapping "mapping_type" $context
    $validShape=if($mappingType -eq "omitted"){$sourceSegmentIds.Count -gt 0 -and $targetSegmentIds.Count -eq 0}elseif($mappingType -eq "added"){$sourceSegmentIds.Count -eq 0 -and $targetSegmentIds.Count -gt 0}else{$sourceSegmentIds.Count -gt 0 -and $targetSegmentIds.Count -gt 0}
    if(-not $validShape){throw "Source registry '$context' has segment lists incompatible with mapping type '$mappingType'."}
    $status=Get-RequiredSourceString $mapping "status" $context;if($allowedMembershipStatuses -notcontains $status){throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')." }
    $manifestationSegmentMappings += [pscustomobject]@{id=$id;source_manifestation_id=$sourceId;source_segment_ids=@($sourceSegmentIds);target_manifestation_id=$targetId;target_segment_ids=@($targetSegmentIds);mapping_type=$mappingType;status=$status}
  }
  if($manifestationSegmentMappings.Count -gt 0){Assert-SourceSchemaPackValues $SchemaPackRegistry "source.manifestation-segment-mapping-type" @($manifestationSegmentMappings|ForEach-Object {$_.mapping_type}) "manifestation_segment_mappings.*.mapping_type"}

  $rawReleaseComponents = Get-ProjectMapValue $registry "release_components"
  if ($null -eq $rawReleaseComponents -or -not ($rawReleaseComponents -is [System.Collections.IDictionary])) { throw "Source registry 'release_components' must be a mapping." }
  $releaseComponents = [ordered]@{}
  foreach ($componentId in $rawReleaseComponents.Keys) {
    $context="release_components.$componentId"; Test-StableSourceId $componentId $context; $component=$rawReleaseComponents[$componentId]
    $manifestationId=Get-OptionalSourceString $component "manifestation_id" $context
    if ($null -ne $manifestationId -and -not $manifestations.Contains($manifestationId)) { throw "Source registry '$context.manifestation_id' references unknown manifestation '$manifestationId'." }
    $segmentIds=@(Get-SourceStringListAllowEmpty $component "segment_ids" $context)
    foreach ($segmentId in $segmentIds) {
      if (-not $segments.Contains($segmentId)) { throw "Source registry '$context.segment_ids' references unknown segment '$segmentId'." }
      if ($null -ne $manifestationId -and ($segments[$segmentId].work_id -ne $manifestations[$manifestationId].work_id -or ($manifestations[$manifestationId].segment_ids.Count -gt 0 -and $manifestations[$manifestationId].segment_ids -notcontains $segmentId))) { throw "Source registry '$context.segment_ids' references segment '$segmentId' outside manifestation scope." }
    }
    $languageTag=Get-OptionalSourceString $component "language_tag" $context
    if ($null -ne $languageTag) { Test-SourceLanguageTag $languageTag "$context.language_tag" }
    $releaseComponents[$componentId]=[pscustomobject]@{
      id=$componentId; lifecycle=Get-RequiredSourceString $component "lifecycle" $context
      label=Get-RequiredSourceString $component "label" $context; manifestation_id=$manifestationId
      component_type=Get-RequiredSourceString $component "component_type" $context
      segment_ids=@($segmentIds); language_tag=$languageTag
    }
    if ($script:AllowedSourceLifecycles -notcontains $releaseComponents[$componentId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }
  if ($releaseComponents.Count -gt 0) { Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-component-type" @($releaseComponents.Values | ForEach-Object { $_.component_type }) "release_components.*.component_type" }

  $releaseComponentRelationshipTypes=ConvertTo-RelationshipTypeRegistry (Get-ProjectMapValue $registry "release_component_relationship_types") "release_component_relationship_types"
  if($releaseComponentRelationshipTypes.Count -gt 0){Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-component-relationship-type" @($releaseComponentRelationshipTypes.Keys) "release_component_relationship_types"}
  $releaseComponentRelationships=@();$seenComponentRelationshipIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $rawComponentRelationships=@(Get-ProjectMapValue $registry "release_component_relationships")
  for($index=0;$index -lt $rawComponentRelationships.Count;$index++){
    $context="release_component_relationships[$index]";$relationship=$rawComponentRelationships[$index]
    $id=Get-RequiredSourceString $relationship "id" $context;Test-StableSourceId $id "$context.id"
    if(-not $seenComponentRelationshipIds.Add($id)){throw "Source registry release-component relationship ID '$id' is duplicated."}
    $sourceComponentId=Get-RequiredSourceString $relationship "source_component_id" $context
    $targetComponentId=Get-RequiredSourceString $relationship "target_component_id" $context
    if(-not $releaseComponents.Contains($sourceComponentId) -or -not $releaseComponents.Contains($targetComponentId)){throw "Source registry '$context' references an unknown release component."}
    if($sourceComponentId -eq $targetComponentId){throw "Source registry '$context' cannot relate a component to itself."}
    $relationshipType=Get-RequiredSourceString $relationship "relationship_type" $context
    if(-not $releaseComponentRelationshipTypes.Contains($relationshipType)){throw "Source registry '$context.relationship_type' references unknown type '$relationshipType'."}
    $releaseComponentRelationships += [pscustomobject]@{id=$id;source_component_id=$sourceComponentId;relationship_type=$relationshipType;target_component_id=$targetComponentId}
  }

  $rawReleasePackages = Get-ProjectMapValue $registry "release_packages"
  if ($null -eq $rawReleasePackages -or -not ($rawReleasePackages -is [System.Collections.IDictionary])) { throw "Source registry 'release_packages' must be a mapping." }
  $releasePackages = [ordered]@{}
  $releasePackageAliasKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($packageId in $rawReleasePackages.Keys) {
    $context="release_packages.$packageId"; Test-StableSourceId $packageId $context; $package=$rawReleasePackages[$packageId]
    $manifestationIds=@(Get-SourceStringListAllowEmpty $package "manifestation_ids" $context)
    $segmentIds=@(Get-SourceStringListAllowEmpty $package "segment_ids" $context)
    $componentIds=@(Get-SourceStringListAllowEmpty $package "release_component_ids" $context)
    $containerFormatIds=@(Get-SourceStringListAllowEmpty $package "container_format_ids" $context)
    if ($manifestationIds.Count -eq 0 -and $segmentIds.Count -eq 0 -and $componentIds.Count -eq 0) { throw "Source registry '$context' must identify at least one manifestation, segment, or release component." }
    foreach ($manifestationId in $manifestationIds) { if (-not $manifestations.Contains($manifestationId)) { throw "Source registry '$context.manifestation_ids' references unknown manifestation '$manifestationId'." } }
    $packageWorkIds=@($manifestationIds | ForEach-Object { $manifestations[$_].work_id } | Sort-Object -Unique)
    foreach ($segmentId in $segmentIds) {
      if (-not $segments.Contains($segmentId)) { throw "Source registry '$context.segment_ids' references unknown segment '$segmentId'." }
      if ($packageWorkIds.Count -gt 0 -and $packageWorkIds -notcontains $segments[$segmentId].work_id) { throw "Source registry '$context.segment_ids' references segment '$segmentId' outside the package manifestations." }
    }
    foreach ($componentId in $componentIds) {
      if (-not $releaseComponents.Contains($componentId)) { throw "Source registry '$context.release_component_ids' references unknown component '$componentId'." }
      if ($manifestationIds.Count -gt 0 -and $null -ne $releaseComponents[$componentId].manifestation_id -and $manifestationIds -notcontains $releaseComponents[$componentId].manifestation_id) { throw "Source registry '$context.release_component_ids' references component '$componentId' outside the package manifestations." }
    }
    $effectiveManifestationIds=@($manifestationIds + @($componentIds | ForEach-Object { $releaseComponents[$_].manifestation_id } | Where-Object {$null -ne $_}) | Sort-Object -Unique)
    $packageWorkIds=@($effectiveManifestationIds | ForEach-Object { $manifestations[$_].work_id } | Sort-Object -Unique)
    foreach ($segmentId in $segmentIds) {
      if ($packageWorkIds.Count -gt 0 -and $packageWorkIds -notcontains $segments[$segmentId].work_id) { throw "Source registry '$context.segment_ids' references segment '$segmentId' outside the package manifestations." }
    }
    foreach ($containerFormatId in $containerFormatIds) { if (-not $containerFormats.Contains($containerFormatId)) { throw "Source registry '$context.container_format_ids' references unknown container format '$containerFormatId'." } }
    $aliases=@(Get-SourceStringListAllowEmpty $package "aliases" $context)
    foreach ($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"
      if ($rawReleasePackages.Contains($alias) -or -not $releasePackageAliasKeys.Add($alias)) { throw "Source registry release-package alias '$alias' is duplicated or collides with a package ID." }
    }
    $localizedTitles=@(ConvertTo-SourceLocalizedTitles $package $context $SchemaPackRegistry)
    foreach ($localizedTitle in $localizedTitles) {
      foreach ($territoryId in $localizedTitle.territory_ids) { if (-not $territories.Contains($territoryId)) { throw "Source registry '$context.localized_titles' references unknown territory '$territoryId'." } }
    }
    $releasePackages[$packageId]=[pscustomobject]@{
      id=$packageId; lifecycle=Get-RequiredSourceString $package "lifecycle" $context
      label=Get-RequiredSourceString $package "label" $context
      package_type=Get-RequiredSourceString $package "package_type" $context
      manifestation_ids=@($manifestationIds); segment_ids=@($segmentIds)
      release_component_ids=@($componentIds); container_format_ids=@($containerFormatIds)
      localized_titles=@($localizedTitles)
      aliases=@($aliases)
    }
    if ($script:AllowedSourceLifecycles -notcontains $releasePackages[$packageId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }
  if ($releasePackages.Count -gt 0) { Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-package-type" @($releasePackages.Values | ForEach-Object { $_.package_type }) "release_packages.*.package_type" }

  $packagesByComponent=@{};foreach($componentId in $releaseComponents.Keys){$packagesByComponent[$componentId]=@()}
  foreach($package in $releasePackages.Values){foreach($componentId in $package.release_component_ids){$packagesByComponent[$componentId]=@($packagesByComponent[$componentId]+$package.id)}}
  foreach($component in $releaseComponents.Values){
    if($null -eq $component.manifestation_id -and $packagesByComponent[$component.id].Count -eq 0){throw "Source registry release component '$($component.id)' has no manifestation and is not included in a release package."}
    foreach($packageId in $packagesByComponent[$component.id]){
      $package=$releasePackages[$packageId]
      $packageWorkIds=@($package.manifestation_ids|ForEach-Object {$manifestations[$_].work_id})
      $packageWorkIds+=@($package.segment_ids|ForEach-Object {$segments[$_].work_id})
      if($null -ne $component.manifestation_id){$packageWorkIds+=@($manifestations[$component.manifestation_id].work_id)}
      $packageWorkIds=@($packageWorkIds|Sort-Object -Unique)
      $componentWorkIds=@($component.segment_ids|ForEach-Object {$segments[$_].work_id}|Sort-Object -Unique)
      if($packageWorkIds.Count -gt 0 -and @($componentWorkIds|Where-Object {$packageWorkIds -notcontains $_}).Count -gt 0){throw "Source registry release component '$($component.id)' has segment scope outside package '$packageId'."}
    }
  }
  $getReleasePackageWorkIds={
    param([string]$PackageId)
    $package=$releasePackages[$PackageId];$workIds=@($package.manifestation_ids|ForEach-Object {$manifestations[$_].work_id});$workIds+=@($package.segment_ids|ForEach-Object {$segments[$_].work_id})
    foreach($componentId in $package.release_component_ids){$component=$releaseComponents[$componentId];if($null -ne $component.manifestation_id){$workIds+=@($manifestations[$component.manifestation_id].work_id)};$workIds+=@($component.segment_ids|ForEach-Object {$segments[$_].work_id})}
    return @($workIds|Sort-Object -Unique)
  }

  $validateDistributionScope = {
    param([string]$SubjectType,[string]$SubjectId,[object[]]$SegmentIds,[string]$Context)
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.distribution-subject-type" @($SubjectType) "$Context.subject_type"
    if ($SubjectType -eq "manifestation") {
      if (-not $manifestations.Contains($SubjectId)) { throw "Source registry '$Context.subject_id' references unknown manifestation '$SubjectId'." }
      foreach ($segmentId in $SegmentIds) {
        if (-not $segments.Contains($segmentId) -or $segments[$segmentId].work_id -ne $manifestations[$SubjectId].work_id) { throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside manifestation work." }
        if ($manifestations[$SubjectId].segment_ids.Count -gt 0 -and $manifestations[$SubjectId].segment_ids -notcontains $segmentId) { throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside manifestation scope." }
      }
      return
    }
    if ($SubjectType -eq "release-package") {
      if (-not $releasePackages.Contains($SubjectId)) { throw "Source registry '$Context.subject_id' references unknown release package '$SubjectId'." }
      foreach ($segmentId in $SegmentIds) {
        if (-not $segments.Contains($segmentId)) { throw "Source registry '$Context.segment_ids' references unknown segment '$segmentId'." }
        if ($releasePackages[$SubjectId].segment_ids.Count -gt 0 -and $releasePackages[$SubjectId].segment_ids -notcontains $segmentId) { throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside release-package scope." }
        if ($releasePackages[$SubjectId].segment_ids.Count -eq 0) {
          $packageWorkIds=@(& $getReleasePackageWorkIds $SubjectId)
          if ($packageWorkIds.Count -gt 0 -and $packageWorkIds -notcontains $segments[$segmentId].work_id) { throw "Source registry '$Context.segment_ids' references segment '$segmentId' outside release-package manifestations." }
        }
      }
      return
    }
    throw "Source registry '$Context.subject_type' has unsupported value '$SubjectType'."
  }

  $rawReleaseRuns=Get-ProjectMapValue $registry "release_runs"
  if($null -eq $rawReleaseRuns -or -not ($rawReleaseRuns -is [System.Collections.IDictionary])){throw "Source registry 'release_runs' must be a mapping."}
  $releaseRuns=[ordered]@{}
  foreach($runId in $rawReleaseRuns.Keys){
    $context="release_runs.$runId";Test-StableSourceId $runId $context;$run=$rawReleaseRuns[$runId]
    $subjectType=Get-RequiredSourceString $run "subject_type" $context;$subjectId=Get-RequiredSourceString $run "subject_id" $context;$segmentIds=@(Get-SourceStringList $run "segment_ids" $context)
    if($segmentIds.Count -eq 0 -or @($segmentIds|Sort-Object -Unique).Count -ne $segmentIds.Count){throw "Source registry '$context.segment_ids' must be a non-empty duplicate-free list."}
    & $validateDistributionScope $subjectType $subjectId $segmentIds $context
    $orderingSchemeId=Get-RequiredSourceString $run "ordering_scheme_id" $context
    if(-not $orderingSchemes.Contains($orderingSchemeId)){throw "Source registry '$context.ordering_scheme_id' references unknown ordering scheme '$orderingSchemeId'."}
    $ordering=$orderingSchemes[$orderingSchemeId];$orderedEntries=@($ordering.entries);$orderedSegmentIds=@($orderedEntries|Where-Object {$_.target_type -eq "segment"}|ForEach-Object {$_.target_id}|Sort-Object -Unique)
    if($ordering.ordering_mode -ne "total" -or $orderedSegmentIds.Count -ne $orderedEntries.Count -or (Compare-Object @($segmentIds|Sort-Object) @($orderedSegmentIds|Sort-Object))){throw "Source registry '$context.ordering_scheme_id' must be a total ordering of exactly the run's segments."}
    $rawPhases=@(Get-ProjectMapValue $run "phases")
    if($rawPhases.Count -eq 0){throw "Source registry '$context.phases' must be a non-empty list."}
    $phases=@();$seenPhaseIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal);$flattenedPhaseSegments=@()
    for($phaseIndex=0;$phaseIndex -lt $rawPhases.Count;$phaseIndex++){
      $phaseContext="$context.phases[$phaseIndex]";$phase=$rawPhases[$phaseIndex]
      $phaseId=Get-RequiredSourceString $phase "id" $phaseContext;Test-StableSourceId $phaseId "$phaseContext.id"
      if(-not $seenPhaseIds.Add($phaseId)){throw "Source registry '$context.phases' repeats phase ID '$phaseId'."}
      $phaseSegmentIds=@(Get-SourceStringList $phase "segment_ids" $phaseContext)
      if($phaseSegmentIds.Count -eq 0){throw "Source registry '$phaseContext.segment_ids' must not be empty."}
      $flattenedPhaseSegments+=@($phaseSegmentIds)
      $firstReleaseWindow=ConvertTo-SourceTemporalWindow $phase "first_release_window" $phaseContext $SchemaPackRegistry
      if($null -eq $firstReleaseWindow){throw "Source registry '$phaseContext.first_release_window' is required."}
      $cadence=Get-ProjectMapValue $phase "cadence";if($null -eq $cadence -or -not ($cadence -is [System.Collections.IDictionary])){throw "Source registry '$phaseContext.cadence' must be a mapping."}
      $cadenceUnit=Get-RequiredSourceString $cadence "unit" "$phaseContext.cadence";$cadenceInterval=Get-ProjectMapValue $cadence "interval"
      if($cadenceInterval -is [bool] -or $cadenceInterval -isnot [int] -or [int]$cadenceInterval -lt 1){throw "Source registry '$phaseContext.cadence.interval' must be a positive integer."}
      Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-run-cadence-unit" @($cadenceUnit) "$phaseContext.cadence.unit"
      $batchSize=Get-ProjectMapValue $phase "batch_size"
      if($batchSize -is [bool] -or $batchSize -isnot [int] -or [int]$batchSize -lt 1 -or [int]$batchSize -gt $phaseSegmentIds.Count){throw "Source registry '$phaseContext.batch_size' must be between 1 and the number of phase segments."}
      $phases += [pscustomobject]@{id=$phaseId;segment_ids=@($phaseSegmentIds);first_release_window=$firstReleaseWindow;cadence_unit=$cadenceUnit;cadence_interval=[int]$cadenceInterval;batch_size=[int]$batchSize}
    }
    $orderedRunSegments=@($orderedEntries|ForEach-Object {$_.target_id})
    if((Compare-Object @($flattenedPhaseSegments) @($orderedRunSegments) -SyncWindow 0)){throw "Source registry '$context.phases' must partition the run's segments exactly in ordering-scheme order."}
    $territoryIds=@(Get-SourceStringListAllowEmpty $run "territory_ids" $context);foreach($territoryId in $territoryIds){if(-not $territories.Contains($territoryId)){throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'."}}
    $platformIds=@(Get-SourceStringListAllowEmpty $run "platform_ids" $context);foreach($platformId in $platformIds){if(-not $platforms.Contains($platformId)){throw "Source registry '$context.platform_ids' references unknown platform '$platformId'."}}
    $rawExceptions=@(Get-ProjectMapValue $run "exceptions");$exceptions=@();$seenExceptions=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for($index=0;$index -lt $rawExceptions.Count;$index++){
      $exceptionContext="$context.exceptions[$index]";$exception=$rawExceptions[$index];$exceptionType=Get-RequiredSourceString $exception "exception_type" $exceptionContext;Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-run-exception-type" @($exceptionType) "$exceptionContext.exception_type"
      $segmentId=Get-RequiredSourceString $exception "segment_id" $exceptionContext;if($segmentIds -notcontains $segmentId){throw "Source registry '$exceptionContext.segment_id' falls outside the release run."};if(-not $seenExceptions.Add("$exceptionType|$segmentId")){throw "Source registry '$context.exceptions' repeats an exception."}
      $releaseWindow=ConvertTo-SourceTemporalWindow $exception "release_window" $exceptionContext $SchemaPackRegistry;$intervalCount=Get-ProjectMapValue $exception "interval_count"
      if($null -ne $intervalCount -and ($intervalCount -is [bool] -or $intervalCount -isnot [int] -or [int]$intervalCount -lt 1)){throw "Source registry '$exceptionContext.interval_count' must be a positive integer when present."}
      $validShape=if($exceptionType -eq "rescheduled"){$null -ne $releaseWindow -and $null -eq $intervalCount}elseif($exceptionType -eq "pause"){$null -eq $releaseWindow -and $null -ne $intervalCount}else{$null -eq $releaseWindow -and $null -eq $intervalCount}
      if(-not $validShape){throw "Source registry '$exceptionContext' fields are incompatible with exception type '$exceptionType'."}
      $exceptions += [pscustomobject]@{exception_type=$exceptionType;segment_id=$segmentId;release_window=$releaseWindow;interval_count=if($null -eq $intervalCount){$null}else{[int]$intervalCount}}
    }
    $lifecycle=Get-RequiredSourceString $run "lifecycle" $context;if($script:AllowedSourceLifecycles -notcontains $lifecycle){throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $releaseRuns[$runId]=[pscustomobject]@{id=$runId;lifecycle=$lifecycle;label=Get-RequiredSourceString $run "label" $context;subject_type=$subjectType;subject_id=$subjectId;segment_ids=@($segmentIds);ordering_scheme_id=$orderingSchemeId;release_event_type=Get-RequiredSourceString $run "release_event_type" $context;phases=@($phases);territory_ids=@($territoryIds);platform_ids=@($platformIds);availability_status=Get-RequiredSourceString $run "availability_status" $context;exceptions=@($exceptions)}
  }
  if($releaseRuns.Count -gt 0){Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-event-type" @($releaseRuns.Values|ForEach-Object {$_.release_event_type}) "release_runs.*.release_event_type";Assert-SourceSchemaPackValues $SchemaPackRegistry "source.availability-status" @($releaseRuns.Values|ForEach-Object {$_.availability_status}) "release_runs.*.availability_status"}

  $rawReleaseEvents = Get-ProjectMapValue $registry "release_events"
  if ($null -eq $rawReleaseEvents -or -not ($rawReleaseEvents -is [System.Collections.IDictionary])) { throw "Source registry 'release_events' must be a mapping." }
  $releaseEvents=[ordered]@{}
  foreach ($eventId in $rawReleaseEvents.Keys) {
    $context="release_events.$eventId"; Test-StableSourceId $eventId $context; $event=$rawReleaseEvents[$eventId]
    $subjectType=Get-RequiredSourceString $event "subject_type" $context
    $subjectId=Get-RequiredSourceString $event "subject_id" $context
    $segmentIds=@(Get-SourceStringListAllowEmpty $event "segment_ids" $context)
    & $validateDistributionScope $subjectType $subjectId $segmentIds $context
    $platformIds=@(Get-SourceStringListAllowEmpty $event "platform_ids" $context)
    foreach ($platformId in $platformIds) { if (-not $platforms.Contains($platformId)) { throw "Source registry '$context.platform_ids' references unknown platform '$platformId'." } }
    $territoryIds=@(Get-SourceStringListAllowEmpty $event "territory_ids" $context)
    foreach ($territoryId in $territoryIds) { if (-not $territories.Contains($territoryId)) { throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'." } }
    $releaseRunId=Get-OptionalSourceString $event "release_run_id" $context
    if($null -ne $releaseRunId){
      if(-not $releaseRuns.Contains($releaseRunId)){throw "Source registry '$context.release_run_id' references unknown release run '$releaseRunId'."}
      $releaseRun=$releaseRuns[$releaseRunId]
      if($releaseRun.subject_type -ne $subjectType -or $releaseRun.subject_id -ne $subjectId -or @($segmentIds|Where-Object {$releaseRun.segment_ids -notcontains $_}).Count -gt 0 -or ($releaseRun.platform_ids.Count -gt 0 -and @($platformIds|Where-Object {$releaseRun.platform_ids -notcontains $_}).Count -gt 0) -or ($releaseRun.territory_ids.Count -gt 0 -and @($territoryIds|Where-Object {$releaseRun.territory_ids -notcontains $_}).Count -gt 0)){throw "Source registry '$context' falls outside its release run."}
    }
    $releaseEvents[$eventId]=[pscustomobject]@{
      id=$eventId; lifecycle=Get-RequiredSourceString $event "lifecycle" $context; label=Get-RequiredSourceString $event "label" $context
      subject_type=$subjectType; subject_id=$subjectId; segment_ids=@($segmentIds)
      release_event_type=Get-RequiredSourceString $event "release_event_type" $context
      release_window=ConvertTo-SourceTemporalWindow (Get-ProjectMapValue $event "release_window") "$context.release_window" $SchemaPackRegistry
      territory_ids=@($territoryIds)
      platform_ids=@($platformIds); availability_status=Get-RequiredSourceString $event "availability_status" $context
      release_run_id=$releaseRunId
    }
    if ($script:AllowedSourceLifecycles -notcontains $releaseEvents[$eventId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }
  if ($releaseEvents.Count -gt 0) {
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.release-event-type" @($releaseEvents.Values | ForEach-Object { $_.release_event_type }) "release_events.*.release_event_type"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.availability-status" @($releaseEvents.Values | ForEach-Object { $_.availability_status }) "release_events.*.availability_status"
  }

  $rawCatalogPlacements = Get-ProjectMapValue $registry "catalog_placements"
  if ($null -eq $rawCatalogPlacements -or -not ($rawCatalogPlacements -is [System.Collections.IDictionary])) { throw "Source registry 'catalog_placements' must be a mapping." }
  $catalogPlacements=[ordered]@{}
  foreach ($placementId in $rawCatalogPlacements.Keys) {
    $context="catalog_placements.$placementId"; Test-StableSourceId $placementId $context; $placement=$rawCatalogPlacements[$placementId]
    $platformId=Get-RequiredSourceString $placement "platform_id" $context
    if (-not $platforms.Contains($platformId)) { throw "Source registry '$context.platform_id' references unknown platform '$platformId'." }
    $targetType=Get-RequiredSourceString $placement "target_type" $context
    $targetId=Get-RequiredSourceString $placement "target_id" $context
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.catalog-target-type" @($targetType) "$context.target_type"
    $targetExists = switch ($targetType) {
      "work" { $works.Contains($targetId) }
      "segment" { $segments.Contains($targetId) }
      "content-group" { $contentGroups.Contains($targetId) }
      "manifestation" { $manifestations.Contains($targetId) }
      "release-package" { $releasePackages.Contains($targetId) }
      default { $false }
    }
    if (-not $targetExists) { throw "Source registry '$context.target_id' references unknown $targetType '$targetId'." }
    $ordinal=Get-ProjectMapValue $placement "ordinal"
    if ($null -ne $ordinal -and ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1)) { throw "Source registry '$context.ordinal' must be a positive integer when present." }
    $localizedTitles=@(ConvertTo-SourceLocalizedTitles $placement $context $SchemaPackRegistry)
    foreach($localizedTitle in $localizedTitles){foreach($territoryId in $localizedTitle.territory_ids){if(-not $territories.Contains($territoryId)){throw "Source registry '$context.localized_titles' references unknown territory '$territoryId'."}}}
    $catalogPlacements[$placementId]=[pscustomobject]@{
      id=$placementId; lifecycle=Get-RequiredSourceString $placement "lifecycle" $context; label=Get-RequiredSourceString $placement "label" $context
      platform_id=$platformId; placement_type=Get-RequiredSourceString $placement "placement_type" $context
      parent_placement_id=Get-OptionalSourceString $placement "parent_placement_id" $context
      target_type=$targetType; target_id=$targetId; ordinal=if($null -eq $ordinal){$null}else{[int]$ordinal}
      provider_key=Get-OptionalSourceString $placement "provider_key" $context
      localized_titles=@($localizedTitles)
    }
    if ($script:AllowedSourceLifecycles -notcontains $catalogPlacements[$placementId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }
  foreach ($placement in $catalogPlacements.Values) {
    if ($null -eq $placement.parent_placement_id) { continue }
    if (-not $catalogPlacements.Contains($placement.parent_placement_id)) { throw "Source registry catalog placement '$($placement.id)' references unknown parent '$($placement.parent_placement_id)'." }
    if ($placement.parent_placement_id -eq $placement.id) { throw "Source registry catalog placement '$($placement.id)' cannot parent itself." }
    if ($catalogPlacements[$placement.parent_placement_id].platform_id -ne $placement.platform_id) { throw "Source registry catalog placement '$($placement.id)' and its parent must belong to the same platform." }
  }
  foreach ($placementId in $catalogPlacements.Keys) {
    $activePlacements=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal); $currentPlacementId=$placementId
    while ($null -ne $currentPlacementId) {
      if (-not $activePlacements.Add($currentPlacementId)) { throw "Source registry contains a catalog-placement cycle involving '$currentPlacementId'." }
      $currentPlacementId=$catalogPlacements[$currentPlacementId].parent_placement_id
    }
  }
  if ($catalogPlacements.Count -gt 0) { Assert-SourceSchemaPackValues $SchemaPackRegistry "source.catalog-placement-type" @($catalogPlacements.Values | ForEach-Object { $_.placement_type }) "catalog_placements.*.placement_type" }

  $rawPlatformOfferings=Get-ProjectMapValue $registry "platform_offerings"
  if ($null -eq $rawPlatformOfferings -or -not ($rawPlatformOfferings -is [System.Collections.IDictionary])) { throw "Source registry 'platform_offerings' must be a mapping." }
  $platformOfferings=[ordered]@{}
  foreach ($offeringId in $rawPlatformOfferings.Keys) {
    $context="platform_offerings.$offeringId"; Test-StableSourceId $offeringId $context; $offering=$rawPlatformOfferings[$offeringId]
    $platformId=Get-RequiredSourceString $offering "platform_id" $context
    $subjectType=Get-RequiredSourceString $offering "subject_type" $context
    $subjectId=Get-RequiredSourceString $offering "subject_id" $context
    $segmentIds=@(Get-SourceStringListAllowEmpty $offering "segment_ids" $context)
    if (-not $platforms.Contains($platformId)) { throw "Source registry '$context.platform_id' references unknown platform '$platformId'." }
    & $validateDistributionScope $subjectType $subjectId $segmentIds $context
    $releaseEventId=Get-OptionalSourceString $offering "release_event_id" $context
    if ($null -ne $releaseEventId -and -not $releaseEvents.Contains($releaseEventId)) { throw "Source registry '$context.release_event_id' references unknown release event '$releaseEventId'." }
    if ($null -ne $releaseEventId -and ($releaseEvents[$releaseEventId].subject_type -ne $subjectType -or $releaseEvents[$releaseEventId].subject_id -ne $subjectId -or $releaseEvents[$releaseEventId].platform_ids -notcontains $platformId)) { throw "Source registry '$context' release event does not match its subject and platform." }
    if ($null -ne $releaseEventId -and $segmentIds.Count -gt 0 -and $releaseEvents[$releaseEventId].segment_ids.Count -gt 0) {
      foreach ($segmentId in $segmentIds) { if ($releaseEvents[$releaseEventId].segment_ids -notcontains $segmentId) { throw "Source registry '$context.segment_ids' extends beyond its release-event scope." } }
    }
    $placementIds=@(Get-SourceStringListAllowEmpty $offering "catalog_placement_ids" $context)
    foreach ($placementId in $placementIds) { if (-not $catalogPlacements.Contains($placementId) -or $catalogPlacements[$placementId].platform_id -ne $platformId) { throw "Source registry '$context.catalog_placement_ids' references placement '$placementId' outside platform '$platformId'." } }
    $territoryIds=@(Get-SourceStringListAllowEmpty $offering "territory_ids" $context)
    foreach ($territoryId in $territoryIds) { if (-not $territories.Contains($territoryId)) { throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'." } }
    $languageTags=@(Get-SourceStringListAllowEmpty $offering "language_tags" $context)
    foreach ($languageTag in $languageTags) { Test-SourceLanguageTag $languageTag "$context.language_tags" }
    $platformOfferings[$offeringId]=[pscustomobject]@{
      id=$offeringId; lifecycle=Get-RequiredSourceString $offering "lifecycle" $context; label=Get-RequiredSourceString $offering "label" $context
      platform_id=$platformId; subject_type=$subjectType; subject_id=$subjectId; segment_ids=@($segmentIds); release_event_id=$releaseEventId
      offering_type=Get-RequiredSourceString $offering "offering_type" $context
      availability_status=Get-RequiredSourceString $offering "availability_status" $context
      territory_ids=@($territoryIds)
      language_tags=@($languageTags)
      availability_window=ConvertTo-SourceTemporalWindow (Get-ProjectMapValue $offering "availability_window") "$context.availability_window" $SchemaPackRegistry
      catalog_placement_ids=@($placementIds)
    }
    if ($script:AllowedSourceLifecycles -notcontains $platformOfferings[$offeringId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }
  if ($platformOfferings.Count -gt 0) {
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.platform-offering-type" @($platformOfferings.Values | ForEach-Object { $_.offering_type }) "platform_offerings.*.offering_type"
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.availability-status" @($platformOfferings.Values | ForEach-Object { $_.availability_status }) "platform_offerings.*.availability_status"
  }

  $rawIdentifierSchemes=Get-ProjectMapValue $registry "identifier_schemes"
  if ($null -eq $rawIdentifierSchemes -or -not ($rawIdentifierSchemes -is [System.Collections.IDictionary])) { throw "Source registry 'identifier_schemes' must be a mapping." }
  $identifierSchemes=[ordered]@{}
  foreach ($schemeId in $rawIdentifierSchemes.Keys) {
    $context="identifier_schemes.$schemeId"; Test-StableSourceId $schemeId $context; $scheme=$rawIdentifierSchemes[$schemeId]
    $targetTypes=@(Get-SourceStringList $scheme "target_types" $context)
    if ($targetTypes.Count -eq 0) { throw "Source registry '$context.target_types' must not be empty." }
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.identifier-target-type" $targetTypes "$context.target_types"
    $identifierSchemes[$schemeId]=[pscustomobject]@{
      id=$schemeId; lifecycle=Get-RequiredSourceString $scheme "lifecycle" $context
      label=Get-RequiredSourceString $scheme "label" $context
      target_types=@($targetTypes); case_sensitive=Get-RequiredSourceBoolean $scheme "case_sensitive" $context
    }
    if ($script:AllowedSourceLifecycles -notcontains $identifierSchemes[$schemeId].lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
  }

  $rawSources = Get-ProjectMapValue $registry "sources"
  if ($null -eq $rawSources -or -not ($rawSources -is [System.Collections.IDictionary])) { throw "Source registry 'sources' must be a mapping." }
  $sources=[ordered]@{}; $sourceAliases=@{}
  foreach ($sourceId in $rawSources.Keys) {
    $context="sources.$sourceId"; Test-StableSourceId $sourceId $context; $source=$rawSources[$sourceId]
    $lifecycle=Get-RequiredSourceString $source "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $workIds=@(Get-SourceStringList $source "work_ids" $context); $mediumId=Get-RequiredSourceString $source "medium_id" $context
    if($workIds.Count -eq 0 -or @($workIds|Sort-Object -Unique).Count -ne $workIds.Count){throw "Source registry '$context.work_ids' must be a non-empty duplicate-free list."}
    foreach($workId in $workIds){if(-not $works.Contains($workId)){throw "Source registry '$context.work_ids' references unknown work '$workId'."}}
    if (-not $mediums.Contains($mediumId)) { throw "Source registry '$context.medium_id' references unknown medium '$mediumId'." }
    $manifestationId=Get-OptionalSourceString $source "manifestation_id" $context
    if ($null -ne $manifestationId) {
      if (-not $manifestations.Contains($manifestationId)) { throw "Source registry '$context.manifestation_id' references unknown manifestation '$manifestationId'." }
      if ($workIds -notcontains $manifestations[$manifestationId].work_id) { throw "Source registry '$context' manifestation belongs to a work outside the source scope." }
    }
    $releasePackageId=Get-OptionalSourceString $source "release_package_id" $context
    if ($null -ne $releasePackageId) {
      if (-not $releasePackages.Contains($releasePackageId)) { throw "Source registry '$context.release_package_id' references unknown release package '$releasePackageId'." }
      $packageManifestationIds=@($releasePackages[$releasePackageId].manifestation_ids + @($releasePackages[$releasePackageId].release_component_ids | ForEach-Object { $releaseComponents[$_].manifestation_id } | Where-Object {$null -ne $_}) | Sort-Object -Unique)
      if ($null -ne $manifestationId -and $packageManifestationIds -notcontains $manifestationId) { throw "Source registry '$context' manifestation is not contained by its release package." }
      $packageWorkIds=@(& $getReleasePackageWorkIds $releasePackageId)
      if($packageWorkIds.Count -gt 0 -and @($workIds|Where-Object {$packageWorkIds -notcontains $_}).Count -gt 0){throw "Source registry '$context.work_ids' extends beyond its release package."}
    }
    $releaseEventId=Get-OptionalSourceString $source "release_event_id" $context
    if ($null -ne $releaseEventId) {
      if (-not $releaseEvents.Contains($releaseEventId)) { throw "Source registry '$context.release_event_id' references unknown release event '$releaseEventId'." }
      $expectedSubjectType=if($null -ne $releasePackageId){"release-package"}else{"manifestation"}
      $expectedSubjectId=if($null -ne $releasePackageId){$releasePackageId}else{$manifestationId}
      if ($releaseEvents[$releaseEventId].subject_type -ne $expectedSubjectType -or $releaseEvents[$releaseEventId].subject_id -ne $expectedSubjectId) { throw "Source registry '$context' release event does not belong to its manifestation or package." }
    }
    $releaseComponentIds=@(Get-SourceStringListAllowEmpty $source "release_component_ids" $context)
    foreach ($componentId in $releaseComponentIds) {
      if (-not $releaseComponents.Contains($componentId)) { throw "Source registry '$context.release_component_ids' references unknown component '$componentId'." }
      $componentMatches=($null -ne $manifestationId -and $releaseComponents[$componentId].manifestation_id -eq $manifestationId)
      if ($null -ne $releasePackageId) { $componentMatches=$componentMatches -or ($releasePackages[$releasePackageId].release_component_ids -contains $componentId) }
      if (-not $componentMatches) { throw "Source registry '$context' component '$componentId' does not belong to its manifestation or package." }
      $componentWorkIds=@($releaseComponents[$componentId].segment_ids|ForEach-Object {$segments[$_].work_id})
      if($null -ne $releaseComponents[$componentId].manifestation_id){$componentWorkIds+=@($manifestations[$releaseComponents[$componentId].manifestation_id].work_id)}
      $componentWorkIds=@($componentWorkIds|Sort-Object -Unique)
      if($componentWorkIds.Count -gt 0 -and @($componentWorkIds|Where-Object {$workIds -contains $_}).Count -eq 0){throw "Source registry '$context' component '$componentId' falls outside the source work scope."}
    }
    $platformOfferingId=Get-OptionalSourceString $source "platform_offering_id" $context
    if ($null -ne $platformOfferingId) {
      if (-not $platformOfferings.Contains($platformOfferingId)) { throw "Source registry '$context.platform_offering_id' references unknown offering '$platformOfferingId'." }
      $expectedSubjectType=if($null -ne $releasePackageId){"release-package"}else{"manifestation"}
      $expectedSubjectId=if($null -ne $releasePackageId){$releasePackageId}else{$manifestationId}
      if ($platformOfferings[$platformOfferingId].subject_type -ne $expectedSubjectType -or $platformOfferings[$platformOfferingId].subject_id -ne $expectedSubjectId) { throw "Source registry '$context' platform offering does not belong to its manifestation or package." }
    }
    $containerFormatIds = @(Get-SourceStringList $source "container_format_ids" $context)
    if ($containerFormatIds.Count -eq 0) { throw "Source registry '$context.container_format_ids' must not be empty." }
    $unknownContainerFormats = @($containerFormatIds | Where-Object { -not $containerFormats.Contains($_) } | Sort-Object -Unique)
    if ($unknownContainerFormats.Count -gt 0) { throw "Source registry '$context.container_format_ids' references unknown container formats: $($unknownContainerFormats -join ', ')." }
    $role=Get-RequiredSourceString $source "role" $context
    if ($allowedSourceRoles -notcontains $role) { throw "Source registry '$context.role' must be one of: $($allowedSourceRoles -join ', ')." }
    $incompatibleWorkIds=@($workIds|Where-Object {$works[$_].medium_id -ne $mediumId})
    if ($incompatibleWorkIds.Count -gt 0 -and $role -notin @("supplemental","reference","extract")) { throw "Source registry '$context' medium does not match works: $($incompatibleWorkIds -join ', ')." }
    $comparisonGroup=Get-RequiredSourceString $source "comparison_group" $context; Test-StableSourceId $comparisonGroup "$context.comparison_group"
    $priority=Get-ProjectMapValue $source "priority"
    if ($priority -is [bool] -or $priority -isnot [int] -or [int]$priority -lt 1) { throw "Source registry '$context.priority' must be a positive integer." }
    $aliases=@(Get-SourceStringListAllowEmpty $source "aliases" $context)
    foreach ($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"; $aliasKey=$alias.ToLowerInvariant()
      if ($sourceAliases.ContainsKey($aliasKey) -or @($rawSources.Keys | Where-Object { $_.ToLowerInvariant() -eq $aliasKey }).Count -gt 0) { throw "Source registry alias '$alias' is duplicated or collides with a source ID." }
      $sourceAliases[$aliasKey]=$sourceId
    }
    $evidenceModes=@(Get-SourceStringListAllowEmpty $source "evidence_modes" $context)
    foreach ($mode in $evidenceModes) { Test-StableSourceId $mode "$context.evidence_modes" }
    $coverage=@();$rawCoverage=@(Get-ProjectMapValue $source "coverage");$seenCoverage=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for($coverageIndex=0;$coverageIndex -lt $rawCoverage.Count;$coverageIndex++){
      $coverageContext="$context.coverage[$coverageIndex]";$coverageEntry=$rawCoverage[$coverageIndex]
      $targetType=Get-RequiredSourceString $coverageEntry "target_type" $coverageContext
      Assert-SourceSchemaPackValues $SchemaPackRegistry "source.coverage-target-type" @($targetType) "$coverageContext.target_type"
      $targetId=Get-RequiredSourceString $coverageEntry "target_id" $coverageContext
      $targetExists=switch($targetType){
        "work"{$works.Contains($targetId)}
        "segment"{$segments.Contains($targetId)}
        "content-group"{$contentGroups.Contains($targetId)}
        "manifestation"{$manifestations.Contains($targetId)}
        "release-component"{$releaseComponents.Contains($targetId)}
        "release-package"{$releasePackages.Contains($targetId)}
        default{$false}
      }
      if(-not $targetExists){throw "Source registry '$coverageContext.target_id' references unknown $targetType '$targetId'."}
      if(-not $seenCoverage.Add("$targetType|$targetId")){throw "Source registry '$context.coverage' repeats a target."}
      $coverageType=Get-RequiredSourceString $coverageEntry "coverage_type" $coverageContext
      Assert-SourceSchemaPackValues $SchemaPackRegistry "source.coverage-type" @($coverageType) "$coverageContext.coverage_type"
      $targetWorkIds=@()
      switch($targetType){
        "work"{$targetWorkIds=@($targetId)}
        "segment"{$targetWorkIds=@($segments[$targetId].work_id)}
        "content-group"{$targetWorkIds=@($contentGroups[$targetId].members|ForEach-Object {if($_.target_type -eq "work"){$_.target_id}else{$segments[$_.target_id].work_id}}|Sort-Object -Unique)}
        "manifestation"{$targetWorkIds=@($manifestations[$targetId].work_id)}
        "release-package"{$targetWorkIds=@(& $getReleasePackageWorkIds $targetId)}
        "release-component"{
          $targetWorkIds=@($releaseComponents[$targetId].segment_ids|ForEach-Object {$segments[$_].work_id})
          if($null -ne $releaseComponents[$targetId].manifestation_id){$targetWorkIds+=@($manifestations[$releaseComponents[$targetId].manifestation_id].work_id)}
          $targetWorkIds=@($targetWorkIds|Sort-Object -Unique)
        }
      }
      if($targetWorkIds.Count -gt 0 -and @($targetWorkIds|Where-Object {$workIds -notcontains $_}).Count -gt 0){throw "Source registry '$coverageContext' extends beyond the source work scope."}
      $coverage += [pscustomobject]@{target_type=$targetType;target_id=$targetId;coverage_type=$coverageType}
    }
    $bindings=@(); $rawBindings=@(Get-ProjectMapValue $source "resource_bindings")
    for ($i=0; $i -lt $rawBindings.Count; $i++) { $bindings += Resolve-SourceResourceBinding $ProjectConfig $ResourceConfig $rawBindings[$i] "$context.resource_bindings[$i]" }
    $sources[$sourceId]=[pscustomobject]@{ id=$sourceId; lifecycle=$lifecycle; label=Get-RequiredSourceString $source "label" $context; work_ids=@($workIds); manifestation_id=$manifestationId; release_package_id=$releasePackageId; release_event_id=$releaseEventId; release_component_ids=@($releaseComponentIds); platform_offering_id=$platformOfferingId; medium_id=$mediumId; container_format_ids=@($containerFormatIds); role=$role; comparison_group=$comparisonGroup; priority=[int]$priority; aliases=@($aliases); evidence_modes=@($evidenceModes); coverage=@($coverage); resource_bindings=@($bindings) }
  }
  Assert-SourceSchemaPackValues $SchemaPackRegistry "source.source-role" @($sources.Values | ForEach-Object { $_.role }) "sources.*.role"

  $sourceRelationships=@(); $rawSourceRelationships=@(Get-ProjectMapValue $registry "source_relationships")
  for ($index=0; $index -lt $rawSourceRelationships.Count; $index++) {
    $context="source_relationships[$index]"; $relationship=$rawSourceRelationships[$index]
    $id=Get-RequiredSourceString $relationship "id" $context; Test-StableSourceId $id "$context.id"
    if (-not $seenRelationshipIds.Add($id)) { throw "Source registry relationship ID '$id' is duplicated." }
    $sourceId=Get-RequiredSourceString $relationship "source_source_id" $context; $targetId=Get-RequiredSourceString $relationship "target_source_id" $context
    $type=Get-RequiredSourceString $relationship "relationship_type" $context
    if (-not $sources.Contains($sourceId) -or -not $sources.Contains($targetId)) { throw "Source registry '$context' references an unknown source." }
    if ($sourceId -eq $targetId) { throw "Source registry '$context' cannot relate a source to itself." }
    if (-not $sourceRelationshipTypes.Contains($type)) { throw "Source registry '$context.relationship_type' references unknown type '$type'." }
    $sourceRelationships += [pscustomobject]@{ id=$id; source_source_id=$sourceId; relationship_type=$type; target_source_id=$targetId }
  }

  $provenanceAssertions=@();$seenProvenanceIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $rawProvenanceAssertions=@(Get-ProjectMapValue $registry "provenance_assertions")
  for($index=0;$index -lt $rawProvenanceAssertions.Count;$index++){
    $context="provenance_assertions[$index]";$assertion=$rawProvenanceAssertions[$index]
    $id=Get-RequiredSourceString $assertion "id" $context;Test-StableSourceId $id "$context.id"
    if(-not $seenProvenanceIds.Add($id)){throw "Source registry provenance assertion ID '$id' is duplicated."}
    $subjectType=Get-RequiredSourceString $assertion "subject_type" $context
    Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.subject-type" @($subjectType) "$context.subject_type"
    $subjectId=Get-RequiredSourceString $assertion "subject_id" $context
    $subjectExists=switch($subjectType){
      "work"{$works.Contains($subjectId)}
      "segment"{$segments.Contains($subjectId)}
      "content-group"{$contentGroups.Contains($subjectId)}
      "work-relationship"{@($workRelationships|Where-Object {$_.id -eq $subjectId}).Count -eq 1}
      "adaptation-mapping"{@($adaptationMappings|Where-Object {$_.id -eq $subjectId}).Count -eq 1}
      "manifestation"{$manifestations.Contains($subjectId)}
      "manifestation-relationship"{@($manifestationRelationships|Where-Object {$_.id -eq $subjectId}).Count -eq 1}
      "manifestation-segment-mapping"{@($manifestationSegmentMappings|Where-Object {$_.id -eq $subjectId}).Count -eq 1}
      "release-component"{$releaseComponents.Contains($subjectId)}
      "release-component-relationship"{@($releaseComponentRelationships|Where-Object {$_.id -eq $subjectId}).Count -eq 1}
      "release-package"{$releasePackages.Contains($subjectId)}
      "release-run"{$releaseRuns.Contains($subjectId)}
      "release-event"{$releaseEvents.Contains($subjectId)}
      "catalog-placement"{$catalogPlacements.Contains($subjectId)}
      "platform-offering"{$platformOfferings.Contains($subjectId)}
      "source"{$sources.Contains($subjectId)}
      "source-relationship"{@($sourceRelationships|Where-Object {$_.id -eq $subjectId}).Count -eq 1}
      default{$false}
    }
    if(-not $subjectExists){throw "Source registry '$context.subject_id' references unknown $subjectType '$subjectId'."}
    $fieldPath=Get-OptionalSourceString $assertion "field_path" $context
    if($null -ne $fieldPath -and $fieldPath -notmatch $script:SourceFieldPathPattern){throw "Source registry '$context.field_path' must be a dotted/indexed machine field path."}
    $assertionStatus=Get-RequiredSourceString $assertion "assertion_status" $context
    Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.assertion-status" @($assertionStatus) "$context.assertion_status"
    $rawEvidenceLinks=@(Get-ProjectMapValue $assertion "evidence_links")
    if($rawEvidenceLinks.Count -eq 0){throw "Source registry '$context.evidence_links' must be a non-empty list."}
    $evidenceLinks=@();$seenEvidenceSources=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for($evidenceIndex=0;$evidenceIndex -lt $rawEvidenceLinks.Count;$evidenceIndex++){
      $evidenceContext="$context.evidence_links[$evidenceIndex]";$link=$rawEvidenceLinks[$evidenceIndex]
      $evidenceSourceId=Get-RequiredSourceString $link "source_id" $evidenceContext
      if(-not $sources.Contains($evidenceSourceId)){throw "Source registry '$evidenceContext.source_id' references unknown source '$evidenceSourceId'."}
      if(-not $seenEvidenceSources.Add($evidenceSourceId)){throw "Source registry '$context.evidence_links' repeats source '$evidenceSourceId'."}
      $evidenceRole=Get-RequiredSourceString $link "evidence_role" $evidenceContext
      Assert-SourceSchemaPackValues $SchemaPackRegistry "provenance.evidence-role" @($evidenceRole) "$evidenceContext.evidence_role"
      $evidenceLinks += [pscustomobject]@{source_id=$evidenceSourceId;evidence_role=$evidenceRole}
    }
    $provenanceAssertions += [pscustomobject]@{id=$id;subject_type=$subjectType;subject_id=$subjectId;field_path=$fieldPath;assertion_status=$assertionStatus;evidence_links=@($evidenceLinks)}
  }

  $rawExternalIdentifiers=@(Get-ProjectMapValue $registry "external_identifiers")
  $externalIdentifiers=@()
  $seenExternalIdentifierIds=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $seenSchemeValues=New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for ($index=0; $index -lt $rawExternalIdentifiers.Count; $index++) {
    $context="external_identifiers[$index]"; $identifier=$rawExternalIdentifiers[$index]
    $id=Get-RequiredSourceString $identifier "id" $context; Test-StableSourceId $id "$context.id"
    if (-not $seenExternalIdentifierIds.Add($id)) { throw "Source registry external identifier ID '$id' is duplicated." }
    $schemeId=Get-RequiredSourceString $identifier "scheme_id" $context
    if (-not $identifierSchemes.Contains($schemeId)) { throw "Source registry '$context.scheme_id' references unknown scheme '$schemeId'." }
    $targetType=Get-RequiredSourceString $identifier "target_type" $context
    if ($identifierSchemes[$schemeId].target_types -notcontains $targetType) { throw "Source registry '$context.target_type' is not allowed by identifier scheme '$schemeId'." }
    $targetId=Get-RequiredSourceString $identifier "target_id" $context
    $targetExists=switch($targetType) {
      "work" { $works.Contains($targetId) }
      "segment" { $segments.Contains($targetId) }
      "content-group" { $contentGroups.Contains($targetId) }
      "manifestation" { $manifestations.Contains($targetId) }
      "release-package" { $releasePackages.Contains($targetId) }
      "release-run" { $releaseRuns.Contains($targetId) }
      "release-event" { $releaseEvents.Contains($targetId) }
      "platform" { $platforms.Contains($targetId) }
      "catalog-placement" { $catalogPlacements.Contains($targetId) }
      "source" { $sources.Contains($targetId) }
      default { $false }
    }
    if (-not $targetExists) { throw "Source registry '$context.target_id' references unknown $targetType '$targetId'." }
    $value=Get-RequiredSourceString $identifier "value" $context
    $normalizedValue=if($identifierSchemes[$schemeId].case_sensitive){$value}else{$value.ToLowerInvariant()}
    if (-not $seenSchemeValues.Add("$schemeId|$normalizedValue")) { throw "Source registry repeats value '$value' in identifier scheme '$schemeId'." }
    $territoryIds=@(Get-SourceStringListAllowEmpty $identifier "territory_ids" $context)
    foreach ($territoryId in $territoryIds) { if (-not $territories.Contains($territoryId)) { throw "Source registry '$context.territory_ids' references unknown territory '$territoryId'." } }
    $languageTag=Get-OptionalSourceString $identifier "language_tag" $context
    if ($null -ne $languageTag) { Test-SourceLanguageTag $languageTag "$context.language_tag" }
    $status=Get-RequiredSourceString $identifier "status" $context
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.identifier-status" @($status) "$context.status"
    $externalIdentifiers += [pscustomobject]@{ id=$id; scheme_id=$schemeId; target_type=$targetType; target_id=$targetId; value=$value; territory_ids=@($territoryIds); language_tag=$languageTag; status=$status }
  }

  return [pscustomobject]@{
    path=$registryPath; schema_version=[int]$schemaVersion; default_authority_profile_id=$defaultAuthorityProfileId
    media_modalities=$mediaModalities; cultural_forms=$culturalForms; release_forms=$releaseForms; container_formats=$containerFormats
    mediums=$mediums; work_group_types=$workGroupTypes; work_groups=$workGroups; continuities=$continuities
    continuity_relationship_types=$continuityRelationshipTypes; continuity_relationships=@($continuityRelationships)
    authority_profiles=$authorityProfiles; work_relationship_types=$workRelationshipTypes; works=$works
    segments=$segments; content_groups=$contentGroups; ordering_schemes=$orderingSchemes; numbering_schemes=$numberingSchemes
    work_relationships=@($workRelationships); adaptation_mappings=@($adaptationMappings)
    territories=$territories; platforms=$platforms; manifestation_relationship_types=$manifestationRelationshipTypes
    manifestations=$manifestations; manifestation_relationships=@($manifestationRelationships); manifestation_segment_mappings=@($manifestationSegmentMappings)
    release_components=$releaseComponents; release_component_relationship_types=$releaseComponentRelationshipTypes
    release_component_relationships=@($releaseComponentRelationships); release_packages=$releasePackages; release_runs=$releaseRuns; release_events=$releaseEvents
    catalog_placements=$catalogPlacements; platform_offerings=$platformOfferings
    identifier_schemes=$identifierSchemes; external_identifiers=@($externalIdentifiers)
    work_aliases=$workAliases; source_relationship_types=$sourceRelationshipTypes
    sources=$sources; source_relationships=@($sourceRelationships); source_aliases=$sourceAliases
    provenance_assertions=@($provenanceAssertions)
  }
}
