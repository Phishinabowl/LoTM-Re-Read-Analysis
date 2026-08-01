$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) {
  . $projectConfigHelper
}

$script:SupportedTaxonomySchemaVersion = 2
$script:AllowedTaxonomyLifecycles = @("active", "deferred")
$script:AllowedCategoryPolicies = @("required", "optional", "forbidden")
$script:AllowedPathStrategies = @("category-file", "category-subject-record", "root-file", "fixed-file")
$script:AllowedMetadataTypeModes = @("category", "fixed", "none")
$script:AllowedSlugModes = @("category", "record")
$script:StableTaxonomyIdPattern = "^[a-z0-9]+(?:-[a-z0-9]+)*$"

function Test-StableTaxonomyId {
  param(
    [string]$Value,
    [string]$Context
  )

  if ($Value -notmatch $script:StableTaxonomyIdPattern) {
    throw "Taxonomy registry '$Context' must be a lowercase kebab-case stable ID: $Value"
  }
}

function Get-RequiredTaxonomyString {
  param(
    [object]$Map,
    [string]$Key,
    [string]$Context
  )

  $value = Get-ProjectMapValue $Map $Key
  if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
    throw "Taxonomy registry '$Context.$Key' must be a non-empty string."
  }
  return ([string]$value).Trim()
}

function Get-RequiredTaxonomyBoolean {
  param(
    [object]$Map,
    [string]$Key,
    [string]$Context
  )

  $value = Get-ProjectMapValue $Map $Key
  if ($value -isnot [bool]) {
    throw "Taxonomy registry '$Context.$Key' must be true or false."
  }
  return [bool]$value
}

function Test-TaxonomyRegex {
  param(
    [string]$Value,
    [string]$Context
  )

  try {
    $null = [regex]::new($Value)
  } catch {
    throw "Taxonomy registry '$Context' is invalid: $($_.Exception.Message)"
  }
}

