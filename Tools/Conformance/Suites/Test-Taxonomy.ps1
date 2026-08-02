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
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Assert-Rejected {
    param(
        [scriptblock]$Action,
        [string]$Message
    )

    $rejected = $false
    try {
        & $Action
    }
    catch {
        $rejected = $true
    }
    if (-not $rejected) {
        throw $Message
    }
}

function ConvertTo-MutableFixtureValue {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value -or $Value -is [string] -or $Value.GetType().IsPrimitive) {
        return $Value
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $mapping = [ordered]@{}
        foreach ($key in $Value.Keys) {
            $mapping[[string]$key] = ConvertTo-MutableFixtureValue $Value[$key]
        }
        return $mapping
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $mapping = [ordered]@{}
        foreach ($property in $Value.PSObject.Properties) {
            $mapping[$property.Name] = ConvertTo-MutableFixtureValue $property.Value
        }
        return $mapping
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        $list = New-Object System.Collections.ArrayList
        foreach ($item in $Value) {
            [void]$list.Add((ConvertTo-MutableFixtureValue $item))
        }
        return , $list
    }
    return $Value
}

function Get-FixtureMutationParent {
    param(
        [object]$Document,
        [object[]]$Path
    )

    if ($Path.Count -eq 0) {
        throw 'Fixture mutation path cannot be empty.'
    }
    $current = $Document
    for ($index = 0; $index -lt $Path.Count - 1; $index += 1) {
        $current = $current[$Path[$index]]
    }
    return [pscustomobject]@{
        parent = $current
        final = $Path[$Path.Count - 1]
    }
}

function Invoke-FixtureMutation {
    param(
        [object]$Document,
        [object]$Operation,
        [string]$CaseRoot
    )

    $location = Get-FixtureMutationParent $Document @($Operation.path)
    $operationValue = if (
        $Operation.PSObject.Properties.Name -ccontains 'value_source' -and
        [string]$Operation.value_source -ceq 'absolute-path'
    ) {
        [System.IO.Path]::GetFullPath((Join-Path $CaseRoot '..\outside'))
    }
    elseif ($Operation.PSObject.Properties.Name -ccontains 'value') {
        ConvertTo-MutableFixtureValue $Operation.value
    }
    else {
        $null
    }
    switch ([string]$Operation.op) {
        'set' {
            $location.parent[$location.final] = $operationValue
        }
        'append' {
            $target = $location.parent[$location.final]
            if ($target -isnot [System.Collections.ArrayList]) {
                throw 'Fixture append target must be a mutable list.'
            }
            [void]$target.Add($operationValue)
        }
        'remove' {
            if ($location.parent -is [System.Collections.ArrayList]) {
                $location.parent.RemoveAt([int]$location.final)
            }
            else {
                [void]$location.parent.Remove([string]$location.final)
            }
        }
        default {
            throw "Unknown fixture mutation operation: $($Operation.op)"
        }
    }
}

