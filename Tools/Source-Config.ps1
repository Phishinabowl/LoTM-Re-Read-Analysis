$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) {
  . $projectConfigHelper
}
$resourceConfigHelper = Join-Path $PSScriptRoot "Resource-Config.ps1"
if (-not (Get-Command Get-KnowledgeResourceConfig -ErrorAction SilentlyContinue)) {
  . $resourceConfigHelper
}

$script:SupportedSourceSchemaVersion = 1
$script:AllowedSourceLifecycles = @("active", "deferred")
$script:AllowedSourceRoles = @("original", "adaptation", "transcript", "supplemental", "reference")
$script:AllowedPositionFieldTypes = @("string", "integer", "number", "timestamp", "boolean")
$script:AllowedPriorityOrders = @("ascending", "descending")
$script:AllowedConflictBehaviors = @("flag")
$script:AllowedDeviationOwners = @("adaptation-source")
$script:AllowedChapterNumberingModes = @("work-local", "series-global")
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

function ConvertTo-SourceComparisonPolicy {
  param([object]$RawPolicy)

  $context = "comparison_policy"
  if ($null -eq $RawPolicy -or -not ($RawPolicy -is [System.Collections.IDictionary])) {
    throw "Source registry '$context' must be a mapping."
  }
  $priorityOrder = Get-RequiredSourceString $RawPolicy "priority_order" $context
  if ($script:AllowedPriorityOrders -notcontains $priorityOrder) {
    throw "Source registry '$context.priority_order' must be one of: $($script:AllowedPriorityOrders -join ', ')."
  }
  $conflictBehavior = Get-RequiredSourceString $RawPolicy "cross_source_conflict" $context
  if ($script:AllowedConflictBehaviors -notcontains $conflictBehavior) {
    throw "Source registry '$context.cross_source_conflict' must be one of: $($script:AllowedConflictBehaviors -join ', ')."
  }
  $deviationOwner = Get-RequiredSourceString $RawPolicy "adaptation_deviation_owner" $context
  if ($script:AllowedDeviationOwners -notcontains $deviationOwner) {
    throw "Source registry '$context.adaptation_deviation_owner' must be one of: $($script:AllowedDeviationOwners -join ', ')."
  }
  return [pscustomobject]@{
    priority_order = $priorityOrder
    compare_within_group_only = Get-RequiredSourceBoolean $RawPolicy "compare_within_group_only" $context
    compare_within_work_only = Get-RequiredSourceBoolean $RawPolicy "compare_within_work_only" $context
    cross_source_conflict = $conflictBehavior
    adaptation_deviation_owner = $deviationOwner
    preserve_source_scoped_claims = Get-RequiredSourceBoolean $RawPolicy "preserve_source_scoped_claims" $context
  }
}

function ConvertTo-SeriesConfig {
  param([string]$SeriesId, [object]$RawSeries)

  $context = "series.$SeriesId"
  Test-StableSourceId $SeriesId $context
  if ($null -eq $RawSeries -or -not ($RawSeries -is [System.Collections.IDictionary])) {
    throw "Source registry '$context' must be a mapping."
  }
  $lifecycle = Get-RequiredSourceString $RawSeries "lifecycle" $context
  if ($script:AllowedSourceLifecycles -notcontains $lifecycle) {
    throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
  }
  return [pscustomobject]@{
    id = $SeriesId
    lifecycle = $lifecycle
    label = Get-RequiredSourceString $RawSeries "label" $context
    short_label = Get-RequiredSourceString $RawSeries "short_label" $context
  }
}