function Resolve-TaxonomyFolder {
  param(
    [object]$ProjectConfig,
    [string]$ContentRootId,
    [string]$Value,
    [string]$Context
  )

  $contentRoot = @($ProjectConfig.content_roots | Where-Object { $_.id -eq $ContentRootId })
  if ($contentRoot.Count -ne 1) {
    throw "Taxonomy registry '$Context' references unknown content root '$ContentRootId'."
  }
  if ([System.IO.Path]::IsPathRooted($Value)) {
    throw "Taxonomy registry '$Context' must be relative: $Value"
  }

  $rootPath = [System.IO.Path]::GetFullPath($contentRoot[0].path)
  $folder = [System.IO.Path]::GetFullPath((Join-Path $rootPath $Value))
  if ($folder -ne $rootPath -and -not $folder.StartsWith($rootPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Taxonomy registry '$Context' escapes content root '$ContentRootId': $Value"
  }
  return $folder
}

function Resolve-TaxonomyTemplate {
  param(
    [object]$ProjectConfig,
    [string]$Value,
    [string]$Context
  )

  $null = Resolve-ProjectManifestPath $ProjectConfig.root $Value $Context $true
  return $Value
}

function ConvertTo-ContentTypeConfig {
  param(
    [string]$ContentTypeId,
    [object]$RawContentType,
    [object]$ProjectConfig
  )

  $context = "content_types.$ContentTypeId"
  Test-StableTaxonomyId $ContentTypeId $context
  if ($null -eq $RawContentType -or -not ($RawContentType -is [System.Collections.IDictionary])) {
    throw "Taxonomy registry '$context' must be a mapping."
  }

  $lifecycle = Get-RequiredTaxonomyString $RawContentType "lifecycle" $context
  if ($script:AllowedTaxonomyLifecycles -notcontains $lifecycle) {
    throw "Taxonomy registry '$context.lifecycle' must be one of: $($script:AllowedTaxonomyLifecycles -join ', ')."
  }
  $canonicalPagesEnabled = Get-RequiredTaxonomyBoolean $RawContentType "canonical_pages_enabled" $context
  if ($lifecycle -eq "deferred" -and $canonicalPagesEnabled) {
    throw "Taxonomy registry '$context' cannot enable canonical pages while deferred."
  }
  if ($lifecycle -eq "active" -and -not $canonicalPagesEnabled) {
    throw "Taxonomy registry active content type '$ContentTypeId' must enable canonical pages."
  }

  $contentRootId = Get-RequiredTaxonomyString $RawContentType "content_root_id" $context
  Test-StableTaxonomyId $contentRootId "$context.content_root_id"
  if (@($ProjectConfig.content_roots | Where-Object { $_.id -eq $contentRootId }).Count -ne 1) {
    throw "Taxonomy registry '$context.content_root_id' references unknown content root '$contentRootId'."
  }

  $categoryPolicy = Get-RequiredTaxonomyString $RawContentType "category_policy" $context
  if ($script:AllowedCategoryPolicies -notcontains $categoryPolicy) {
    throw "Taxonomy registry '$context.category_policy' must be one of: $($script:AllowedCategoryPolicies -join ', ')."
  }
  $pathStrategy = Get-RequiredTaxonomyString $RawContentType "path_strategy" $context
  if ($script:AllowedPathStrategies -notcontains $pathStrategy) {
    throw "Taxonomy registry '$context.path_strategy' must be one of: $($script:AllowedPathStrategies -join ', ')."
  }
  $metadataTypeMode = Get-RequiredTaxonomyString $RawContentType "metadata_type_mode" $context
  if ($script:AllowedMetadataTypeModes -notcontains $metadataTypeMode) {
    throw "Taxonomy registry '$context.metadata_type_mode' must be one of: $($script:AllowedMetadataTypeModes -join ', ')."
  }
  $slugMode = Get-RequiredTaxonomyString $RawContentType "slug_mode" $context
  if ($script:AllowedSlugModes -notcontains $slugMode) {
    throw "Taxonomy registry '$context.slug_mode' must be one of: $($script:AllowedSlugModes -join ', ')."
  }

  if ($categoryPolicy -eq "forbidden" -and $pathStrategy -notin @("root-file", "fixed-file")) {
    throw "Taxonomy registry '$context' with forbidden categories must use 'root-file' or 'fixed-file' path strategy."
  }
  if ($slugMode -eq "category" -and $categoryPolicy -eq "forbidden") {
    throw "Taxonomy registry '$context' cannot use category slugs when categories are forbidden."
  }
  if ($metadataTypeMode -eq "category" -and $categoryPolicy -eq "forbidden") {
    throw "Taxonomy registry '$context' cannot use category metadata types when categories are forbidden."
  }

  $metadataType = ([string](Get-ProjectMapValue $RawContentType "metadata_type" "")).Trim()
  if ($metadataTypeMode -eq "fixed" -and [string]::IsNullOrWhiteSpace($metadataType)) {
    throw "Taxonomy registry '$context.metadata_type' is required for fixed mode."
  }

  $recordSlugPrefix = ([string](Get-ProjectMapValue $RawContentType "record_slug_prefix" "")).Trim()
  $recordSlugPattern = ([string](Get-ProjectMapValue $RawContentType "record_slug_pattern" "")).Trim()
  if ($slugMode -eq "record") {
    if (-not [string]::IsNullOrWhiteSpace($recordSlugPrefix)) {
      Test-StableTaxonomyId $recordSlugPrefix "$context.record_slug_prefix"
    }
    if ([string]::IsNullOrWhiteSpace($recordSlugPattern)) {
      throw "Taxonomy registry '$context.record_slug_pattern' is required for record slug mode."
    }
    Test-TaxonomyRegex $recordSlugPattern "$context.record_slug_pattern"
  }

  $defaultTemplateValue = ([string](Get-ProjectMapValue $RawContentType "default_template" "")).Trim()
  $defaultTemplate = if ([string]::IsNullOrWhiteSpace($defaultTemplateValue)) {
    $null
  } else {
    Resolve-TaxonomyTemplate $ProjectConfig $defaultTemplateValue "$context.default_template"
  }
  $recordPathValue = ([string](Get-ProjectMapValue $RawContentType "record_path" "")).Trim()
  $recordPath = $null
  if ($pathStrategy -eq "fixed-file") {
    if ([string]::IsNullOrWhiteSpace($recordPathValue)) {
      throw "Taxonomy registry '$context.record_path' is required for fixed-file."
    }
    $resolvedRecordPath = Resolve-TaxonomyFolder $ProjectConfig $contentRootId $recordPathValue "$context.record_path"
    if (-not (Test-Path -LiteralPath $resolvedRecordPath -PathType Leaf)) {
      throw "Taxonomy registry '$context.record_path' does not exist: $resolvedRecordPath"
    }
    $recordPath = $recordPathValue
  } elseif (-not [string]::IsNullOrWhiteSpace($recordPathValue)) {
    throw "Taxonomy registry '$context.record_path' is only valid for fixed-file."
  }
  return [pscustomobject]@{
    id = $ContentTypeId
    lifecycle = $lifecycle
    label = Get-RequiredTaxonomyString $RawContentType "label" $context
    plural_label = Get-RequiredTaxonomyString $RawContentType "plural_label" $context
    canonical_pages_enabled = [bool]$canonicalPagesEnabled
    content_root_id = $contentRootId
    category_policy = $categoryPolicy
    path_strategy = $pathStrategy
    metadata_type_mode = $metadataTypeMode
    slug_mode = $slugMode
    default_template = $defaultTemplate
    qa_page_enabled = Get-RequiredTaxonomyBoolean $RawContentType "qa_page_enabled" $context
    graph_enabled = Get-RequiredTaxonomyBoolean $RawContentType "graph_enabled" $context
    metadata_type = $metadataType
    record_slug_prefix = $recordSlugPrefix
    record_slug_pattern = $recordSlugPattern
    record_path = $recordPath
  }
}

function ConvertTo-CategoryConfig {
  param(
    [string]$CategoryId,
    [object]$RawCategory,
    [object]$ProjectConfig,
    [System.Collections.IDictionary]$ContentTypes
  )

  $context = "categories.$CategoryId"
  Test-StableTaxonomyId $CategoryId $context
  if ($null -eq $RawCategory -or -not ($RawCategory -is [System.Collections.IDictionary])) {
    throw "Taxonomy registry '$context' must be a mapping."
  }

  $lifecycle = Get-RequiredTaxonomyString $RawCategory "lifecycle" $context
  if ($script:AllowedTaxonomyLifecycles -notcontains $lifecycle) {
    throw "Taxonomy registry '$context.lifecycle' must be one of: $($script:AllowedTaxonomyLifecycles -join ', ')."
  }
  $canonicalPagesEnabled = Get-RequiredTaxonomyBoolean $RawCategory "canonical_pages_enabled" $context
  $label = Get-RequiredTaxonomyString $RawCategory "label" $context
  $pluralLabel = Get-RequiredTaxonomyString $RawCategory "plural_label" $context
  if ($lifecycle -eq "deferred") {
    if ($canonicalPagesEnabled) {
      throw "Taxonomy registry '$context' cannot enable canonical pages while deferred."
    }
    return [pscustomobject]@{
      id = $CategoryId
      lifecycle = $lifecycle
      label = $label
      plural_label = $pluralLabel
      canonical_pages_enabled = $false
      metadata_type = ""
      subject_slug_prefix = ""
      subject_slug_pattern = ""
      graph_class = ""
      placements = [ordered]@{}
    }
  }
  if (-not $canonicalPagesEnabled) {
    throw "Taxonomy registry active category '$CategoryId' must enable canonical pages."
  }

  $subjectSlugPrefix = Get-RequiredTaxonomyString $RawCategory "subject_slug_prefix" $context
  Test-StableTaxonomyId $subjectSlugPrefix "$context.subject_slug_prefix"
  $subjectSlugPattern = Get-RequiredTaxonomyString $RawCategory "subject_slug_pattern" $context
  Test-TaxonomyRegex $subjectSlugPattern "$context.subject_slug_pattern"
  $graphClass = Get-RequiredTaxonomyString $RawCategory "graph_class" $context
  Test-StableTaxonomyId $graphClass "$context.graph_class"

  $rawPlacements = Get-ProjectMapValue $RawCategory "placements"
  if ($null -eq $rawPlacements -or -not ($rawPlacements -is [System.Collections.IDictionary])) {
    throw "Taxonomy registry '$context.placements' must be a mapping."
  }
  $placements = [ordered]@{}
  foreach ($contentTypeId in $rawPlacements.Keys) {
    $placementContext = "$context.placements.$contentTypeId"
    if (-not $ContentTypes.Contains($contentTypeId)) {
      throw "Taxonomy registry '$placementContext' references unknown content type."
    }
    $contentType = $ContentTypes[$contentTypeId]
    if ($contentType.category_policy -eq "forbidden") {
      throw "Taxonomy registry '$placementContext' references content type that forbids categories."
    }
    $rawPlacement = $rawPlacements[$contentTypeId]
    if ($null -eq $rawPlacement -or -not ($rawPlacement -is [System.Collections.IDictionary])) {
      throw "Taxonomy registry '$placementContext' must be a mapping."
    }
    $relativeFolder = Get-RequiredTaxonomyString $rawPlacement "relative_folder" $placementContext
    $folder = Resolve-TaxonomyFolder $ProjectConfig $contentType.content_root_id $relativeFolder "$placementContext.relative_folder"
    $templateValue = ([string](Get-ProjectMapValue $rawPlacement "template" "")).Trim()
    $template = if ([string]::IsNullOrWhiteSpace($templateValue)) {
      $contentType.default_template
    } else {
      Resolve-TaxonomyTemplate $ProjectConfig $templateValue "$placementContext.template"
    }
    if ($null -eq $template) {
      throw "Taxonomy registry '$placementContext' requires a template because content type '$contentTypeId' has no default template."
    }
    $placements[$contentTypeId] = [pscustomobject]@{
      content_type_id = $contentTypeId
      relative_folder = $relativeFolder
      folder = $folder
      template = $template
    }
  }

  $requiredCategoryTypes = @($ContentTypes.Values | Where-Object {
    $_.lifecycle -eq "active" -and $_.category_policy -eq "required"
  })
  $missingRequired = @($requiredCategoryTypes | Where-Object { -not $placements.Contains($_.id) })
  if ($missingRequired.Count -gt 0) {
    throw "Taxonomy registry '$context.placements' is missing required content type(s): $(($missingRequired.id | Sort-Object) -join ', ')."
  }

  return [pscustomobject]@{
    id = $CategoryId
    lifecycle = $lifecycle
    label = $label
    plural_label = $pluralLabel
    canonical_pages_enabled = $true
    metadata_type = Get-RequiredTaxonomyString $RawCategory "metadata_type" $context
    subject_slug_prefix = $subjectSlugPrefix
    subject_slug_pattern = $subjectSlugPattern
    graph_class = $graphClass
    placements = $placements
  }
}

function Assert-UniqueTaxonomyValue {
  param(
    [object[]]$Records,
    [string]$Property,
    [string]$Label
  )

  $seen = @{}
  foreach ($record in $Records) {
    $value = [string]$record.$Property
    $key = $value.ToLowerInvariant()
    if ($seen.ContainsKey($key)) {
      throw "Taxonomy registry duplicates $Label '$value' between '$($seen[$key])' and '$($record.id)'."
    }
    $seen[$key] = $record.id
  }
}

function Get-KnowledgeTaxonomyConfig {
  param([object]$ProjectConfig)

  Import-ProjectYamlModule
  $registryPath = $ProjectConfig.taxonomy_registry
  $registry = ConvertFrom-Yaml -Yaml ([System.IO.File]::ReadAllText($registryPath, [System.Text.UTF8Encoding]::new($true))) -Ordered
  if ($null -eq $registry -or -not ($registry -is [System.Collections.IDictionary])) {
    throw "Taxonomy registry root must be a mapping: $registryPath"
  }
  $schemaVersion = Get-ProjectMapValue $registry "schema_version"
  if ([int]$schemaVersion -ne $script:SupportedTaxonomySchemaVersion) {
    throw "Unsupported taxonomy schema_version '$schemaVersion'; expected $($script:SupportedTaxonomySchemaVersion)."
  }

  $rawContentTypes = Get-ProjectMapValue $registry "content_types"
  if ($null -eq $rawContentTypes -or -not ($rawContentTypes -is [System.Collections.IDictionary])) {
    throw "Taxonomy registry 'content_types' must be a mapping."
  }
  $contentTypes = [ordered]@{}
  foreach ($contentTypeId in $rawContentTypes.Keys) {
    $contentTypes[$contentTypeId] = ConvertTo-ContentTypeConfig $contentTypeId $rawContentTypes[$contentTypeId] $ProjectConfig
  }
  Assert-UniqueTaxonomyValue @($contentTypes.Values | Where-Object {
    $_.lifecycle -eq "active" -and $null -ne $_.record_path
  }) "record_path" "fixed record path"

  $rawCategories = Get-ProjectMapValue $registry "categories"
  if ($null -eq $rawCategories -or -not ($rawCategories -is [System.Collections.IDictionary])) {
    throw "Taxonomy registry 'categories' must be a mapping."
  }
  $categories = [ordered]@{}
  foreach ($categoryId in $rawCategories.Keys) {
    if ($contentTypes.Contains($categoryId)) {
      throw "Taxonomy registry ID '$categoryId' cannot be both a category and content type."
    }
    $categories[$categoryId] = ConvertTo-CategoryConfig $categoryId $rawCategories[$categoryId] $ProjectConfig $contentTypes
  }

  $activeCategories = @($categories.Values | Where-Object lifecycle -eq "active")
  Assert-UniqueTaxonomyValue $activeCategories "metadata_type" "category metadata type"
  Assert-UniqueTaxonomyValue $activeCategories "subject_slug_prefix" "subject slug prefix"
  Assert-UniqueTaxonomyValue $activeCategories "graph_class" "graph class"

  $seenPlacements = @{}
  foreach ($category in $activeCategories) {
    foreach ($contentTypeId in $category.placements.Keys) {
      $placement = $category.placements[$contentTypeId]
      $key = "$contentTypeId|$(([string]$placement.relative_folder).ToLowerInvariant())"
      if ($seenPlacements.ContainsKey($key)) {
        throw "Taxonomy registry duplicates '$contentTypeId' folder '$($placement.relative_folder)' between '$($seenPlacements[$key])' and '$($category.id)'."
      }
      $seenPlacements[$key] = $category.id
    }
  }

  return [pscustomobject]@{
    path = $registryPath
    schema_version = [int]$schemaVersion
    categories = $categories
    content_types = $contentTypes
  }
}

function Get-TaxonomyQaPageContentRoots {
  param(
    [object]$ProjectConfig,
    [object]$TaxonomyConfig
  )

  $enabledRootIds = @($TaxonomyConfig.content_types.Values | Where-Object {
    $_.lifecycle -eq "active" -and $_.qa_page_enabled
  } | ForEach-Object { $_.content_root_id })
  return @($ProjectConfig.content_roots | Where-Object { $enabledRootIds -contains $_.id })
}

function Get-KnowledgeTaxonomyReconciliationTargetTypes {
  return @("content-type", "category")
}

function Get-KnowledgeTaxonomyReconciliationTargets {
  param([object]$TaxonomyConfig)
  return [ordered]@{"content-type"=$TaxonomyConfig.content_types;category=$TaxonomyConfig.categories}
}

function Get-KnowledgeTaxonomyReconciliationProvider {
  param([object]$TaxonomyConfig)
  return [pscustomobject]@{provider_id="taxonomy";targets=(Get-KnowledgeTaxonomyReconciliationTargets $TaxonomyConfig);aliases=[ordered]@{}}
}

function Get-KnowledgeTaxonomyReconciliationTarget {
  param([object]$TaxonomyConfig, [string]$TargetType, [string]$TargetId)
  $targets = switch ($TargetType) {
    "content-type" { $TaxonomyConfig.content_types; break }
    "category" { $TaxonomyConfig.categories; break }
    default { throw "Unsupported taxonomy reconciliation target type '$TargetType'." }
  }
  if (-not $targets.Contains($TargetId)) { throw "Unknown $TargetType '$TargetId'." }
  return $targets[$TargetId]
}
