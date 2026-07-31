$script:ProjectManifestPath = "Project_Config/project.yaml"
$script:SupportedProjectSchemaVersion = 5
$script:AllowedProvenanceModes = @("child-directory", "fixed", "slug-prefix")
$script:StableProjectIdPattern = "^[a-z0-9]+(?:-[a-z0-9]+)*$"

function Test-KnowledgeProjectRoot {
  param([string]$Path)

  return (
    (Test-Path -LiteralPath $Path -PathType Container) -and
    (Test-Path -LiteralPath (Join-Path $Path $script:ProjectManifestPath) -PathType Leaf)
  )
}

function Resolve-KnowledgeProjectRoot {
  param([string]$ExplicitRoot)

  if (-not [string]::IsNullOrWhiteSpace($ExplicitRoot)) {
    $resolved = (Resolve-Path -LiteralPath $ExplicitRoot).Path
    if (-not (Test-KnowledgeProjectRoot $resolved)) {
      throw "Project root is missing required manifest $($script:ProjectManifestPath): $resolved"
    }
    return $resolved
  }

  $checked = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
  $searchStarts = @((Get-Location).Path, $PSScriptRoot)
  foreach ($start in $searchStarts) {
    $current = [System.IO.Path]::GetFullPath($start)
    while ($current) {
      if ($checked.Add($current) -and (Test-KnowledgeProjectRoot $current)) {
        return $current
      }
      $parent = [System.IO.Directory]::GetParent($current)
      if ($null -eq $parent) {
        break
      }
      $current = $parent.FullName
    }
  }

  $starts = ($searchStarts | ForEach-Object { [System.IO.Path]::GetFullPath($_) }) -join ", "
  throw "Could not auto-detect the project root from $starts. Expected manifest: $($script:ProjectManifestPath). Pass the root explicitly."
}

function Import-ProjectYamlModule {
  try {
    Import-Module powershell-yaml -ErrorAction Stop
  } catch {
    throw "Project configuration requires the PowerShell module 'powershell-yaml'. Install it with: Install-Module powershell-yaml -Scope CurrentUser -Force -AllowClobber"
  }
}

function Get-ProjectMapValue {
  param(
    [object]$Map,
    [string]$Key,
    [object]$Default = $null
  )

  if ($null -eq $Map) {
    return $Default
  }
  if ($Map -is [System.Collections.IDictionary]) {
    if ($Map.Contains($Key)) {
      return $Map[$Key]
    }
    return $Default
  }
  $property = $Map.PSObject.Properties[$Key]
  if ($null -ne $property) {
    return $property.Value
  }
  return $Default
}

function Get-RequiredProjectString {
  param(
    [object]$Map,
    [string]$Key,
    [string]$Context
  )

  $value = Get-ProjectMapValue $Map $Key
  if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
    throw "Project manifest '$Context.$Key' must be a non-empty string."
  }
  return ([string]$value).Trim()
}

