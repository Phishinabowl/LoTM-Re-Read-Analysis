$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-KnowledgeProjectConfig -ErrorAction SilentlyContinue)) {
  . $projectConfigHelper
}

$script:SupportedResourceSchemaVersion = 1
$script:AllowedResourceLifecycles = @("active", "deferred")
$script:AllowedResourceAuthorities = @("canonical", "supporting", "evidence", "operational", "generated", "temporary")
$script:AllowedResourceTrackingModes = @("tracked", "ignored", "mixed")

function Get-RequiredResourceString {
  param([object]$Map, [string]$Key, [string]$Context)

  $value = Get-ProjectMapValue $Map $Key
  if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
    throw "Resource registry '$Context.$Key' must be a non-empty string."
  }
  return ([string]$value).Trim()
}

function Get-RequiredResourceBoolean {
  param([object]$Map, [string]$Key, [string]$Context)

  $value = Get-ProjectMapValue $Map $Key
  if ($value -isnot [bool]) {
    throw "Resource registry '$Context.$Key' must be true or false."
  }
  return [bool]$value
}

function Test-StableResourceId {
  param([string]$Value, [string]$Context)

  if ($Value -notmatch $script:StableProjectIdPattern) {
    throw "Resource registry '$Context' must be a lowercase kebab-case stable ID: $Value"
  }
}

