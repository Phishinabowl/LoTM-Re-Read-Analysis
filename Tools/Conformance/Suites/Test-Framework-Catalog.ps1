[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

$fixturePackIds = @('fixture-core', 'fixture-domain', 'fixture-extension')

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)

    $parent = [System.IO.Path]::GetDirectoryName($Path)
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        $null = New-Item -ItemType Directory -Path $parent -Force
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Write-JsonFixture {
    param([string]$Path, [object]$Value)

    Write-Utf8NoBom $Path (($Value | ConvertTo-Json -Depth 30) + "`n")
}

function Assert-Rejected {
    param(
        [scriptblock]$Action,
        [string]$ExpectedText,
        [string]$ExpectedClassification
    )

    try {
        & $Action
    }
    catch {
        if (-not $_.Exception.Message.Contains($ExpectedText)) {
            throw "Expected error containing '$ExpectedText', got: $($_.Exception.Message)"
        }
        if (-not [string]::IsNullOrWhiteSpace($ExpectedClassification)) {
            $actualClassification = [string]$_.Exception.Data['FrameworkCatalogClassification']
            if ($actualClassification -cne $ExpectedClassification) {
                throw "Expected classification '$ExpectedClassification', got '$actualClassification'."
            }
        }
        return
    }
    throw "Expected rejection containing '$ExpectedText'."
}

function New-CatalogRoot {
    param([string]$SourceRoot, [string]$TargetRoot)

    $framework = Join-Path $TargetRoot 'Framework'
    $data = Join-Path $framework 'Data'
    $packs = Join-Path $framework 'Packs'
    $null = New-Item -ItemType Directory -Path $data -Force
    $null = New-Item -ItemType Directory -Path $packs
    Copy-Item `
        -LiteralPath (Join-Path $SourceRoot 'Framework\Data\unicode-lookup-16.0.0.json') `
        -Destination $data
    Write-Utf8NoBom `
    (Join-Path $framework 'framework.yaml') `
    (
        "schema_version: 1`n" +
        "framework_id: fixture-framework`n" +
        "paths:`n" +
        "  packs: Packs`n" +
        "registries:`n" +
        "  lookup_keys: Data/unicode-lookup-16.0.0.json`n"
    )
    $sourcePacks = Join-Path $SourceRoot 'Framework\Data\Schema-Packs\base\packs'
    foreach ($packId in $fixturePackIds) {
        $target = Join-Path $packs "$packId\pack.yaml"
        $null = New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($target))
        Copy-Item -LiteralPath (Join-Path $sourcePacks "$packId.json") -Destination $target
    }
    $ignored = Join-Path $packs 'ignored-directory'
    $null = New-Item -ItemType Directory -Path $ignored
    Write-Utf8NoBom (Join-Path $ignored 'README.md') "No pack manifest.`n"
    return [System.IO.Path]::GetFullPath($TargetRoot)
}

function Update-CatalogPack {
    param([string]$CatalogRoot, [string]$PackId, [scriptblock]$Action)

    $path = Join-Path $CatalogRoot "Framework\Packs\$PackId\pack.yaml"
    $document = ConvertFrom-Json -InputObject ([System.IO.File]::ReadAllText($path))
    & $Action $document
    Write-JsonFixture $path $document
}

