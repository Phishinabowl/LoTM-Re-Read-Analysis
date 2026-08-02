$script:ProjectManifestPath = 'Project_Config/project.yaml'
$script:ProjectRootEnvironmentVariable = 'KNOWLEDGE_PROJECT_ROOT'

function Test-KnowledgeProjectRoot {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $false
    }
    $resolved = [System.IO.Path]::GetFullPath($Path)
    return (
        (Test-Path -LiteralPath $resolved -PathType Container) -and
        (Test-Path -LiteralPath (Join-Path $resolved $script:ProjectManifestPath) -PathType Leaf)
    )
}

function Get-KnowledgeProjectSearchStart {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (Test-Path -LiteralPath $resolved -PathType Leaf) {
        return [System.IO.Path]::GetDirectoryName($resolved)
    }
    return $resolved
}

function Resolve-KnowledgeValidatedProjectRoot {
    param(
        [string]$Value,
        [string]$Source,
        [switch]$RequireAbsolute
    )

    if ($RequireAbsolute -and -not [System.IO.Path]::IsPathRooted($Value)) {
        throw "$Source must be an absolute path: $Value"
    }
    $resolved = [System.IO.Path]::GetFullPath($Value)
    if (-not (Test-KnowledgeProjectRoot $resolved)) {
        throw "Project root from $Source is missing required manifest $($script:ProjectManifestPath): $resolved"
    }
    return $resolved
}

function Resolve-KnowledgeProjectRoot {
    param(
        [string]$ExplicitRoot,
        [string]$ExecutablePath,
        [string]$CurrentDirectory
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitRoot)) {
        return Resolve-KnowledgeValidatedProjectRoot $ExplicitRoot 'explicit root'
    }

    $environmentRoot = [Environment]::GetEnvironmentVariable($script:ProjectRootEnvironmentVariable)
    if (-not [string]::IsNullOrWhiteSpace($environmentRoot)) {
        return Resolve-KnowledgeValidatedProjectRoot `
            $environmentRoot.Trim() `
            "environment variable $($script:ProjectRootEnvironmentVariable)" `
            -RequireAbsolute
    }

    $workingDirectory = if ([string]::IsNullOrWhiteSpace($CurrentDirectory)) {
        (Get-Location).Path
    }
    else {
        $CurrentDirectory
    }
    $searchStarts = @(
        [pscustomobject]@{ label = 'current directory'
            path = $workingDirectory
        }
    )
    $executableStart = Get-KnowledgeProjectSearchStart $ExecutablePath
    if ($null -ne $executableStart) {
        $searchStarts += [pscustomobject]@{ label = 'executable location'
            path = $executableStart
        }
    }

    $checked = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($start in $searchStarts) {
        $current = [System.IO.Path]::GetFullPath($start.path)
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

    $starts = @(
        $searchStarts | ForEach-Object {
            '{0}={1}' -f $_.label, [System.IO.Path]::GetFullPath($_.path)
        }
    ) -join ', '
    throw (
        "Could not auto-detect the project root from $starts. " +
        "Expected manifest: $($script:ProjectManifestPath). " +
        "Pass the root explicitly or set $($script:ProjectRootEnvironmentVariable) to an absolute project path."
    )
}

$implementationFiles = @(
    'Strict-Yaml.ps1'
    'Project-Config.ps1'
    'Lookup-Key-Config.ps1'
    'Schema-Pack-Config.ps1'
    'Taxonomy-Config.ps1'
    'Resource-Config.ps1'
    'Temporal-Config.ps1'
    'Source-Config.ps1'
    'Chronology-Config.ps1'
    'Entity-Config.ps1'
    'Reconciliation-Config.ps1'
    'Occurrence-Config.ps1'
    'Provenance-Config.ps1'
)
foreach ($implementationFile in $implementationFiles) {
    . (Join-Path $PSScriptRoot (Join-Path 'Private' $implementationFile))
}
