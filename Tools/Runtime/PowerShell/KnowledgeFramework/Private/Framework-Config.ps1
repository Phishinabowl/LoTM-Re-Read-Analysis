$script:SupportedFrameworkSchemaVersion = 1
$script:StableFrameworkIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'

function Get-RequiredFrameworkString {
    param(
        [object]$Map,
        [string]$Key,
        [string]$Context
    )

    $value = Get-ProjectMapValue $Map $Key
    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
        throw "Framework manifest '$Context.$Key' must be a non-empty string."
    }
    return ([string]$value).Trim()
}

function Resolve-FrameworkManifestPath {
    param(
        [string]$FrameworkDirectory,
        [string]$Value,
        [string]$Key,
        [switch]$Directory
    )

    if ($Value.Contains('\')) {
        throw "Framework manifest '$Key' must use forward slashes: $Value"
    }
    $segments = @($Value.Split('/'))
    if (
        [System.IO.Path]::IsPathRooted($Value) -or
        $Value -match '^[A-Za-z]:/' -or
        $Value.StartsWith('//') -or
        @($segments | Where-Object { $_ -in @('', '.', '..') }).Count -gt 0
    ) {
        throw "Framework manifest '$Key' must be a confined relative path: $Value"
    }

    $resolvedRoot = [System.IO.Path]::GetFullPath($FrameworkDirectory)
    $relativePlatformPath = $segments -join [System.IO.Path]::DirectorySeparatorChar
    $resolved = [System.IO.Path]::GetFullPath((Join-Path $resolvedRoot $relativePlatformPath))
    if (-not $resolved.StartsWith($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Framework manifest '$Key' escapes the Framework directory: $Value"
    }
    if ($Directory) {
        if (-not (Test-Path -LiteralPath $resolved -PathType Container)) {
            throw "Framework manifest '$Key' directory does not exist: $Value"
        }
    }
    elseif (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "Framework manifest '$Key' file does not exist: $Value"
    }
    return $resolved
}

function Get-KnowledgeFrameworkConfig {
    param([string]$FrameworkRoot)

    Import-KnowledgeYamlModule
    $resolvedRoot = [System.IO.Path]::GetFullPath($FrameworkRoot)
    $manifestPath = Join-Path $resolvedRoot $script:FrameworkManifestPath
    $manifest = ConvertFrom-KnowledgeYamlFile `
        $manifestPath `
        $script:SupportedFrameworkSchemaVersion `
        'framework manifest'
    Assert-KnowledgeMapKeys `
        $manifest `
    @('schema_version', 'framework_id', 'paths', 'registries') `
        'Framework manifest root'

    $frameworkId = Get-RequiredFrameworkString $manifest 'framework_id' 'root'
    if ($frameworkId -cnotmatch $script:StableFrameworkIdPattern) {
        throw "Framework manifest 'root.framework_id' must be a lowercase kebab-case stable ID: $frameworkId"
    }

    $paths = Get-ProjectMapValue $manifest 'paths'
    if ($null -eq $paths) {
        throw "Framework manifest 'paths' must be a mapping."
    }
    Assert-KnowledgeMapKeys $paths @('packs') "Framework manifest 'paths'"
    $registries = Get-ProjectMapValue $manifest 'registries'
    if ($null -eq $registries) {
        throw "Framework manifest 'registries' must be a mapping."
    }
    Assert-KnowledgeMapKeys $registries @('lookup_keys') "Framework manifest 'registries'"

    $packsRelativePath = Get-RequiredFrameworkString $paths 'packs' 'paths'
    $lookupRelativePath = Get-RequiredFrameworkString $registries 'lookup_keys' 'registries'
    $frameworkDirectory = [System.IO.Path]::GetDirectoryName($manifestPath)
    $packsRoot = Resolve-FrameworkManifestPath $frameworkDirectory $packsRelativePath 'paths.packs' -Directory
    $lookupRegistry = Resolve-FrameworkManifestPath `
        $frameworkDirectory `
        $lookupRelativePath `
        'registries.lookup_keys'

    return [pscustomobject]@{
        root = $resolvedRoot
        framework_directory = $frameworkDirectory
        manifest_path = $manifestPath
        schema_version = $script:SupportedFrameworkSchemaVersion
        framework_id = $frameworkId
        packs_relative_path = $packsRelativePath
        packs_root = $packsRoot
        lookup_keys_relative_path = $lookupRelativePath
        lookup_keys_registry = $lookupRegistry
        lookup_keys = Get-KnowledgeLookupKeyRegistryConfig $lookupRegistry
    }
}
