[CmdletBinding()]
param(
    [Alias('?', 'h')]
    [switch]$Help,
    [string]$Root,
    [string]$ProjectRoot,
    [switch]$Json,
    [string]$Output,
    [string]$ReportOutput,
    [string]$Show,
    [string]$Pack,
    [string]$Capability
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

function Show-Help {
    @"
Inspect or export the generated project-independent FrameworkCatalog.

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 [options]

Options:
  -Root <path>     Framework repository root. When omitted, searches upward
                   from the current directory and this script's directory.
  -ProjectRoot <path>
                   Attach a project and emit a FrameworkCatalogProjectView.
  -Json            Write canonical catalog JSON to standard output.
  -Output <path>   Also write JSON beneath the framework root.
  -ReportOutput <path>
                   Write the selected human-readable report beneath the
                   framework root.
  -Show <section>  Append human output for overview, packs, capabilities, or
                   all. Pass a comma-separated list to combine sections.
  -Pack <pack-id>  Inspect one installed pack by stable ID.
  -Capability <id> Inspect one capability by stable ID.
  -Help, -?, -h    Show this help and exit.

Examples:
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -Json
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -Show overview
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -Show packs,capabilities
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -Pack narrative-media
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -Capability narrative-time-loops -Json
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -ProjectRoot . -Show overview
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -Output .tmp\framework-catalog.json
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-FrameworkCatalog.ps1 -Show all -ReportOutput .local\framework-catalog.txt
"@
}

function Resolve-FrameworkCatalogOutputPath {
    param([string]$FrameworkRoot, [string]$Value)

    $candidate = if ([System.IO.Path]::IsPathRooted($Value)) {
        [System.IO.Path]::GetFullPath($Value)
    }
    else {
        [System.IO.Path]::GetFullPath((Join-Path $FrameworkRoot $Value))
    }
    $resolvedRoot = [System.IO.Path]::GetFullPath($FrameworkRoot).TrimEnd('\', '/')
    $prefix = $resolvedRoot + [System.IO.Path]::DirectorySeparatorChar
    if ($candidate -ceq $resolvedRoot -or -not $candidate.StartsWith(
            $prefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        throw "Output path must resolve to a file beneath the framework root: $candidate"
    }
    return $candidate
}

function Get-FrameworkCatalogDisplayValue {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value -or [string]::IsNullOrEmpty([string]$Value)) {
        return '-'
    }
    if ($Value -is [bool]) {
        return $Value.ToString().ToLowerInvariant()
    }
    return [string]$Value
}

function Write-FrameworkCatalogSummary {
    param([object]$Catalog)

    if ($Catalog.contract -ceq 'framework-catalog-project-view') {
        Write-Output "Framework catalog project view: $($Catalog.project.project_id)"
        Write-Output "Contract: $($Catalog.contract) v$($Catalog.contract_version)"
        Write-Output "Framework: $($Catalog.project.framework_id)"
        Write-Output "Domain: $($Catalog.project.domain_id)"
        Write-Output (
            "Packs: $($Catalog.summary.selected_pack_count) selected of " +
            "$($Catalog.summary.pack_count) installed"
        )
        Write-Output (
            "Capabilities: $($Catalog.summary.enabled_capability_count) enabled, " +
            "$($Catalog.summary.selected_capability_count) selected, " +
            "$($Catalog.summary.capability_count) installed"
        )
        return
    }
    Write-Output "Framework catalog: $($Catalog.framework.id)"
    Write-Output "Contract: $($Catalog.contract) v$($Catalog.contract_version)"
    Write-Output "Manifest: $($Catalog.framework.manifest_path)"
    Write-Output "Pack root: $($Catalog.framework.packs_root)"
    Write-Output (
        "Lookup registry: $($Catalog.framework.lookup_registry) " +
        "($($Catalog.framework.unicode_version))"
    )
    Write-Output "Installed packs: $($Catalog.summary.pack_count)"
    Write-Output (
        "Capabilities: $($Catalog.summary.capability_count) declared, " +
        "$($Catalog.summary.available_capability_count) available, " +
        "$($Catalog.summary.planned_capability_count) planned, " +
        "$($Catalog.summary.deprecated_capability_count) deprecated"
    )
}

function Write-FrameworkCatalogOverview {
    param([object]$Catalog)

    Write-Output "Installed Packs ($(@($Catalog.packs).Count))"
    foreach ($row in @($Catalog.packs)) {
        $label = if ($null -eq $row.presentation) {
            $row.id
        }
        else {
            $row.presentation.label
        }
        $description = if ($null -eq $row.presentation) {
            '-'
        }
        else {
            $row.presentation.short_description
        }
        $selectable = Get-FrameworkCatalogDisplayValue $row.discoverability.selectable
        $projectText = if ($null -eq $row.project_state) {
            ''
        }
        else {
            ' | selected=' + (Get-FrameworkCatalogDisplayValue $row.project_state.selected)
        }
        Write-Output (
            "- $label ($($row.id)) | lifecycle=$($row.lifecycle) | " +
            "selectable=$selectable$projectText`: $description"
        )
    }
}

function Write-FrameworkCatalogPresentationEntries {
    param([string]$Label, [object[]]$Entries)

    Write-Output "  $Label ($(@($Entries).Count)):"
    if (@($Entries).Count -eq 0) {
        Write-Output '    - none'
    }
    foreach ($entry in @($Entries)) {
        Write-Output "    - $($entry.id) | $($entry.label): $($entry.description)"
    }
}

function Write-FrameworkCatalogPackRows {
    param([object[]]$Rows, [string]$Heading)

    Write-Output "$Heading ($(@($Rows).Count))"
    foreach ($row in @($Rows)) {
        $selectable = Get-FrameworkCatalogDisplayValue $row.discoverability.selectable
        Write-Output (
            "- $($row.id) | lifecycle=$($row.lifecycle) | kind=$($row.kind) | " +
            "schema=$($row.schema_version) | version=$($row.pack_version) | selectable=$selectable"
        )
        if ($null -ne $row.project_state) {
            Write-Output (
                '  project state: ' +
                "selected=$(Get-FrameworkCatalogDisplayValue $row.project_state.selected) | " +
                "available=$(Get-FrameworkCatalogDisplayValue $row.project_state.available) | " +
                "enabled=$(Get-FrameworkCatalogDisplayValue $row.project_state.enabled) | " +
                "planned=$(Get-FrameworkCatalogDisplayValue $row.project_state.planned) | " +
                "used=$(Get-FrameworkCatalogDisplayValue $row.project_state.used_by_project) | " +
                "unavailable=$(Get-FrameworkCatalogDisplayValue $row.project_state.unavailable_reason)"
            )
        }
        Write-Output "  path: $($row.path)"
        if ($null -eq $row.classification) {
            Write-Output '  classification: legacy / unavailable'
        }
        else {
            $domains = if (@($row.classification.domains).Count -eq 0) {
                'none'
            }
            else {
                @($row.classification.domains) -join ','
            }
            $bridges = if (@($row.classification.bridge_pack_ids).Count -eq 0) {
                'none'
            }
            else {
                @($row.classification.bridge_pack_ids) -join ','
            }
            Write-Output (
                "  classification: family=$($row.classification.family) | " +
                "role=$($row.classification.role) | scope=$($row.classification.scope) | " +
                "domains=$domains | bridges=$bridges"
            )
        }
        if ($null -eq $row.presentation) {
            Write-Output '  presentation: unavailable'
        }
        else {
            Write-Output (
                "  presentation: key=$($row.presentation.localization_key) | " +
                "locale=$($row.presentation.default_locale) | maturity=$($row.presentation.maturity)"
            )
            Write-Output "  label: $($row.presentation.label)"
            Write-Output "  short description: $($row.presentation.short_description)"
            Write-Output "  long description: $($row.presentation.long_description)"
            $keywords = if (@($row.presentation.search_keywords).Count -eq 0) {
                'none'
            }
            else {
                @($row.presentation.search_keywords) -join ', '
            }
            Write-Output "  search keywords: $keywords"
            if ($null -eq $row.presentation.visual) {
                Write-Output '  visual: none'
            }
            else {
                $icon = Get-FrameworkCatalogDisplayValue $row.presentation.visual.icon_id
                $accent = Get-FrameworkCatalogDisplayValue $row.presentation.visual.accent_token
                Write-Output "  visual: icon=$icon | accent=$accent"
            }
            Write-FrameworkCatalogPresentationEntries 'intended audiences' $row.presentation.intended_audiences
            Write-FrameworkCatalogPresentationEntries 'use cases' $row.presentation.use_cases
            Write-FrameworkCatalogPresentationEntries 'examples' $row.presentation.examples
            Write-FrameworkCatalogPresentationEntries 'prerequisites' $row.presentation.prerequisites
            Write-FrameworkCatalogPresentationEntries 'provided behaviors' $row.presentation.provided_behaviors
            Write-FrameworkCatalogPresentationEntries 'exclusions' $row.presentation.exclusions
            Write-Output "  documentation ($(@($row.presentation.documentation).Count)):"
            if (@($row.presentation.documentation).Count -eq 0) {
                Write-Output '    - none'
            }
            foreach ($entry in @($row.presentation.documentation)) {
                Write-Output (
                    "    - $($entry.id) | $($entry.label) | " +
                    "$($entry.target_kind)=$($entry.target)"
                )
            }
        }
        Write-Output "  dependencies ($(@($row.dependencies).Count)):"
        if (@($row.dependencies).Count -eq 0) {
            Write-Output '    - none'
        }
        foreach ($dependency in @($row.dependencies)) {
            Write-Output (
                "    - $($dependency.pack_id) | minimum=$($dependency.minimum_version) | " +
                "installed=$($dependency.installed_version) | status=$($dependency.status)"
            )
        }
        Write-Output "  capabilities ($(@($row.capability_ids).Count)):"
        foreach ($capabilityId in @($row.capability_ids)) {
            Write-Output "    - $capabilityId"
        }
        Write-Output "  controlled-value namespaces ($(@($row.controlled_value_namespaces).Count)):"
        if (@($row.controlled_value_namespaces).Count -eq 0) {
            Write-Output '    - none'
        }
        foreach ($namespace in @($row.controlled_value_namespaces)) {
            Write-Output "    - $($namespace.id) ($(@($namespace.values).Count))"
            foreach ($value in @($namespace.values)) {
                $broader = Get-FrameworkCatalogDisplayValue $value.broader_value
                $label = Get-FrameworkCatalogDisplayValue $value.label
                $description = Get-FrameworkCatalogDisplayValue $value.description
                Write-Output (
                    "      - $($value.id) | broader=$broader | label=$label | " +
                    "description=$description"
                )
            }
        }
    }
}

function Write-FrameworkCatalogCapabilityRows {
    param([object[]]$Rows, [string]$Heading)

    Write-Output "$Heading ($(@($Rows).Count))"
    foreach ($row in @($Rows)) {
        $available = Get-FrameworkCatalogDisplayValue $row.available
        $deprecated = Get-FrameworkCatalogDisplayValue $row.deprecated
        $planned = Get-FrameworkCatalogDisplayValue $row.planned
        Write-Output (
            "- $($row.id) | lifecycle=$($row.effective_lifecycle) | available=$available | " +
            "deprecated=$deprecated | planned=$planned"
        )
        if ($null -ne $row.project_state) {
            Write-Output (
                '  project state: ' +
                "selected=$(Get-FrameworkCatalogDisplayValue $row.project_state.selected) | " +
                "available=$(Get-FrameworkCatalogDisplayValue $row.project_state.available) | " +
                "enabled=$(Get-FrameworkCatalogDisplayValue $row.project_state.enabled) | " +
                "deprecated=$(Get-FrameworkCatalogDisplayValue $row.project_state.deprecated) | " +
                "planned=$(Get-FrameworkCatalogDisplayValue $row.project_state.planned) | " +
                "used=$(Get-FrameworkCatalogDisplayValue $row.project_state.used_by_project) | " +
                "unavailable=$(Get-FrameworkCatalogDisplayValue $row.project_state.unavailable_reason)"
            )
        }
        $label = if ($null -eq $row.presentation) {
            $row.id
        }
        else {
            $row.presentation.label
        }
        $description = if ($null -eq $row.presentation) {
            '-'
        }
        else {
            $row.presentation.description
        }
        Write-Output "  label: $label"
        Write-Output "  description: $description"
        if ($null -ne $row.presentation) {
            Write-Output "  presentation key: $($row.presentation.localization_key)"
        }
        Write-Output "  providers ($(@($row.providers).Count)):"
        foreach ($provider in @($row.providers)) {
            $providerLabel = if ($null -eq $provider.presentation) {
                $provider.pack_id
            }
            else {
                $provider.presentation.label
            }
            Write-Output (
                "    - $($provider.pack_id) | lifecycle=$($provider.lifecycle) | " +
                "label=$providerLabel"
            )
        }
    }
}

function Get-FrameworkCatalogShowSections {
    param([string]$Value)

    $sections = @()
    if (-not [string]::IsNullOrWhiteSpace($Value)) {
        foreach ($entry in @($Value -split ',')) {
            $section = $entry.Trim()
            if ($section -cnotin @('overview', 'packs', 'capabilities', 'all')) {
                throw (
                    "Unknown framework-catalog section ``$section``; choose from: " +
                    'overview, packs, capabilities, all.'
                )
            }
            $candidates = if ($section -ceq 'all') {
                @('packs', 'capabilities')
            }
            else {
                @($section)
            }
            foreach ($candidate in $candidates) {
                if ($candidate -cnotin $sections) {
                    $sections += $candidate
                }
            }
        }
    }
    return @($sections)
}

function Write-FrameworkCatalogReport {
    param([object]$Catalog, [string[]]$Sections, [AllowNull()][object]$Selection)

    Write-FrameworkCatalogSummary $Catalog
    foreach ($section in @($Sections)) {
        Write-Output ''
        switch ($section) {
            'overview' {
                Write-FrameworkCatalogOverview $Catalog
            }
            'packs' {
                Write-FrameworkCatalogPackRows @($Catalog.packs) 'Packs'
            }
            'capabilities' {
                Write-FrameworkCatalogCapabilityRows @($Catalog.capabilities) 'Capabilities'
            }
        }
    }
    if ($null -ne $Selection) {
        if (@($Selection.packs).Count -gt 0) {
            Write-Output ''
            Write-FrameworkCatalogPackRows @($Selection.packs) 'Pack Inspection'
        }
        if (@($Selection.capabilities).Count -gt 0) {
            Write-Output ''
            Write-FrameworkCatalogCapabilityRows @($Selection.capabilities) 'Capability Inspection'
        }
    }
}

if ($Help) {
    Show-Help
    exit 0
}

$classification = 'root-discovery'
$resolvedRoot = $null
try {
    $resolvedRoot = Resolve-KnowledgeFrameworkRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
    $classification = 'catalog-composition'
    $frameworkConfig = Get-KnowledgeFrameworkConfig $resolvedRoot
    $catalog = Get-KnowledgeFrameworkCatalog $resolvedRoot
    $document = $catalog
    if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) {
        $classification = 'project-attachment'
        $resolvedProjectRoot = Resolve-KnowledgeProjectRoot `
            -ExplicitRoot $ProjectRoot `
            -ExecutablePath $PSCommandPath
        $effectiveSchema = Get-KnowledgeEffectiveProjectSchema $resolvedProjectRoot
        $document = New-KnowledgeFrameworkCatalogProjectView $catalog $effectiveSchema
    }
    $selection = if (
        -not [string]::IsNullOrWhiteSpace($Pack) -or
        -not [string]::IsNullOrWhiteSpace($Capability)
    ) {
        $classification = 'selector'
        if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
            New-KnowledgeFrameworkCatalogSelection `
                $catalog `
                $frameworkConfig.lookup_keys `
                $Pack `
                $Capability
        }
        else {
            New-KnowledgeFrameworkCatalogProjectViewSelection `
                $catalog `
                $document `
                $frameworkConfig.lookup_keys `
                $Pack `
                $Capability
        }
    }
    else {
        $null
    }
    $classification = 'catalog-composition'
    $serialized = ConvertTo-KnowledgeCanonicalJson $(if ($null -eq $selection) {
            $document
        }
        else {
            $selection
        })
    $sections = @(Get-FrameworkCatalogShowSections $Show)
    if (-not [string]::IsNullOrWhiteSpace($Output)) {
        $classification = 'output-path'
        $outputPath = Resolve-FrameworkCatalogOutputPath $resolvedRoot $Output
        $parent = [System.IO.Path]::GetDirectoryName($outputPath)
        if (-not [string]::IsNullOrWhiteSpace($parent)) {
            [System.IO.Directory]::CreateDirectory($parent) | Out-Null
        }
        [System.IO.File]::WriteAllText($outputPath, $serialized, [System.Text.UTF8Encoding]::new($false))
    }
    if (-not [string]::IsNullOrWhiteSpace($ReportOutput)) {
        $classification = 'output-path'
        $reportOutputPath = Resolve-FrameworkCatalogOutputPath $resolvedRoot $ReportOutput
        $parent = [System.IO.Path]::GetDirectoryName($reportOutputPath)
        if (-not [string]::IsNullOrWhiteSpace($parent)) {
            [System.IO.Directory]::CreateDirectory($parent) | Out-Null
        }
        $reportLines = @(Write-FrameworkCatalogReport $document $sections $selection)
        $reportText = ($reportLines -join "`n") + "`n"
        [System.IO.File]::WriteAllText(
            $reportOutputPath,
            $reportText,
            [System.Text.UTF8Encoding]::new($false)
        )
    }
    if ($Json) {
        [Console]::Out.Write($serialized)
    }
    else {
        if ([string]::IsNullOrWhiteSpace($ReportOutput)) {
            Write-FrameworkCatalogReport $document $sections $selection
        }
        if (-not [string]::IsNullOrWhiteSpace($Output)) {
            $relative = $outputPath.Substring($resolvedRoot.TrimEnd('\', '/').Length + 1).Replace('\', '/')
            Write-Output "Exported JSON: $relative"
        }
        if (-not [string]::IsNullOrWhiteSpace($ReportOutput)) {
            $relative = $reportOutputPath.Substring($resolvedRoot.TrimEnd('\', '/').Length + 1).Replace('\', '/')
            Write-Output "Exported report: $relative"
        }
    }
    exit 0
}
catch {
    if ($_.Exception.Data.Contains('FrameworkCatalogClassification')) {
        $classification = [string]$_.Exception.Data['FrameworkCatalogClassification']
    }
    if ($Json) {
        $message = if ($classification -ceq 'root-discovery') {
            'Framework root discovery failed.'
        }
        elseif ($classification -ceq 'output-path') {
            'Framework catalog output path is invalid.'
        }
        else {
            $value = $_.Exception.Message
            if (-not [string]::IsNullOrWhiteSpace($resolvedRoot)) {
                $value = $value.Replace($resolvedRoot, '.')
            }
            $value
        }
        $failure = New-KnowledgeFrameworkCatalogFailure $_.Exception $classification $message
        [Console]::Out.Write((ConvertTo-KnowledgeCanonicalJson $failure))
    }
    else {
        [Console]::Error.WriteLine("Framework-catalog composition failed: $($_.Exception.Message)")
    }
    exit 1
}