function ConvertTo-WorkConfig {
  param(
    [string]$WorkId,
    [object]$RawWork,
    [System.Collections.IDictionary]$Series,
    [System.Collections.IDictionary]$Mediums
  )

  $context = "works.$WorkId"
  Test-StableSourceId $WorkId $context
  if ($null -eq $RawWork -or -not ($RawWork -is [System.Collections.IDictionary])) {
    throw "Source registry '$context' must be a mapping."
  }
  $lifecycle = Get-RequiredSourceString $RawWork "lifecycle" $context
  if ($script:AllowedSourceLifecycles -notcontains $lifecycle) {
    throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
  }
  $seriesId = Get-RequiredSourceString $RawWork "series_id" $context
  if (-not $Series.Contains($seriesId)) {
    throw "Source registry '$context.series_id' references unknown series '$seriesId'."
  }
  $mediumId = Get-RequiredSourceString $RawWork "medium_id" $context
  if (-not $Mediums.Contains($mediumId)) {
    throw "Source registry '$context.medium_id' references unknown medium '$mediumId'."
  }
  $ordinal = Get-ProjectMapValue $RawWork "ordinal"
  if ($ordinal -is [bool] -or $ordinal -isnot [int] -or [int]$ordinal -lt 1) {
    throw "Source registry '$context.ordinal' must be a positive integer."
  }
  $workType = Get-RequiredSourceString $RawWork "work_type" $context
  Test-StableSourceId $workType "$context.work_type"
  $chapterNumbering = Get-RequiredSourceString $RawWork "chapter_numbering" $context
  if ($script:AllowedChapterNumberingModes -notcontains $chapterNumbering) {
    throw "Source registry '$context.chapter_numbering' must be one of: $($script:AllowedChapterNumberingModes -join ', ')."
  }
  $volumeStatus = Get-RequiredSourceString $RawWork "volume_catalog_status" $context
  if ($script:AllowedVolumeCatalogStatuses -notcontains $volumeStatus) {
    throw "Source registry '$context.volume_catalog_status' must be one of: $($script:AllowedVolumeCatalogStatuses -join ', ')."
  }
  $aliases = @(Get-SourceStringList $RawWork "aliases" $context)
  foreach ($alias in $aliases) {
    Test-StableSourceId $alias "$context.aliases"
  }
  if (-not $RawWork.Contains("volumes")) {
    throw "Source registry '$context.volumes' must be a list."
  }
  $rawVolumes = @(Get-ProjectMapValue $RawWork "volumes")
  if ($volumeStatus -eq "verified" -and $rawVolumes.Count -eq 0) {
    throw "Source registry verified work '$WorkId' requires volume records."
  }
  $volumes = @()
  $volumeIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  $volumeNumbers = New-Object 'System.Collections.Generic.HashSet[int]'
  for ($index = 0; $index -lt $rawVolumes.Count; $index += 1) {
    $volume = $rawVolumes[$index]
    $volumeContext = "$context.volumes[$index]"
    if ($null -eq $volume -or -not ($volume -is [System.Collections.IDictionary])) {
      throw "Source registry '$volumeContext' must be a mapping."
    }
    $volumeId = Get-RequiredSourceString $volume "id" $volumeContext
    Test-StableSourceId $volumeId "$volumeContext.id"
    if (-not $volumeIds.Add($volumeId)) {
      throw "Source registry '$volumeContext.id' duplicates '$volumeId'."
    }
    $number = Get-ProjectMapValue $volume "number"
    $chapterStart = Get-ProjectMapValue $volume "chapter_start"
    $chapterEnd = Get-ProjectMapValue $volume "chapter_end"
    foreach ($field in @(
      [pscustomobject]@{ name = "number"; value = $number },
      [pscustomobject]@{ name = "chapter_start"; value = $chapterStart },
      [pscustomobject]@{ name = "chapter_end"; value = $chapterEnd }
    )) {
      if ($field.value -is [bool] -or $field.value -isnot [int] -or [int]$field.value -lt 1) {
        throw "Source registry '$volumeContext.$($field.name)' must be a positive integer."
      }
    }
    if (-not $volumeNumbers.Add([int]$number)) {
      throw "Source registry '$context' duplicates volume number $number."
    }
    if ([int]$chapterEnd -lt [int]$chapterStart) {
      throw "Source registry '$volumeContext' chapter range is reversed."
    }
    $volumes += [pscustomobject]@{
      id = $volumeId
      number = [int]$number
      label = Get-RequiredSourceString $volume "label" $volumeContext
      chapter_start = [int]$chapterStart
      chapter_end = [int]$chapterEnd
    }
  }
  $sortedVolumes = @($volumes | Sort-Object number)
  if ($volumeStatus -eq "verified") {
    for ($index = 0; $index -lt $sortedVolumes.Count; $index += 1) {
      if ($sortedVolumes[$index].number -ne $index + 1) {
        throw "Source registry '$context' verified volume numbers must be contiguous from 1."
      }
      if ($index -gt 0 -and $sortedVolumes[$index].chapter_start -ne $sortedVolumes[$index - 1].chapter_end + 1) {
        throw "Source registry '$context' verified chapter ranges must be contiguous and non-overlapping."
      }
    }
  }
  return [pscustomobject]@{
    id = $WorkId
    lifecycle = $lifecycle
    series_id = $seriesId
    label = Get-RequiredSourceString $RawWork "label" $context
    short_label = Get-RequiredSourceString $RawWork "short_label" $context
    ordinal = [int]$ordinal
    work_type = $workType
    medium_id = $mediumId
    aliases = @($aliases)
    chapter_numbering = $chapterNumbering
    volume_catalog_status = $volumeStatus
    volumes = @($sortedVolumes)
  }
}

