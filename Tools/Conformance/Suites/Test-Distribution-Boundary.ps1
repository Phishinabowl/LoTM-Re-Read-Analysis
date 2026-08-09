[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force
$Root = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath

$requiredPackRejections = @(
    'registry-unselected-dependency'
    'pack-executable-entrypoint'
    'pack-install-hooks'
    'pack-embedded-credentials'
    'pack-commercial-offerings'
    'pack-entitlements'
)
$forbiddenOutputKeys = @(
    'account_id'
    'acquirable'
    'commercial_offerings'
    'entitled'
    'entitlement_provider'
    'entitlements'
    'grants'
    'offering_catalog'
    'post_install_enforcement'
    'price'
    'pricing'
    'product_tier'
    'sku'
    'subscription_id'
    'tenant_id'
    'token'
)
$projectInjectionCases = [ordered]@{
    account_id = 'fixture-account'
    commercial_offerings = @('premium')
    entitlements = @('paid')
    pricing = [ordered]@{ amount = '999.00' }
    post_install_enforcement = 'disable'
}
$projectDirectories = @(
    'Artwork'
    'Tools'
    'Visualization'
    'Visualization\graphs'
    'Visualization\rendered'
)
$projectContentDirectories = @('Boards', 'Glossary_Threads', 'Investigations', 'Volumes')
$projectFiles = @(
    'Tools\Commands\Maintenance\clean_temp_files.py'
    'Tools\Commands\Maintenance\Clean-TempFiles.ps1'
    'Visualization\visualize.py'
    'Visualization\visualize.ps1'
    'Visualization\config\render-settings.json'
    'Visualization\config\puppeteer-config.json'
    'Visualization\data\refresh-snapshot.json'
)

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)

    $parent = [System.IO.Path]::GetDirectoryName($Path)
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        $null = New-Item -ItemType Directory -Path $parent -Force
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function New-BoundaryProject {
    param([string]$SourceRoot, [string]$TargetRoot)

    $null = New-Item -ItemType Directory -Path $TargetRoot -Force
    Copy-Item -LiteralPath (Join-Path $SourceRoot 'Framework') -Destination $TargetRoot -Recurse
    Copy-Item -LiteralPath (Join-Path $SourceRoot 'Project_Config') -Destination $TargetRoot -Recurse
    Get-ChildItem -LiteralPath $SourceRoot -File -Filter '*.md' |
        ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $TargetRoot }
    foreach ($relative in $projectContentDirectories) {
        Copy-Item -LiteralPath (Join-Path $SourceRoot $relative) -Destination $TargetRoot -Recurse
    }
    foreach ($relative in $projectDirectories) {
        $null = New-Item -ItemType Directory -Path (Join-Path $TargetRoot $relative) -Force
    }
    foreach ($relative in $projectFiles) {
        $content = if ([System.IO.Path]::GetExtension($relative) -ceq '.json') {
            "{}`n"
        }
        else {
            "# Boundary fixture.`n"
        }
        Write-Utf8NoBom (Join-Path $TargetRoot $relative) $content
    }
}