function New-ScalePack {
    param([int]$Index)

    $packId = 'scale-pack-{0:d3}' -f $Index
    $capabilityId = 'scale-capability-{0:d3}' -f $Index
    $namespace = 'scale.value-{0:d3}' -f $Index
    $valueId = 'value-{0:d3}' -f $Index
    return [ordered]@{
        schema_version = 5
        pack_id = $packId
        pack_version = 1
        lifecycle = 'active'
        pack_kind = 'extension'
        classification = [ordered]@{
            family = 'scale'
            role = 'extension'
            scope = 'domain-neutral'
            domains = @()
            bridge_pack_ids = @()
        }
        presentation = [ordered]@{
            localization_key = "pack.$packId"
            default_locale = 'en'
            label = 'Scale Pack {0:d3}' -f $Index
            short_description = 'Generated catalog scale fixture.'
            long_description = 'Exercises deterministic installed-pack catalog behavior at scale.'
            maturity = 'experimental'
            intended_audiences = @(
                [ordered]@{ id = 'tester'
                    label = 'Tester'
                    description = 'Runs catalog scale tests.'
                }
            )
            use_cases = @(
                [ordered]@{ id = 'scale'
                    label = 'Scale'
                    description = 'Exercises catalog scale.'
                }
            )
            examples = @()
            prerequisites = @()
            provided_behaviors = @(
                [ordered]@{ id = 'catalog'
                    label = 'Catalog'
                    description = 'Provides one catalog row.'
                }
            )
            exclusions = @(
                [ordered]@{ id = 'project'
                    label = 'No project'
                    description = 'Contains no project data.'
                }
            )
            documentation = @()
            search_keywords = @('catalog', 'scale')
        }
        dependencies = @()
        capabilities = @(
            [ordered]@{
                id = $capabilityId
                lifecycle = 'available'
                presentation = [ordered]@{
                    localization_key = "capability.$capabilityId"
                    label = 'Scale Capability {0:d3}' -f $Index
                    description = 'Generated catalog scale capability.'
                }
            }
        )
        controlled_values = [ordered]@{
            $namespace = @($valueId)
        }
    }
}

