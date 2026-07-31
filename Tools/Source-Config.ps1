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

$script:SupportedSourceSchemaVersion = 3
$script:AllowedSourceLifecycles = @("active", "deferred")
$script:AllowedPositionFieldTypes = @("string", "integer", "number", "timestamp", "boolean")
$script:AllowedPriorityOrders = @("ascending", "descending")
$script:AllowedConflictBehaviors = @("flag")
$script:AllowedDeviationOwners = @("derivative-work")
$script:AllowedChapterNumberingModes = @("work-local", "series-global", "not-applicable")
$script:AllowedVolumeCatalogStatuses = @("verified", "pending-verification", "not-applicable")
$script:SourceFieldIdPattern = "^[a-z][a-z0-9_]*$"

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
      medium_id=$mediumId; release_form_id=$releaseFormId; work_status=$workStatus
      aliases=@($aliases); group_memberships=@($groupMemberships)
      continuity_memberships=@($continuityMemberships); chapter_numbering=$chapterNumbering
      volume_catalog_status=$volumeStatus; volumes=@($volumes)
    }
  }
  Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-type" @($works.Values | ForEach-Object { $_.work_type }) "works.*.work_type"
  Assert-SourceSchemaPackValues $SchemaPackRegistry "source.work-lifecycle-status" @($works.Values | ForEach-Object { $_.work_status }) "works.*.work_status"

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

  $rawOrderingSchemes = Get-ProjectMapValue $registry "ordering_schemes"
  if ($null -eq $rawOrderingSchemes -or -not ($rawOrderingSchemes -is [System.Collections.IDictionary])) { throw "Source registry 'ordering_schemes' must be a mapping." }
  $orderingSchemes = [ordered]@{}
  foreach ($schemeId in $rawOrderingSchemes.Keys) {
    $context = "ordering_schemes.$schemeId"
    Test-StableSourceId $schemeId $context
    $scheme = $rawOrderingSchemes[$schemeId]
    $orderingType = Get-RequiredSourceString $scheme "ordering_type" $context
    Test-StableSourceId $orderingType "$context.ordering_type"
    $rawEntries = @(Get-ProjectMapValue $scheme "entries")
    if ($rawEntries.Count -eq 0) { throw "Source registry '$context.entries' must be a non-empty list." }
    $entries = @()
    $seenTargets = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $seenOrderingOrdinals = New-Object 'System.Collections.Generic.HashSet[int]'
    for ($index=0; $index -lt $rawEntries.Count; $index++) {
      $entryContext = "$context.entries[$index]"
      $entry = $rawEntries[$index]
      $targetType = Get-RequiredSourceString $entry "target_type" $entryContext
      if ($targetType -notin @("work","segment")) { throw "Source registry '$entryContext.target_type' must be 'work' or 'segment'." }
      $targetId = Get-RequiredSourceString $entry "target_id" $entryContext
      $targetRegistry = if ($targetType -eq "work") { $works } else { $segments }
      if (-not $targetRegistry.Contains($targetId)) { throw "Source registry '$entryContext.target_id' references unknown $targetType '$targetId'." }
      $ordinal = Get-ProjectMapValue $entry "ordinal"
      if ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1) { throw "Source registry '$entryContext.ordinal' must be a positive integer." }
      if (-not $seenTargets.Add("$targetType|$targetId") -or -not $seenOrderingOrdinals.Add([int]$ordinal)) { throw "Source registry '$context.entries' repeats a target or ordinal." }
      $entries += [pscustomobject]@{ target_type=$targetType; target_id=$targetId; ordinal=[int]$ordinal }
    }
    $orderingSchemes[$schemeId] = [pscustomobject]@{
      id=$schemeId; label=Get-RequiredSourceString $scheme "label" $context
      ordering_type=$orderingType; entries=@($entries | Sort-Object ordinal)
    }
  }
  if ($orderingSchemes.Count -gt 0) {
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.ordering-type" @($orderingSchemes.Values | ForEach-Object { $_.ordering_type }) "ordering_schemes.*.ordering_type"
  }

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
    $sourceWorkId = Get-RequiredSourceString $mapping "source_work_id" $context
    $targetWorkId = Get-RequiredSourceString $mapping "target_work_id" $context
    if (-not $works.Contains($sourceWorkId) -or -not $works.Contains($targetWorkId)) { throw "Source registry '$context' references an unknown work." }
    $sourceSegmentIds = @(Get-SourceStringListAllowEmpty $mapping "source_segment_ids" $context)
    $targetSegmentIds = @(Get-SourceStringListAllowEmpty $mapping "target_segment_ids" $context)
    foreach ($entry in @(
      [pscustomobject]@{ name="source_segment_ids"; ids=$sourceSegmentIds; work_id=$sourceWorkId },
      [pscustomobject]@{ name="target_segment_ids"; ids=$targetSegmentIds; work_id=$targetWorkId }
    )) {
      foreach ($segmentId in $entry.ids) {
        if (-not $segments.Contains($segmentId)) { throw "Source registry '$context.$($entry.name)' references unknown segment '$segmentId'." }
        if ($segments[$segmentId].work_id -ne $entry.work_id) { throw "Source registry '$context.$($entry.name)' segment '$segmentId' belongs to a different work." }
      }
    }
    $mappingType = Get-RequiredSourceString $mapping "mapping_type" $context
    $status = Get-RequiredSourceString $mapping "status" $context
    if ($allowedMembershipStatuses -notcontains $status) { throw "Source registry '$context.status' must be one of: $($allowedMembershipStatuses -join ', ')." }
    $adaptationMappings += [pscustomobject]@{
      id=$id; source_work_id=$sourceWorkId; target_work_id=$targetWorkId
      source_segment_ids=@($sourceSegmentIds); target_segment_ids=@($targetSegmentIds)
      mapping_type=$mappingType; status=$status
    }
  }
  if ($adaptationMappings.Count -gt 0) {
    Assert-SourceSchemaPackValues $SchemaPackRegistry "source.adaptation-mapping-type" @($adaptationMappings | ForEach-Object { $_.mapping_type }) "adaptation_mappings.*.mapping_type"
  }

  $rawSources = Get-ProjectMapValue $registry "sources"
  if ($null -eq $rawSources -or -not ($rawSources -is [System.Collections.IDictionary])) { throw "Source registry 'sources' must be a mapping." }
  $sources=[ordered]@{}; $sourceAliases=@{}
  foreach ($sourceId in $rawSources.Keys) {
    $context="sources.$sourceId"; Test-StableSourceId $sourceId $context; $source=$rawSources[$sourceId]
    $lifecycle=Get-RequiredSourceString $source "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) { throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')." }
    $workId=Get-RequiredSourceString $source "work_id" $context; $mediumId=Get-RequiredSourceString $source "medium_id" $context
    if (-not $works.Contains($workId)) { throw "Source registry '$context.work_id' references unknown work '$workId'." }
    if (-not $mediums.Contains($mediumId)) { throw "Source registry '$context.medium_id' references unknown medium '$mediumId'." }
    $containerFormatIds = @(Get-SourceStringList $source "container_format_ids" $context)
    if ($containerFormatIds.Count -eq 0) { throw "Source registry '$context.container_format_ids' must not be empty." }
    $unknownContainerFormats = @($containerFormatIds | Where-Object { -not $containerFormats.Contains($_) } | Sort-Object -Unique)
    if ($unknownContainerFormats.Count -gt 0) { throw "Source registry '$context.container_format_ids' references unknown container formats: $($unknownContainerFormats -join ', ')." }
    $role=Get-RequiredSourceString $source "role" $context
    if ($allowedSourceRoles -notcontains $role) { throw "Source registry '$context.role' must be one of: $($allowedSourceRoles -join ', ')." }
    if ($works[$workId].medium_id -ne $mediumId -and $role -notin @("supplemental","reference","extract")) { throw "Source registry '$context' medium does not match work '$workId'." }
    $comparisonGroup=Get-RequiredSourceString $source "comparison_group" $context; Test-StableSourceId $comparisonGroup "$context.comparison_group"
    $priority=Get-ProjectMapValue $source "priority"
    if ($priority -is [bool] -or $priority -isnot [int] -or [int]$priority -lt 1) { throw "Source registry '$context.priority' must be a positive integer." }
    $aliases=@(Get-SourceStringList $source "aliases" $context)
    foreach ($alias in $aliases) {
      Test-StableSourceId $alias "$context.aliases"; $aliasKey=$alias.ToLowerInvariant()
      if ($sourceAliases.ContainsKey($aliasKey) -or @($rawSources.Keys | Where-Object { $_.ToLowerInvariant() -eq $aliasKey }).Count -gt 0) { throw "Source registry alias '$alias' is duplicated or collides with a source ID." }
      $sourceAliases[$aliasKey]=$sourceId
    }
    $evidenceModes=@(Get-SourceStringList $source "evidence_modes" $context)
    foreach ($mode in $evidenceModes) { Test-StableSourceId $mode "$context.evidence_modes" }
    $bindings=@(); $rawBindings=@(Get-ProjectMapValue $source "resource_bindings")
    for ($i=0; $i -lt $rawBindings.Count; $i++) { $bindings += Resolve-SourceResourceBinding $ProjectConfig $ResourceConfig $rawBindings[$i] "$context.resource_bindings[$i]" }
    $sources[$sourceId]=[pscustomobject]@{ id=$sourceId; lifecycle=$lifecycle; label=Get-RequiredSourceString $source "label" $context; work_id=$workId; medium_id=$mediumId; container_format_ids=@($containerFormatIds); role=$role; comparison_group=$comparisonGroup; priority=[int]$priority; aliases=@($aliases); evidence_modes=@($evidenceModes); resource_bindings=@($bindings) }
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

  return [pscustomobject]@{
    path=$registryPath; schema_version=[int]$schemaVersion; default_authority_profile_id=$defaultAuthorityProfileId
    media_modalities=$mediaModalities; cultural_forms=$culturalForms; release_forms=$releaseForms; container_formats=$containerFormats
    mediums=$mediums; work_group_types=$workGroupTypes; work_groups=$workGroups; continuities=$continuities
    continuity_relationship_types=$continuityRelationshipTypes; continuity_relationships=@($continuityRelationships)
    authority_profiles=$authorityProfiles; work_relationship_types=$workRelationshipTypes; works=$works
    segments=$segments; ordering_schemes=$orderingSchemes
    work_relationships=@($workRelationships); adaptation_mappings=@($adaptationMappings)
    work_aliases=$workAliases; source_relationship_types=$sourceRelationshipTypes
    sources=$sources; source_relationships=@($sourceRelationships); source_aliases=$sourceAliases
  }
}