function Resolve-ProjectManifestPath {
  param(
    [string]$RepoRoot,
    [string]$Value,
    [string]$Key,
    [bool]$MustExist
  )

  if ([System.IO.Path]::IsPathRooted($Value)) {
    throw "Project manifest '$Key' must be repository-relative: $Value"
  }
  $resolvedRoot = [System.IO.Path]::GetFullPath($RepoRoot)
  $resolved = [System.IO.Path]::GetFullPath((Join-Path $resolvedRoot $Value))
  if ($resolved -ne $resolvedRoot -and -not $resolved.StartsWith($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Project manifest '$Key' escapes the repository root: $Value"
  }
  if ($MustExist -and -not (Test-Path -LiteralPath $resolved)) {
    throw "Project manifest '$Key' path does not exist: $resolved"
  }
  return $resolved
}

function Get-KnowledgeProjectConfig {
  param([string]$RepoRoot)

  Import-ProjectYamlModule
  $manifestPath = Join-Path $RepoRoot $script:ProjectManifestPath
  $manifest = ConvertFrom-Yaml -Yaml ([System.IO.File]::ReadAllText($manifestPath, [System.Text.UTF8Encoding]::new($true))) -Ordered
  if ($null -eq $manifest -or -not ($manifest -is [System.Collections.IDictionary])) {
    throw "Project manifest root must be a mapping: $manifestPath"
  }

  $schemaVersion = Get-ProjectMapValue $manifest "schema_version"
  if ([int]$schemaVersion -ne $script:SupportedProjectSchemaVersion) {
    throw "Unsupported project manifest schema_version '$schemaVersion'; expected $($script:SupportedProjectSchemaVersion)."
  }

  $projectId = Get-RequiredProjectString $manifest "project_id" "root"
  $framework = Get-RequiredProjectString $manifest "framework" "root"
  $domain = Get-RequiredProjectString $manifest "domain" "root"
  $paths = Get-ProjectMapValue $manifest "paths"
  if ($null -eq $paths) {
    throw "Project manifest 'paths' must be a mapping."
  }

  $rawContentRoots = @(Get-ProjectMapValue $paths "content_roots")
  if ($rawContentRoots.Count -eq 0) {
    throw "Project manifest 'paths.content_roots' must be a non-empty list."
  }
  $contentRoots = @()
  $configuredRootIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
  for ($index = 0; $index -lt $rawContentRoots.Count; $index += 1) {
    $entry = $rawContentRoots[$index]
    $context = "paths.content_roots[$index]"
    $contentRootId = Get-RequiredProjectString $entry "id" $context
    if ($contentRootId -notmatch $script:StableProjectIdPattern) {
      throw "Project manifest '$context.id' must be a lowercase kebab-case stable ID: $contentRootId"
    }
    if (-not $configuredRootIds.Add($contentRootId)) {
      throw "Project manifest '$context.id' duplicates content-root ID '$contentRootId'."
    }
    $pathValue = Get-RequiredProjectString $entry "path" $context
    $provenanceMode = Get-RequiredProjectString $entry "provenance_mode" $context
    if ($script:AllowedProvenanceModes -notcontains $provenanceMode) {
      throw "Project manifest '$context.provenance_mode' must be one of: $($script:AllowedProvenanceModes -join ', ')."
    }
    $provenanceLabel = [string](Get-ProjectMapValue $entry "provenance_label" "")
    if ($provenanceMode -eq "fixed" -and [string]::IsNullOrWhiteSpace($provenanceLabel)) {
      throw "Project manifest '$context.provenance_label' is required for fixed provenance."
    }
    $contentRoots += [pscustomobject]@{
      id = $contentRootId
      relative_path = $pathValue
      path = Resolve-ProjectManifestPath $RepoRoot $pathValue "$context.path" $true
      provenance_mode = $provenanceMode
      provenance_label = $provenanceLabel.Trim()
    }
  }

  $rawResourceRoots = @(Get-ProjectMapValue $paths "resource_roots")
  if ($rawResourceRoots.Count -eq 0) {
    throw "Project manifest 'paths.resource_roots' must be a non-empty list."
  }
  $resourceRoots = @()
  for ($index = 0; $index -lt $rawResourceRoots.Count; $index += 1) {
    $entry = $rawResourceRoots[$index]
    $context = "paths.resource_roots[$index]"
    $resourceRootId = Get-RequiredProjectString $entry "id" $context
    if ($resourceRootId -notmatch $script:StableProjectIdPattern) {
      throw "Project manifest '$context.id' must be a lowercase kebab-case stable ID: $resourceRootId"
    }
    if (-not $configuredRootIds.Add($resourceRootId)) {
      throw "Project manifest '$context.id' duplicates configured root ID '$resourceRootId'."
    }
    $required = Get-ProjectMapValue $entry "required"
    if ($required -isnot [bool]) {
      throw "Project manifest '$context.required' must be true or false."
    }
    $pathValue = Get-RequiredProjectString $entry "path" $context
    $resourceRoots += [pscustomobject]@{
      id = $resourceRootId
      relative_path = $pathValue
      path = Resolve-ProjectManifestPath $RepoRoot $pathValue "$context.path" ([bool]$required)
      required = [bool]$required
    }
  }

  $visualization = Get-ProjectMapValue $paths "visualization"
  if ($null -eq $visualization) {
    throw "Project manifest 'paths.visualization' must be a mapping."
  }
  $cleanup = Get-ProjectMapValue $paths "cleanup"
  if ($null -eq $cleanup) {
    throw "Project manifest 'paths.cleanup' must be a mapping."
  }
  $registries = Get-ProjectMapValue $manifest "registries"
  if ($null -eq $registries) {
    throw "Project manifest 'registries' must be a mapping."
  }

  return [pscustomobject]@{
    root = [System.IO.Path]::GetFullPath($RepoRoot)
    manifest_path = $manifestPath
    schema_version = [int]$schemaVersion
    project_id = $projectId
    framework = $framework
    domain = $domain
    content_roots = @($contentRoots)
    resource_roots = @($resourceRoots)
    qa_export = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $paths "qa_export" "paths") "paths.qa_export" $false
    visualization_python_helper = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $visualization "python_helper" "paths.visualization") "paths.visualization.python_helper" $true
    visualization_powershell_helper = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $visualization "powershell_helper" "paths.visualization") "paths.visualization.powershell_helper" $true
    visualization_render_settings = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $visualization "render_settings" "paths.visualization") "paths.visualization.render_settings" $true
    visualization_puppeteer_config = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $visualization "puppeteer_config" "paths.visualization") "paths.visualization.puppeteer_config" $true
    cleanup_python_helper = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $cleanup "python_helper" "paths.cleanup") "paths.cleanup.python_helper" $true
    cleanup_powershell_helper = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $cleanup "powershell_helper" "paths.cleanup") "paths.cleanup.powershell_helper" $true
    lookup_keys_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "lookup_keys" "registries") "registries.lookup_keys" $true
    schema_packs_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "schema_packs" "registries") "registries.schema_packs" $true
    taxonomy_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "taxonomy" "registries") "registries.taxonomy" $true
    resources_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "resources" "registries") "registries.resources" $true
    sources_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "sources" "registries") "registries.sources" $true
    entities_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "entities" "registries") "registries.entities" $true
  }
}