function ConvertTo-MediumConfig {
  param([string]$MediumId, [object]$RawMedium)

  $context = "mediums.$MediumId"
  Test-StableSourceId $MediumId $context
  if ($null -eq $RawMedium -or -not ($RawMedium -is [System.Collections.IDictionary])) {
    throw "Source registry '$context' must be a mapping."
  }
  $lifecycle = Get-RequiredSourceString $RawMedium "lifecycle" $context
  if ($script:AllowedSourceLifecycles -notcontains $lifecycle) {
    throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
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
    fields = $fields
    required_fields = @($requiredFields)
    sort_fields = @($sortFields)
    citation_formats = @($citationFormats)
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

function Test-SourceDerivationCycle {
  param(
    [string]$SourceId,
    [System.Collections.IDictionary]$Sources,
    [System.Collections.Generic.HashSet[string]]$Active,
    [System.Collections.Generic.HashSet[string]]$Complete
  )

  if ($Active.Contains($SourceId)) {
    throw "Source registry contains a derivation cycle involving '$SourceId'."
  }
  if ($Complete.Contains($SourceId)) {
    return
  }
  $null = $Active.Add($SourceId)
  $source = $Sources[$SourceId]
  foreach ($targetId in @($source.adapted_from_source_id, $source.derived_from_source_id)) {
    if ($null -ne $targetId) {
      Test-SourceDerivationCycle $targetId $Sources $Active $Complete
    }
  }
  $null = $Active.Remove($SourceId)
  $null = $Complete.Add($SourceId)
}

function Get-KnowledgeSourceRegistry {
  param([object]$ProjectConfig, [object]$ResourceConfig)

  Import-ProjectYamlModule
  $registryPath = $ProjectConfig.sources_registry
  $registry = ConvertFrom-Yaml -Yaml ([System.IO.File]::ReadAllText($registryPath, [System.Text.UTF8Encoding]::new($true))) -Ordered
  if ($null -eq $registry -or -not ($registry -is [System.Collections.IDictionary])) {
    throw "Source registry root must be a mapping: $registryPath"
  }
  $schemaVersion = Get-ProjectMapValue $registry "schema_version"
  if ([int]$schemaVersion -ne $script:SupportedSourceSchemaVersion) {
    throw "Unsupported source schema_version '$schemaVersion'; expected $($script:SupportedSourceSchemaVersion)."
  }
  $policy = ConvertTo-SourceComparisonPolicy (Get-ProjectMapValue $registry "comparison_policy")

  $rawMediums = Get-ProjectMapValue $registry "mediums"
  if ($null -eq $rawMediums -or -not ($rawMediums -is [System.Collections.IDictionary])) {
    throw "Source registry 'mediums' must be a mapping."
  }
  $mediums = [ordered]@{}
  foreach ($mediumId in $rawMediums.Keys) {
    $mediums[$mediumId] = ConvertTo-MediumConfig $mediumId $rawMediums[$mediumId]
  }

  $rawSeries = Get-ProjectMapValue $registry "series"
  if ($null -eq $rawSeries -or -not ($rawSeries -is [System.Collections.IDictionary])) {
    throw "Source registry 'series' must be a mapping."
  }
  $series = [ordered]@{}
  foreach ($seriesId in $rawSeries.Keys) {
    $series[$seriesId] = ConvertTo-SeriesConfig $seriesId $rawSeries[$seriesId]
  }
  $rawWorks = Get-ProjectMapValue $registry "works"
  if ($null -eq $rawWorks -or -not ($rawWorks -is [System.Collections.IDictionary])) {
    throw "Source registry 'works' must be a mapping."
  }
  $works = [ordered]@{}
  foreach ($workId in $rawWorks.Keys) {
    $works[$workId] = ConvertTo-WorkConfig $workId $rawWorks[$workId] $series $mediums
  }
  $seenOrdinals = @{}
  $workAliases = @{}
  foreach ($work in $works.Values) {
    $ordinalKey = "$($work.series_id)|$($work.ordinal)"
    if ($seenOrdinals.ContainsKey($ordinalKey)) {
      throw "Source registry duplicates ordinal $($work.ordinal) in series '$($work.series_id)' between '$($seenOrdinals[$ordinalKey])' and '$($work.id)'."
    }
    $seenOrdinals[$ordinalKey] = $work.id
    foreach ($alias in $work.aliases) {
      $aliasKey = $alias.ToLowerInvariant()
      $workIdCollision = @($works.Keys | Where-Object { $_.ToLowerInvariant() -eq $aliasKey })
      if ($workAliases.ContainsKey($aliasKey) -or $workIdCollision.Count -gt 0) {
        throw "Source registry work alias '$alias' is duplicated or collides with a work ID."
      }
      $workAliases[$aliasKey] = $work.id
    }
  }

  $rawSources = Get-ProjectMapValue $registry "sources"
  if ($null -eq $rawSources -or -not ($rawSources -is [System.Collections.IDictionary])) {
    throw "Source registry 'sources' must be a mapping."
  }
  $sources = [ordered]@{}
  $aliases = @{}
  foreach ($sourceId in $rawSources.Keys) {
    $context = "sources.$sourceId"
    Test-StableSourceId $sourceId $context
    $source = $rawSources[$sourceId]
    if ($null -eq $source -or -not ($source -is [System.Collections.IDictionary])) {
      throw "Source registry '$context' must be a mapping."
    }
    $lifecycle = Get-RequiredSourceString $source "lifecycle" $context
    if ($script:AllowedSourceLifecycles -notcontains $lifecycle) {
      throw "Source registry '$context.lifecycle' must be one of: $($script:AllowedSourceLifecycles -join ', ')."
    }
    $mediumId = Get-RequiredSourceString $source "medium_id" $context
    if (-not $mediums.Contains($mediumId)) {
      throw "Source registry '$context.medium_id' references unknown medium '$mediumId'."
    }
    $role = Get-RequiredSourceString $source "role" $context
    if ($script:AllowedSourceRoles -notcontains $role) {
      throw "Source registry '$context.role' must be one of: $($script:AllowedSourceRoles -join ', ')."
    }
    $workId = Get-RequiredSourceString $source "work_id" $context
    if (-not $works.Contains($workId)) {
      throw "Source registry '$context.work_id' references unknown work '$workId'."
    }
    if ($works[$workId].medium_id -ne $mediumId -and $role -notin @("adaptation", "transcript", "supplemental")) {
      throw "Source registry '$context' medium does not match work '$workId'."
    }
    $comparisonGroup = Get-RequiredSourceString $source "comparison_group" $context
    Test-StableSourceId $comparisonGroup "$context.comparison_group"
    $priority = Get-ProjectMapValue $source "priority"
    if ($priority -is [bool] -or $priority -isnot [int] -or [int]$priority -lt 1) {
      throw "Source registry '$context.priority' must be a positive integer."
    }
    $sourceAliases = @(Get-SourceStringList $source "aliases" $context)
    foreach ($alias in $sourceAliases) {
      Test-StableSourceId $alias "$context.aliases"
      $aliasKey = $alias.ToLowerInvariant()
      $sourceIdCollision = @($rawSources.Keys | Where-Object { $_.ToLowerInvariant() -eq $aliasKey })
      if ($aliases.ContainsKey($aliasKey) -or $sourceIdCollision.Count -gt 0) {
        throw "Source registry alias '$alias' is duplicated or collides with a source ID."
      }
      $aliases[$aliasKey] = $sourceId
    }
    $evidenceModes = @(Get-SourceStringList $source "evidence_modes" $context)
    foreach ($evidenceMode in $evidenceModes) {
      Test-StableSourceId $evidenceMode "$context.evidence_modes"
    }
    if (-not $source.Contains("resource_bindings")) {
      throw "Source registry '$context.resource_bindings' must be a list."
    }
    $rawBindingsValue = Get-ProjectMapValue $source "resource_bindings"
    $rawBindings = @($rawBindingsValue)
    $bindings = @()
    for ($index = 0; $index -lt $rawBindings.Count; $index += 1) {
      $bindings += Resolve-SourceResourceBinding $ProjectConfig $ResourceConfig $rawBindings[$index] "$context.resource_bindings[$index]"
    }
    $adaptedFrom = ([string](Get-ProjectMapValue $source "adapted_from_source_id" "")).Trim()
    $derivedFrom = ([string](Get-ProjectMapValue $source "derived_from_source_id" "")).Trim()
    $sources[$sourceId] = [pscustomobject]@{
      id = $sourceId
      lifecycle = $lifecycle
      label = Get-RequiredSourceString $source "label" $context
      work_id = $workId
      medium_id = $mediumId
      role = $role
      comparison_group = $comparisonGroup
      priority = [int]$priority
      aliases = @($sourceAliases)
      evidence_modes = @($evidenceModes)
      adapted_from_source_id = if ([string]::IsNullOrWhiteSpace($adaptedFrom)) { $null } else { $adaptedFrom }
      derived_from_source_id = if ([string]::IsNullOrWhiteSpace($derivedFrom)) { $null } else { $derivedFrom }
      resource_bindings = @($bindings)
    }
  }

  foreach ($source in $sources.Values) {
    foreach ($relationshipName in @("adapted_from_source_id", "derived_from_source_id")) {
      $targetId = $source.$relationshipName
      if ($null -eq $targetId) {
        continue
      }
      if (-not $sources.Contains($targetId)) {
        throw "Source registry 'sources.$($source.id).$relationshipName' references unknown source '$targetId'."
      }
      if ($targetId -eq $source.id) {
        throw "Source registry 'sources.$($source.id).$relationshipName' cannot reference itself."
      }
      if ($sources[$targetId].comparison_group -ne $source.comparison_group) {
        throw "Source registry '$($source.id)' and '$targetId' must share a comparison group."
      }
      if ($sources[$targetId].work_id -ne $source.work_id) {
        throw "Source registry '$($source.id)' and '$targetId' must reference the same work."
      }
    }
    if ($source.role -eq "adaptation" -and $null -eq $source.adapted_from_source_id) {
      throw "Source registry adaptation '$($source.id)' requires 'adapted_from_source_id'."
    }
    if ($null -ne $source.adapted_from_source_id) {
      $original = $sources[$source.adapted_from_source_id]
      $outranksOriginal = if ($policy.priority_order -eq "ascending") {
        $source.priority -lt $original.priority
      } else {
        $source.priority -gt $original.priority
      }
      if ($outranksOriginal) {
        throw "Source registry adaptation '$($source.id)' cannot outrank '$($original.id)' under the configured priority order."
      }
    }
  }

  $completeSources = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  foreach ($sourceId in $sources.Keys) {
    $activeSources = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    Test-SourceDerivationCycle $sourceId $sources $activeSources $completeSources
  }

  return [pscustomobject]@{
    path = $registryPath
    schema_version = [int]$schemaVersion
    comparison_policy = $policy
    mediums = $mediums
    series = $series
    works = $works
    work_aliases = $workAliases
    sources = $sources
    source_aliases = $aliases
  }
}