function Get-ProjectCompositionProbe {
    param([string]$SourceRoot, [string]$ProjectRoot)

    $executable = (Get-Process -Id $PID).Path
    $arguments = @('-NoProfile')
    if ($PSVersionTable.PSEdition -ceq 'Desktop') {
        $arguments += @('-ExecutionPolicy', 'Bypass')
    }
    $arguments += @(
        '-File'
        (Join-Path $SourceRoot 'Tools\Conformance\Suites\Test-Project-Composition.ps1')
        '-Root'
        $ProjectRoot
        '-Json'
    )
    $output = @(& $executable @arguments 2>&1)
    if ($LASTEXITCODE -ne 0) {
        $detail = @($output | ForEach-Object { [string]$_ } | Where-Object { $_ }) -join [Environment]::NewLine
        throw "Project-composition boundary probe failed: $detail"
    }
    $lines = @($output | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
    if ($lines.Count -eq 0) {
        throw 'Project-composition boundary probe emitted no JSON summary.'
    }
    return $lines[$lines.Count - 1] | ConvertFrom-Json
}

function Get-BoundarySemanticOutputs {
    param([string]$SourceRoot, [string]$ProjectRoot)

    return [ordered]@{
        catalog = Get-KnowledgeFrameworkCatalog $ProjectRoot
        effective_schema = Get-KnowledgeEffectiveProjectSchema $ProjectRoot
        project_composition = Get-ProjectCompositionProbe $SourceRoot $ProjectRoot
    }
}

function Assert-NoForbiddenOutputKeys {
    param([string]$CanonicalJson)

    foreach ($key in $forbiddenOutputKeys) {
        $pattern = '"' + [regex]::Escape($key) + '"\s*:'
        if ($CanonicalJson -match $pattern) {
            throw "Commercial field leaked into portable outputs: $key"
        }
    }
}

function Assert-ProjectInjectionRejected {
    param([string]$ProjectRoot, [string]$Key, [object]$Value)

    $manifest = Join-Path $ProjectRoot 'Project_Config\project.yaml'
    $original = [System.IO.File]::ReadAllText($manifest)
    try {
        $serialized = $Value | ConvertTo-Json -Depth 10 -Compress
        Write-Utf8NoBom $manifest ($original + "`n${Key}: $serialized`n")
        try {
            $null = Get-KnowledgeProjectConfig $ProjectRoot
        }
        catch {
            return
        }
        throw "Portable project manifest accepted commercial field: $Key"
    }
    finally {
        Write-Utf8NoBom $manifest $original
    }
}

$expectations = Get-Content `
    -LiteralPath (Join-Path $Root 'Framework\Data\Schema-Packs\expectations.json') `
    -Raw |
    ConvertFrom-Json
$rejectionIds = @($expectations.invalid_cases | ForEach-Object { [string]$_.id })
$missingRejections = @($requiredPackRejections | Where-Object { $rejectionIds -cnotcontains $_ })
if ($missingRejections.Count -gt 0) {
    throw "Required schema-pack boundary rejections are missing: $($missingRejections -join ', ')"
}

$fixturePath = Join-Path $Root 'Framework\Data\Distribution-Boundary\adversarial-external-metadata.json'
$fixtureContent = [System.IO.File]::ReadAllText($fixturePath)
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "knowledge-distribution-boundary-$PID-$([guid]::NewGuid())"
try {
    $projectRoot = Join-Path $tempRoot 'project'
    New-BoundaryProject $Root $projectRoot
    $baseline = Get-BoundarySemanticOutputs $Root $projectRoot
    $baselineJson = ConvertTo-KnowledgeCanonicalJson $baseline
    Assert-NoForbiddenOutputKeys $baselineJson

    $sidecarPaths = @(
        (Join-Path $projectRoot 'Framework\Distribution\offerings.json')
        (Join-Path $projectRoot 'Project_Config\entitlements.json')
        (Join-Path $projectRoot 'Framework\Packs\narrative-media\entitlement.json')
        (Join-Path $projectRoot 'Framework\Packs\remote-premium\offering.json')
    )
    foreach ($path in $sidecarPaths) {
        Write-Utf8NoBom $path $fixtureContent
    }

    $withExternalMetadata = Get-BoundarySemanticOutputs $Root $projectRoot
    $externalJson = ConvertTo-KnowledgeCanonicalJson $withExternalMetadata
    if ($externalJson -cne $baselineJson) {
        throw 'External commercial metadata changed portable composition outputs.'
    }
    foreach ($entry in $projectInjectionCases.GetEnumerator()) {
        Assert-ProjectInjectionRejected $projectRoot ([string]$entry.Key) $entry.Value
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    schema_version = 1
    pack_rejection_vectors = $requiredPackRejections.Count
    project_injection_cases = $projectInjectionCases.Count
    external_metadata_locations = $sidecarPaths.Count
    semantic_surfaces = $baseline.Count
    provider_failure_inert = $true
    portable_outputs_unchanged = $true
    forbidden_output_keys = $forbiddenOutputKeys.Count
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Distribution-boundary conformance passed: ' +
        "$($summary.semantic_surfaces) semantic surfaces, " +
        "$($summary.external_metadata_locations) inert metadata locations, and " +
        "$($summary.project_injection_cases) rejected project injections."
    )
}