function Resolve-ResourcePlacement {
  param(
    [object]$ProjectConfig,
    [string]$RootId,
    [string]$Value,
    [string]$Context,
    [bool]$Required
  )

  $resourceRoot = @($ProjectConfig.resource_roots | Where-Object { $_.id -eq $RootId })
  if ($resourceRoot.Count -ne 1) {
    throw "Resource registry '$Context' references unknown resource root '$RootId'."
  }
  if ([System.IO.Path]::IsPathRooted($Value)) {
    throw "Resource registry '$Context' must be relative: $Value"
  }
  $rootPath = [System.IO.Path]::GetFullPath($resourceRoot[0].path)
  $path = [System.IO.Path]::GetFullPath((Join-Path $rootPath $Value))
  if ($path -ne $rootPath -and -not $path.StartsWith($rootPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Resource registry '$Context' escapes resource root '$RootId': $Value"
  }
  if ($Required -and -not (Test-Path -LiteralPath $path)) {
    throw "Resource registry '$Context' path does not exist: $path"
  }
  return $path
}

function Get-KnowledgeResourceConfig {
  param([object]$ProjectConfig)

  Import-ProjectYamlModule
  $registryPath = $ProjectConfig.resources_registry
  $registry = ConvertFrom-Yaml -Yaml ([System.IO.File]::ReadAllText($registryPath, [System.Text.UTF8Encoding]::new($true))) -Ordered
  if ($null -eq $registry -or -not ($registry -is [System.Collections.IDictionary])) {
    throw "Resource registry root must be a mapping: $registryPath"
  }
  $schemaVersion = Get-ProjectMapValue $registry "schema_version"
  if ([int]$schemaVersion -ne $script:SupportedResourceSchemaVersion) {
    throw "Unsupported resource schema_version '$schemaVersion'; expected $($script:SupportedResourceSchemaVersion)."
  }

  $rawKinds = Get-ProjectMapValue $registry "resource_kinds"
  if ($null -eq $rawKinds -or -not ($rawKinds -is [System.Collections.IDictionary])) {
    throw "Resource registry 'resource_kinds' must be a mapping."
  }
  $kinds = [ordered]@{}
  foreach ($kindId in $rawKinds.Keys) {
    $context = "resource_kinds.$kindId"
    Test-StableResourceId $kindId $context
    $rawKind = $rawKinds[$kindId]
    if ($null -eq $rawKind -or -not ($rawKind -is [System.Collections.IDictionary])) {
      throw "Resource registry '$context' must be a mapping."
    }
    $kinds[$kindId] = [pscustomobject]@{
      id = $kindId
      label = Get-RequiredResourceString $rawKind "label" $context
      plural_label = Get-RequiredResourceString $rawKind "plural_label" $context
    }
  }

  $rawTypes = Get-ProjectMapValue $registry "resource_types"
  if ($null -eq $rawTypes -or -not ($rawTypes -is [System.Collections.IDictionary])) {
    throw "Resource registry 'resource_types' must be a mapping."
  }
  $types = [ordered]@{}
  $seenPlacements = @{}
  foreach ($typeId in $rawTypes.Keys) {
    $context = "resource_types.$typeId"
    Test-StableResourceId $typeId $context
    $rawType = $rawTypes[$typeId]
    if ($null -eq $rawType -or -not ($rawType -is [System.Collections.IDictionary])) {
      throw "Resource registry '$context' must be a mapping."
    }
    $lifecycle = Get-RequiredResourceString $rawType "lifecycle" $context
    if ($script:AllowedResourceLifecycles -notcontains $lifecycle) {
      throw "Resource registry '$context.lifecycle' must be one of: $($script:AllowedResourceLifecycles -join ', ')."
    }
    $kindId = Get-RequiredResourceString $rawType "kind_id" $context
    if (-not $kinds.Contains($kindId)) {
      throw "Resource registry '$context.kind_id' references unknown kind '$kindId'."
    }
    $authority = Get-RequiredResourceString $rawType "authority" $context
    if ($script:AllowedResourceAuthorities -notcontains $authority) {
      throw "Resource registry '$context.authority' must be one of: $($script:AllowedResourceAuthorities -join ', ')."
    }
    $rawPlacements = @(Get-ProjectMapValue $rawType "placements")
    if ($lifecycle -eq "active" -and $rawPlacements.Count -eq 0) {
      throw "Resource registry '$context.placements' must be a non-empty list for active resource types."
    }
    $placements = @()
    for ($index = 0; $index -lt $rawPlacements.Count; $index += 1) {
      $placement = $rawPlacements[$index]
      $placementContext = "$context.placements[$index]"
      if ($null -eq $placement -or -not ($placement -is [System.Collections.IDictionary])) {
        throw "Resource registry '$placementContext' must be a mapping."
      }
      $rootId = Get-RequiredResourceString $placement "root_id" $placementContext
      Test-StableResourceId $rootId "$placementContext.root_id"
      $tracking = Get-RequiredResourceString $placement "tracking" $placementContext
      if ($script:AllowedResourceTrackingModes -notcontains $tracking) {
        throw "Resource registry '$placementContext.tracking' must be one of: $($script:AllowedResourceTrackingModes -join ', ')."
      }
      $required = Get-RequiredResourceBoolean $placement "required" $placementContext
      $relativePath = Get-RequiredResourceString $placement "relative_path" $placementContext
      $path = Resolve-ResourcePlacement $ProjectConfig $rootId $relativePath "$placementContext.relative_path" $required
      $placementKey = "$rootId|$($relativePath.ToLowerInvariant())"
      if ($seenPlacements.ContainsKey($placementKey)) {
        throw "Resource registry duplicates placement '$rootId/$relativePath' between '$($seenPlacements[$placementKey])' and '$typeId'."
      }
      $seenPlacements[$placementKey] = $typeId
      $placements += [pscustomobject]@{
        root_id = $rootId
        relative_path = $relativePath
        path = $path
        tracking = $tracking
        required = $required
      }
    }
    $types[$typeId] = [pscustomobject]@{
      id = $typeId
      lifecycle = $lifecycle
      label = Get-RequiredResourceString $rawType "label" $context
      plural_label = Get-RequiredResourceString $rawType "plural_label" $context
      kind_id = $kindId
      authority = $authority
      editor_enabled = Get-RequiredResourceBoolean $rawType "editor_enabled" $context
      placements = @($placements)
    }
  }

  return [pscustomobject]@{
    path = $registryPath
    schema_version = [int]$schemaVersion
    kinds = $kinds
    types = $types
  }
}

function Get-KnowledgeResourceReconciliationTargetTypes {
  return @("resource-kind", "resource-type")
}

function Get-KnowledgeResourceReconciliationTargets {
  param([object]$ResourceConfig)
  return [ordered]@{"resource-kind"=$ResourceConfig.kinds;"resource-type"=$ResourceConfig.types}
}

function Get-KnowledgeResourceReconciliationProvider {
  param([object]$ResourceConfig)
  return [pscustomobject]@{provider_id="resource";targets=(Get-KnowledgeResourceReconciliationTargets $ResourceConfig);aliases=[ordered]@{}}
}

function Get-KnowledgeResourceReconciliationTarget {
  param([object]$ResourceConfig, [string]$TargetType, [string]$TargetId)
  $targets = switch ($TargetType) {
    "resource-kind" { $ResourceConfig.kinds; break }
    "resource-type" { $ResourceConfig.types; break }
    default { throw "Unsupported resource reconciliation target type '$TargetType'." }
  }
  if (-not $targets.Contains($TargetId)) { throw "Unknown $TargetType '$TargetId'." }
  return $targets[$TargetId]
}