$actualRoot = Resolve-KnowledgeFrameworkRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$expectations = ConvertFrom-Json -InputObject (
    [System.IO.File]::ReadAllText(
        (Join-Path $actualRoot 'Framework\Data\Framework-Catalog\expectations.json')
    )
)
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('knowledge-framework-catalog-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
$invalidCases = 0

try {
    $canonical = Get-KnowledgeFrameworkCatalog $actualRoot
    if ([int]$canonical.summary.pack_count -ne [int]$expectations.canonical_pack_count) {
        throw 'Canonical framework catalog pack count changed.'
    }
    if ([int]$canonical.summary.capability_count -ne [int]$expectations.canonical_capability_count) {
        throw 'Canonical framework catalog capability count changed.'
    }
    if (
        [int]$canonical.summary.available_capability_count -ne
        [int]$expectations.canonical_available_capability_count
    ) {
        throw 'Canonical available-capability count changed.'
    }
    if (
        [int]$canonical.summary.planned_capability_count -ne
        [int]$expectations.canonical_planned_capability_count
    ) {
        throw 'Canonical planned-capability count changed.'
    }
    if (
        [int]$canonical.summary.deprecated_capability_count -ne
        [int]$expectations.canonical_deprecated_capability_count
    ) {
        throw 'Canonical deprecated-capability count changed.'
    }
    $firstCatalogJson = ConvertTo-KnowledgeCanonicalJson $canonical
    $secondCatalogJson = ConvertTo-KnowledgeCanonicalJson (Get-KnowledgeFrameworkCatalog $actualRoot)
    if ($firstCatalogJson -cne $secondCatalogJson) {
        throw 'Repeated framework catalog loading was not deterministic.'
    }

    $effectiveSchema = Get-KnowledgeEffectiveProjectSchema $actualRoot
    $catalogBeforeView = ConvertTo-KnowledgeCanonicalJson $canonical
    $projectView = New-KnowledgeFrameworkCatalogProjectView $canonical $effectiveSchema
    if ($projectView.contract -cne 'framework-catalog-project-view') {
        throw 'Framework catalog project-view contract changed.'
    }
    if ($effectiveSchema.project.project_id -ceq 'lotm-analysis') {
        if (
            (ConvertTo-KnowledgeCanonicalJson $projectView.summary) -cne
            (ConvertTo-KnowledgeCanonicalJson $expectations.project_view_summary)
        ) {
            throw 'Framework catalog project-view summary changed.'
        }
    }
    if (
        [int]$projectView.summary.pack_count -ne @($canonical.packs).Count -or
        [int]$projectView.summary.selected_pack_count -ne @($effectiveSchema.packs).Count -or
        [int]$projectView.summary.capability_count -ne @($canonical.capabilities).Count -or
        [int]$projectView.summary.selected_capability_count -ne @($effectiveSchema.capabilities).Count -or
        [int]$projectView.summary.enabled_capability_count -ne
        @($effectiveSchema.capabilities | Where-Object enabled).Count
    ) {
        throw 'Framework catalog project-view invariant counts changed.'
    }
    $repeatedProjectView = New-KnowledgeFrameworkCatalogProjectView $canonical $effectiveSchema
    if (
        (ConvertTo-KnowledgeCanonicalJson $projectView) -cne
        (ConvertTo-KnowledgeCanonicalJson $repeatedProjectView)
    ) {
        throw 'Repeated framework catalog project-view composition was not deterministic.'
    }
    if ((ConvertTo-KnowledgeCanonicalJson $canonical) -cne $catalogBeforeView) {
        throw 'Framework catalog project-view composition mutated the base catalog.'
    }
    $selectedPackId = [string]@($effectiveSchema.packs)[0].id
    $selectedPack = @($projectView.packs | Where-Object id -CEQ $selectedPackId)[0]
    $unselectedPack = @($projectView.packs | Where-Object { -not $_.project_state.selected })[0]
    $enabledCapabilityId = [string]@($effectiveSchema.capabilities | Where-Object enabled)[0].id
    $enabledCapability = @($projectView.capabilities | Where-Object id -CEQ $enabledCapabilityId)[0]
    $plannedCapability = @($projectView.capabilities | Where-Object { $_.project_state.planned })[0]
    if (-not $selectedPack.project_state.selected -or -not $selectedPack.project_state.used_by_project) {
        throw 'Selected project-view pack state changed.'
    }
    if ($unselectedPack.project_state.selected -or -not $unselectedPack.project_state.available) {
        throw 'Unselected project-view pack state changed.'
    }
    if (-not $enabledCapability.project_state.enabled) {
        throw 'Enabled project-view capability state changed.'
    }
    if (
        $plannedCapability.project_state.selected -ne
        (@($effectiveSchema.capabilities | Where-Object id -CEQ $plannedCapability.id).Count -gt 0) -or
        $plannedCapability.project_state.available -or
        $plannedCapability.project_state.enabled -or
        -not $plannedCapability.project_state.planned -or
        $plannedCapability.project_state.used_by_project -or
        $plannedCapability.project_state.unavailable_reason -cne 'capability-lifecycle-planned'
    ) {
        throw 'Planned project-view capability state changed.'
    }
    $projectSelection = New-KnowledgeFrameworkCatalogProjectViewSelection `
        $canonical `
        $projectView `
    (Get-KnowledgeFrameworkConfig $actualRoot).lookup_keys `
        $selectedPackId.ToUpperInvariant() `
        $enabledCapabilityId.ToUpperInvariant()
    if (
        $projectSelection.contract -cne 'framework-catalog-project-view-selection' -or
        (@($projectSelection.packs | ForEach-Object id) -join ',') -cne $selectedPackId -or
        (@($projectSelection.capabilities | ForEach-Object id) -join ',') -cne $enabledCapabilityId
    ) {
        throw 'Framework catalog project-view selection changed.'
    }

    $frameworkConfig = Get-KnowledgeFrameworkConfig $actualRoot
    $selection = New-KnowledgeFrameworkCatalogSelection `
        $canonical `
        $frameworkConfig.lookup_keys `
        'NARRATIVE-MEDIA' `
        'NARRATIVE-TIME-LOOPS'
    if (@($selection.packs | ForEach-Object id) -cne 'narrative-media') {
        throw 'Normalized framework-catalog pack selection changed.'
    }
    if (@($selection.capabilities | ForEach-Object id) -cne 'narrative-time-loops') {
        throw 'Normalized framework-catalog capability selection changed.'
    }
    Assert-Rejected {
        New-KnowledgeFrameworkCatalogSelection `
            $canonical `
            $frameworkConfig.lookup_keys `
            'unknown-pack' `
            $null
    } 'Unknown framework-catalog pack ID'

    $ambiguous = [pscustomobject][ordered]@{
        contract_version = 1
        packs = @(
            [ordered]@{ id = 'ambiguous-pack'
                record_id = 'one'
            },
            [ordered]@{ id = 'AMBIGUOUS-PACK'
                record_id = 'two'
            }
        )
        capabilities = @()
    }
    Assert-Rejected {
        New-KnowledgeFrameworkCatalogSelection `
            $ambiguous `
            $frameworkConfig.lookup_keys `
            'Ambiguous-Pack' `
            $null
    } 'Ambiguous framework-catalog pack ID'

    $fixtureRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'fixture')
    $fixture = Get-KnowledgeFrameworkCatalog $fixtureRoot
    if ([int]$fixture.summary.pack_count -ne [int]$expectations.fixture_pack_count) {
        throw 'Fixture framework catalog pack count changed.'
    }
    if ([int]$fixture.summary.capability_count -ne [int]$expectations.fixture_capability_count) {
        throw 'Fixture framework catalog capability count changed.'
    }
    $extension = @($fixture.packs | Where-Object id -CEQ 'fixture-extension')[0]
    if (-not $extension.discoverability.installed -or $extension.discoverability.selectable) {
        throw 'Deferred pack discoverability changed.'
    }
    $shared = @($fixture.capabilities | Where-Object id -CEQ 'shared-capability')[0]
    if ((@($shared.providers | ForEach-Object pack_id) -join ',') -cne 'fixture-core,fixture-domain') {
        throw 'Multiple-provider capability order changed.'
    }
    if ($shared.effective_lifecycle -cne 'available') {
        throw 'Multiple-provider capability lifecycle changed.'
    }
    $planned = @($fixture.capabilities | Where-Object id -CEQ 'planned-capability')[0]
    $deprecated = @($fixture.capabilities | Where-Object id -CEQ 'deprecated-capability')[0]
    if (-not $planned.planned -or $planned.available) {
        throw 'Planned capability state changed.'
    }
    if (-not $deprecated.deprecated -or $deprecated.available) {
        throw 'Deprecated capability state changed.'
    }

    $missingRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'missing-dependency')
    Update-CatalogPack $missingRoot 'fixture-domain' {
        param($Value)
        $Value.dependencies = @([pscustomobject]@{ pack_id = 'missing-pack'
                minimum_version = 1
            })
    }
    Assert-Rejected {
        Get-KnowledgeFrameworkCatalog $missingRoot
    } 'requires missing pack' 'catalog-composition'
    $invalidCases++

    $versionRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'dependency-version')
    Update-CatalogPack $versionRoot 'fixture-domain' {
        param($Value)
        $Value.dependencies = @([pscustomobject]@{ pack_id = 'fixture-core'
                minimum_version = 99
            })
    }
    Assert-Rejected {
        Get-KnowledgeFrameworkCatalog $versionRoot
    } 'version 99 or newer' 'catalog-composition'
    $invalidCases++

    $cycleRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'dependency-cycle')
    Update-CatalogPack $cycleRoot 'fixture-core' {
        param($Value)
        $Value.dependencies = @([pscustomobject]@{ pack_id = 'fixture-domain'
                minimum_version = 1
            })
    }
    Assert-Rejected {
        Get-KnowledgeFrameworkCatalog $cycleRoot
    } 'dependency graph contains a cycle' 'catalog-composition'
    $invalidCases++

    $mismatchRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'directory-mismatch')
    Move-Item `
        -LiteralPath (Join-Path $mismatchRoot 'Framework\Packs\fixture-core') `
        -Destination (Join-Path $mismatchRoot 'Framework\Packs\wrong-name')
    Assert-Rejected { Get-KnowledgeFrameworkCatalog $mismatchRoot } 'wrong-name' 'pack-parsing'
    $invalidCases++

    $malformedRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'malformed-pack')
    Update-CatalogPack $malformedRoot 'fixture-core' {
        param($Value)
        $Value | Add-Member -NotePropertyName unknown_catalog_field -NotePropertyValue $true
    }
    Assert-Rejected {
        Get-KnowledgeFrameworkCatalog $malformedRoot
    } 'unsupported field' 'pack-parsing'
    $invalidCases++

    $discoveryRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'invalid-directory')
    Move-Item `
        -LiteralPath (Join-Path $discoveryRoot 'Framework\Packs\fixture-core') `
        -Destination (Join-Path $discoveryRoot 'Framework\Packs\Invalid_Directory')
    Assert-Rejected {
        Get-KnowledgeFrameworkCatalog $discoveryRoot
    } 'lowercase kebab-case' 'installed-pack-discovery'
    $invalidCases++

    $manifestRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'invalid-manifest')
    Write-Utf8NoBom `
    (Join-Path $manifestRoot 'Framework\framework.yaml') `
        "schema_version: 1`nunknown: true`n"
    Assert-Rejected {
        Get-KnowledgeFrameworkCatalog $manifestRoot
    } 'unsupported field' 'installation-manifest'
    $invalidCases++

    $lookupRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'invalid-lookup')
    Write-Utf8NoBom `
    (Join-Path $lookupRoot 'Framework\Data\unicode-lookup-16.0.0.json') `
        "{`"schema_version`": 1, `"unknown`": true}`n"
    Assert-Rejected {
        Get-KnowledgeFrameworkCatalog $lookupRoot
    } 'Lookup-key registry' 'lookup-registry'
    $invalidCases++

    $scaleRoot = New-CatalogRoot $actualRoot (Join-Path $tempRoot 'scale')
    Remove-Item -LiteralPath (Join-Path $scaleRoot 'Framework\Packs') -Recurse -Force
    for ($index = 0; $index -lt [int]$expectations.scale_pack_count; $index++) {
        $packId = 'scale-pack-{0:d3}' -f $index
        Write-JsonFixture `
        (Join-Path $scaleRoot "Framework\Packs\$packId\pack.yaml") `
        (New-ScalePack $index)
    }
    $scale = Get-KnowledgeFrameworkCatalog $scaleRoot
    if ([int]$scale.summary.pack_count -ne [int]$expectations.scale_pack_count) {
        throw 'Framework catalog scale pack count changed.'
    }
    if ([int]$scale.summary.capability_count -ne [int]$expectations.scale_pack_count) {
        throw 'Framework catalog scale capability count changed.'
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

if ($invalidCases -ne [int]$expectations.invalid_cases) {
    throw "Expected $($expectations.invalid_cases) invalid cases, got $invalidCases."
}

$result = [ordered]@{
    ambiguity_cases = 1
    canonical_capability_count = [int]$expectations.canonical_capability_count
    canonical_pack_count = [int]$expectations.canonical_pack_count
    fixture_capability_count = [int]$expectations.fixture_capability_count
    fixture_pack_count = [int]$expectations.fixture_pack_count
    invalid_cases = $invalidCases
    project_view_cases = 8
    scale_pack_count = [int]$expectations.scale_pack_count
    selection_cases = 3
}
if ($Json) {
    $result | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Framework-catalog conformance passed: ' +
        "$($result.canonical_pack_count) canonical packs, " +
        "$($result.canonical_capability_count) canonical capabilities, " +
        "$invalidCases invalid cases, $($result.scale_pack_count) scale packs."
    )
}