function Write-FixtureJson {
    param(
        [string]$Path,
        [object]$Value
    )

    $content = ($Value | ConvertTo-Json -Depth 100) + [Environment]::NewLine
    [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
}

function New-FixtureProject {
    param(
        [object]$Project,
        [string]$FixtureRoot
    )

    $fixtureProject = $Project.PSObject.Copy()
    $fixtureProject.root = $FixtureRoot
    $fixtureProject.taxonomy_registry = Join-Path $FixtureRoot 'registry.json'
    $fixtureProject.content_roots = @(
        [pscustomobject]@{
            id = 'articles'
            relative_path = 'content/articles'
            path = Join-Path $FixtureRoot 'content\articles'
            provenance_mode = 'fixed'
            provenance_label = 'article'
        }
        [pscustomobject]@{
            id = 'records'
            relative_path = 'content/records'
            path = Join-Path $FixtureRoot 'content\records'
            provenance_mode = 'fixed'
            provenance_label = 'record'
        }
    )
    return $fixtureProject
}

function Assert-ValidTaxonomyFixture {
    param(
        [object]$Registry,
        [object]$Project,
        [object]$Expected
    )

    if ($Registry.content_types.Count -ne [int]$Expected.content_types) {
        throw 'Taxonomy fixture content-type count changed.'
    }
    if ($Registry.categories.Count -ne [int]$Expected.categories) {
        throw 'Taxonomy fixture category count changed.'
    }
    $activeCategories = @($Registry.categories.Values | Where-Object lifecycle -eq 'active')
    if ($activeCategories.Count -ne [int]$Expected.active_categories) {
        throw 'Taxonomy fixture active-category count changed.'
    }
    $qaRootIds = @(Get-TaxonomyQaPageContentRoots $Project $Registry | ForEach-Object id)
    if (($qaRootIds -join '|') -cne (@($Expected.qa_root_ids) -join '|')) {
        throw 'Taxonomy QA content-root selection changed.'
    }
    $alpha = $Registry.categories['subject-alpha']
    if (($alpha.placements.Keys -join '|') -cne (@($Expected.subject_alpha_placements) -join '|')) {
        throw 'Taxonomy category placement order changed.'
    }
    $alphaPage = $alpha.placements['subject-page']
    if ([string]$alphaPage.relative_folder -cne [string]$Expected.subject_alpha_page_folder) {
        throw 'Taxonomy relative placement changed.'
    }
    if (([string]$alphaPage.template).Replace('\', '/') -cne [string]$Expected.subject_alpha_page_template) {
        throw 'Taxonomy placement template selection changed.'
    }
    if ([string]$Registry.content_types['fixed-index'].record_path -cne [string]$Expected.fixed_record_path) {
        throw 'Taxonomy fixed record path changed.'
    }
    $provider = Get-KnowledgeTaxonomyReconciliationProvider $Registry
    if (
        [string]$provider.provider_id -cne 'taxonomy' -or
        ($provider.targets.Keys -join '|') -cne (@($Expected.reconciliation_target_types) -join '|')
    ) {
        throw 'Taxonomy reconciliation provider changed.'
    }
    $categoryTarget = Get-KnowledgeTaxonomyReconciliationTarget $Registry 'category' 'subject-alpha'
    if (-not [object]::ReferenceEquals($categoryTarget, $alpha)) {
        throw 'Taxonomy reconciliation category lookup changed.'
    }
    $contentTarget = Get-KnowledgeTaxonomyReconciliationTarget $Registry 'content-type' 'subject-page'
    if (-not [object]::ReferenceEquals($contentTarget, $Registry.content_types['subject-page'])) {
        throw 'Taxonomy reconciliation content-type lookup changed.'
    }
}

function New-ScaleTaxonomyFixture {
    param(
        [string]$FixtureRoot,
        [object]$BaseDocument,
        [int]$CategoryCount
    )

    $categories = [ordered]@{}
    for ($index = 0; $index -lt $CategoryCount; $index += 1) {
        $categoryId = 'scale-subject-{0:d3}' -f $index
        $prefix = 'scale-{0:d3}' -f $index
        $categories[$categoryId] = [ordered]@{
            lifecycle = 'active'
            label = 'Scale Subject {0:d3}' -f $index
            plural_label = 'Scale Subjects {0:d3}' -f $index
            canonical_pages_enabled = $true
            metadata_type = 'Scale Subject {0:d3}' -f $index
            subject_slug_prefix = $prefix
            subject_slug_pattern = "^$prefix-[a-z0-9][a-z0-9-]*$"
            graph_class = 'scale-class-{0:d3}' -f $index
            placements = [ordered]@{
                'subject-page' = [ordered]@{relative_folder="Scale-$('{0:d3}' -f $index)"
                }
            }
        }
    }
    $registry = [ordered]@{
        schema_version = 2
        content_types = [ordered]@{'subject-page'=$BaseDocument['content_types']['subject-page']
        }
        categories = $categories
    }
    Write-FixtureJson (Join-Path $FixtureRoot 'registry.json') $registry
}

$project = Get-KnowledgeProjectConfig $Root
$canonical = Get-KnowledgeTaxonomyConfig $project
$fixtureRoot = Join-Path $Root 'Framework\Data\Taxonomy'
$baseRoot = Join-Path $fixtureRoot 'base'
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
if (-not (Test-KnowledgeJsonInteger $expectations.schema_version) -or [int]$expectations.schema_version -ne 1) {
    throw 'Unsupported taxonomy conformance expectation schema.'
}
$baseDocument = ConvertTo-MutableFixtureValue (
    Get-Content -LiteralPath (Join-Path $baseRoot 'registry.json') -Raw |
        ConvertFrom-Json
)

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-taxonomy-{0}" -f [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
try {
    $validRoot = Join-Path $tempRoot 'valid'
    Copy-Item -LiteralPath $baseRoot -Destination $validRoot -Recurse
    $validProject = New-FixtureProject $project $validRoot
    $fixtureRegistry = Get-KnowledgeTaxonomyConfig $validProject
    Assert-ValidTaxonomyFixture $fixtureRegistry $validProject $expectations.valid
    Assert-Rejected {
        $null = Get-KnowledgeTaxonomyReconciliationTarget $fixtureRegistry 'unknown' 'subject-alpha'
    } 'Unsupported taxonomy reconciliation target type was accepted.'
    Assert-Rejected {
        $null = Get-KnowledgeTaxonomyReconciliationTarget $fixtureRegistry 'category' 'unknown'
    } 'Unknown taxonomy reconciliation target was accepted.'

    foreach ($case in @($expectations.invalid_cases)) {
        $caseRoot = Join-Path $tempRoot ([string]$case.id)
        Copy-Item -LiteralPath $baseRoot -Destination $caseRoot -Recurse
        $document = ConvertTo-MutableFixtureValue $baseDocument
        foreach ($operation in @($case.operations)) {
            Invoke-FixtureMutation $document $operation $caseRoot
        }
        Write-FixtureJson (Join-Path $caseRoot 'registry.json') $document
        $caseProject = New-FixtureProject $project $caseRoot
        Assert-Rejected {
            $null = Get-KnowledgeTaxonomyConfig $caseProject
        } "Malformed taxonomy configuration was accepted: $($case.id)"
    }

    $scaleRoot = Join-Path $tempRoot 'scale'
    Copy-Item -LiteralPath $baseRoot -Destination $scaleRoot -Recurse
    $scaleCount = [int]$expectations.scale_category_count
    New-ScaleTaxonomyFixture $scaleRoot $baseDocument $scaleCount
    $scaleProject = New-FixtureProject $project $scaleRoot
    $scaleRegistry = Get-KnowledgeTaxonomyConfig $scaleProject
    if ($scaleRegistry.content_types.Count -ne 1 -or $scaleRegistry.categories.Count -ne $scaleCount) {
        throw 'Taxonomy scale composition counts changed.'
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    canonical_categories = [int]$canonical.categories.Count
    canonical_content_types = [int]$canonical.content_types.Count
    fixture_active_categories = [int]@($fixtureRegistry.categories.Values | Where-Object lifecycle -eq 'active').Count
    fixture_categories = [int]$fixtureRegistry.categories.Count
    fixture_content_types = [int]$fixtureRegistry.content_types.Count
    invalid_configuration_cases = [int]@($expectations.invalid_cases).Count
    invalid_query_cases = [int]$expectations.invalid_query_cases
    scale_category_count = [int]$scaleCount
    schema_version = 1
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Taxonomy conformance passed: {0} canonical content types, {1} canonical categories, ' +
        '{2} malformed configurations, and {3} scale categories.' -f
        $summary.canonical_content_types,
        $summary.canonical_categories,
        $summary.invalid_configuration_cases,
        $summary.scale_category_count
    )
}
