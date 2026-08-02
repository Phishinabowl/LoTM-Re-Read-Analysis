$script:ProjectManifestPath = "Project_Config/project.yaml"
$script:SupportedProjectSchemaVersion = 9
$script:AllowedProvenanceModes = @("child-directory", "fixed", "slug-prefix")
$script:StableProjectIdPattern = "^[a-z0-9]+(?:-[a-z0-9]+)*$"
$strictYamlHelper = Join-Path $PSScriptRoot "Strict-Yaml.ps1"
if (-not (Get-Command ConvertFrom-KnowledgeYamlFile -ErrorAction SilentlyContinue)) {
    . $strictYamlHelper
}

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
    Import-KnowledgeYamlModule
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
    $manifest = ConvertFrom-KnowledgeYamlFile $manifestPath $script:SupportedProjectSchemaVersion "project manifest"
    Assert-KnowledgeMapKeys $manifest @("schema_version", "project_id", "framework", "domain", "paths", "registries") "Project manifest root"

    $schemaVersion = Get-ProjectMapValue $manifest "schema_version"
    if ($schemaVersion -isnot [int] -or $schemaVersion -ne $script:SupportedProjectSchemaVersion) {
        throw "Unsupported project manifest schema_version '$schemaVersion'; expected $($script:SupportedProjectSchemaVersion)."
    }

    $projectId = Get-RequiredProjectString $manifest "project_id" "root"
    $framework = Get-RequiredProjectString $manifest "framework" "root"
    $domain = Get-RequiredProjectString $manifest "domain" "root"
    $paths = Get-ProjectMapValue $manifest "paths"
    if ($null -eq $paths) {
        throw "Project manifest 'paths' must be a mapping."
    }
    Assert-KnowledgeMapKeys $paths @("content_roots", "resource_roots", "qa_export", "visualization", "cleanup") "Project manifest 'paths'"

    $rawContentRoots = @(Get-ProjectMapValue $paths "content_roots")
    if ($rawContentRoots.Count -eq 0) {
        throw "Project manifest 'paths.content_roots' must be a non-empty list."
    }
    $contentRoots = @()
    $configuredRootIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    for ($index = 0; $index -lt $rawContentRoots.Count; $index += 1) {
        $entry = $rawContentRoots[$index]
        $context = "paths.content_roots[$index]"
        Assert-KnowledgeMapKeys $entry @("id", "path", "provenance_mode", "provenance_label") "Project manifest '$context'"
        $contentRootId = Get-RequiredProjectString $entry "id" $context
        if ($contentRootId -cnotmatch $script:StableProjectIdPattern) {
            throw "Project manifest '$context.id' must be a lowercase kebab-case stable ID: $contentRootId"
        }
        if (-not $configuredRootIds.Add($contentRootId)) {
            throw "Project manifest '$context.id' duplicates content-root ID '$contentRootId'."
        }
        $pathValue = Get-RequiredProjectString $entry "path" $context
        $provenanceMode = Get-RequiredProjectString $entry "provenance_mode" $context
        if ($script:AllowedProvenanceModes -cnotcontains $provenanceMode) {
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
        Assert-KnowledgeMapKeys $entry @("id", "path", "required") "Project manifest '$context'"
        $resourceRootId = Get-RequiredProjectString $entry "id" $context
        if ($resourceRootId -cnotmatch $script:StableProjectIdPattern) {
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
    Assert-KnowledgeMapKeys $visualization @("python_helper", "powershell_helper", "render_settings", "puppeteer_config") "Project manifest 'paths.visualization'"
    $cleanup = Get-ProjectMapValue $paths "cleanup"
    if ($null -eq $cleanup) {
        throw "Project manifest 'paths.cleanup' must be a mapping."
    }
    Assert-KnowledgeMapKeys $cleanup @("python_helper", "powershell_helper") "Project manifest 'paths.cleanup'"
    $registries = Get-ProjectMapValue $manifest "registries"
    if ($null -eq $registries) {
        throw "Project manifest 'registries' must be a mapping."
    }
    $registryKeys = @(
        "lookup_keys"
        "schema_packs"
        "taxonomy"
        "resources"
        "sources"
        "entities"
        "reconciliation"
        "provenance"
        "chronology"
        "occurrences"
    )
    Assert-KnowledgeMapKeys $registries $registryKeys "Project manifest 'registries'"

    $visualizationPowershellHelper = Resolve-ProjectManifestPath $RepoRoot (
        Get-RequiredProjectString $visualization "powershell_helper" "paths.visualization"
    ) "paths.visualization.powershell_helper" $true
    $visualizationRenderSettings = Resolve-ProjectManifestPath $RepoRoot (
        Get-RequiredProjectString $visualization "render_settings" "paths.visualization"
    ) "paths.visualization.render_settings" $true
    $visualizationPuppeteerConfig = Resolve-ProjectManifestPath $RepoRoot (
        Get-RequiredProjectString $visualization "puppeteer_config" "paths.visualization"
    ) "paths.visualization.puppeteer_config" $true

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
        visualization_powershell_helper = $visualizationPowershellHelper
        visualization_render_settings = $visualizationRenderSettings
        visualization_puppeteer_config = $visualizationPuppeteerConfig
        cleanup_python_helper = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $cleanup "python_helper" "paths.cleanup") "paths.cleanup.python_helper" $true
        cleanup_powershell_helper = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $cleanup "powershell_helper" "paths.cleanup") "paths.cleanup.powershell_helper" $true
        lookup_keys_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "lookup_keys" "registries") "registries.lookup_keys" $true
        schema_packs_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "schema_packs" "registries") "registries.schema_packs" $true
        taxonomy_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "taxonomy" "registries") "registries.taxonomy" $true
        resources_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "resources" "registries") "registries.resources" $true
        sources_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "sources" "registries") "registries.sources" $true
        entities_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "entities" "registries") "registries.entities" $true
        reconciliation_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "reconciliation" "registries") "registries.reconciliation" $true
        provenance_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "provenance" "registries") "registries.provenance" $true
        chronology_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "chronology" "registries") "registries.chronology" $true
        occurrences_registry = Resolve-ProjectManifestPath $RepoRoot (Get-RequiredProjectString $registries "occurrences" "registries") "registries.occurrences" $true
    }
}
