[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

function New-TestProject {
    param([string]$Path)

    $configDirectory = Join-Path $Path 'Project_Config'
    $null = New-Item -ItemType Directory -Path $configDirectory -Force
    Set-Content -LiteralPath (Join-Path $configDirectory 'project.yaml') -Value 'schema_version: 1' -Encoding UTF8
    return [System.IO.Path]::GetFullPath($Path)
}

function Assert-Rejected {
    param(
        [scriptblock]$Action,
        [string]$ExpectedText
    )

    try {
        & $Action
    }
    catch {
        if (-not $_.Exception.Message.Contains($ExpectedText)) {
            throw "Expected error containing '$ExpectedText', got: $($_.Exception.Message)"
        }
        return
    }
    throw "Expected rejection containing '$ExpectedText'."
}

$actualRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$originalLocation = (Get-Location).Path
$originalEnvironmentRoot = [Environment]::GetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT')
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('knowledge-project-root-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
$vectors = 0

try {
    $projectA = New-TestProject (Join-Path $tempRoot 'project-a')
    $projectB = New-TestProject (Join-Path $tempRoot 'project-b')
    $nestedA = Join-Path $projectA 'one\two'
    $null = New-Item -ItemType Directory -Path $nestedA -Force
    $nestedB = Join-Path $projectB 'nested'
    $null = New-Item -ItemType Directory -Path $nestedB
    $executableB = Join-Path $nestedB 'command.ps1'
    Set-Content -LiteralPath $executableB -Value '# fixture' -Encoding UTF8
    $unrelated = Join-Path $tempRoot 'unrelated'
    $null = New-Item -ItemType Directory -Path $unrelated
    $gitOnly = Join-Path $tempRoot 'git-only'
    $null = New-Item -ItemType Directory -Path (Join-Path $gitOnly '.git') -Force

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT', $projectB)
    if ((Resolve-KnowledgeProjectRoot -ExplicitRoot $actualRoot) -cne $actualRoot) {
        throw 'Explicit root did not take precedence over the environment override.'
    }
    $vectors++
    if ((Resolve-KnowledgeProjectRoot) -cne $projectB) {
        throw 'Environment root did not resolve.'
    }
    $vectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT', $unrelated)
    Assert-Rejected { Resolve-KnowledgeProjectRoot } 'missing required manifest'
    $vectors++
    [Environment]::SetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT', 'relative/project')
    Assert-Rejected { Resolve-KnowledgeProjectRoot } 'must be an absolute path'
    $vectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT', $null)
    if ((Resolve-KnowledgeProjectRoot -CurrentDirectory $nestedA) -cne $projectA) {
        throw 'Current-directory ancestry did not resolve.'
    }
    $vectors++
    if ((Resolve-KnowledgeProjectRoot -ExecutablePath $executableB -CurrentDirectory $unrelated) -cne $projectB) {
        throw 'Executable ancestry did not resolve after current-directory search failed.'
    }
    $vectors++
    if ((Resolve-KnowledgeProjectRoot -ExecutablePath $executableB -CurrentDirectory $nestedA) -cne $projectA) {
        throw 'Current-directory ancestry did not take precedence over executable ancestry.'
    }
    $vectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT', $projectB)
    if ((Resolve-KnowledgeProjectRoot -ExecutablePath $executableB -CurrentDirectory $nestedA) -cne $projectB) {
        throw 'Environment root did not take precedence over ancestry searches.'
    }
    $vectors++

    [Environment]::SetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT', $null)
    Assert-Rejected { Resolve-KnowledgeProjectRoot -CurrentDirectory $gitOnly } 'Could not auto-detect'
    $vectors++
    Assert-Rejected { Resolve-KnowledgeProjectRoot -CurrentDirectory $unrelated } 'Expected manifest: Project_Config/project.yaml'
    $vectors++
    if ((Get-Location).Path -cne $originalLocation) {
        throw 'Project-root discovery changed the working directory.'
    }
    $vectors++
}
finally {
    [Environment]::SetEnvironmentVariable('KNOWLEDGE_PROJECT_ROOT', $originalEnvironmentRoot)
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    environment_variable = 'KNOWLEDGE_PROJECT_ROOT'
    marker = 'Project_Config/project.yaml'
    schema_version = 1
    vectors = $vectors
    working_directory_preserved = (Get-Location).Path -ceq $originalLocation
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output "Project-root conformance passed: $vectors vectors; working directory preserved."
}
