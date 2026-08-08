[CmdletBinding()]
param(
    [Alias('?', 'h')]
    [switch]$Help,
    [string]$Root,
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
Inspect or export the generated EffectiveProjectSchema for a configured project.

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 [options]

Options:
  -Root <path>     Project root. When omitted, searches upward from the current
                   directory and this script's directory.
  -Json            Write canonical schema JSON to standard output.
  -Output <path>   Also write JSON beneath the project root.
  -ReportOutput <path>
                   Write the selected human-readable report beneath the
                   project root.
  -Show <section>  Append human output for overview, packs, capabilities,
                   namespaces, content, resources, diagnostics, or all.
                   Pass a comma-separated list to combine sections.
  -Pack <pack-id>  Inspect one selected pack by stable ID.
  -Capability <id> Inspect one declared capability by stable ID.
  -Help, -?, -h    Show this help and exit.

Examples:
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 -Json
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 -Show overview
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 -Show packs,capabilities
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 -Pack narrative-media
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 -Capability narrative-time-loops -Json
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 -Output .tmp\effective-schema.json
  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 -Show all -ReportOutput .local\effective-schema.txt
"@
}

function Resolve-EffectiveSchemaOutputPath {
    param(
        [string]$ProjectRoot,
        [string]$Value
    )

    $candidate = if ([System.IO.Path]::IsPathRooted($Value)) {
        [System.IO.Path]::GetFullPath($Value)
    }
    else {
        [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $Value))
    }
    $prefix = [System.IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if ($candidate -cne [System.IO.Path]::GetFullPath($ProjectRoot) -and -not $candidate.StartsWith(
            $prefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        throw "Output path must remain inside the project root: $candidate"
    }
    return $candidate
}

function Get-EffectiveSchemaDisplayValue {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value -or [string]::IsNullOrEmpty([string]$Value)) {
        return '-'
    }
    if ($Value -is [bool]) {
        return $Value.ToString().ToLowerInvariant()
    }
    return [string]$Value
}

function Write-EffectiveSchemaSummary {
    param(
        [object]$Schema,
        [bool]$IncludeDiagnosticRows = $true
    )

    $capabilities = @($Schema.capabilities)
    $enabled = @($capabilities | Where-Object enabled).Count
    $available = @($capabilities | Where-Object available).Count
    $planned = @($capabilities | Where-Object planned).Count
    $deprecated = @($capabilities | Where-Object deprecated).Count
    Write-Output "Effective project schema: $($Schema.project.project_id)"
    Write-Output "Contract: $($Schema.contract) v$($Schema.contract_version)"
    Write-Output "Framework/domain: $($Schema.project.framework_id) / $($Schema.project.domain_id)"
    Write-Output "Selected packs: $(@($Schema.packs).Count)"
    Write-Output (
        'Capabilities: {0} declared, {1} available, {2} enabled, {3} planned, {4} deprecated' -f
        $capabilities.Count,
        $available,
        $enabled,
        $planned,
        $deprecated
    )
    Write-Output "Controlled-value namespaces: $(@($Schema.controlled_value_namespaces).Count)"
    Write-Output (
        'Content: {0} roots, {1} types, {2} categories' -f
        @($Schema.content.roots).Count,
        @($Schema.content.content_types).Count,
        @($Schema.content.categories).Count
    )
    Write-Output (
        'Resources: {0} roots, {1} kinds, {2} types' -f
        @($Schema.resources.roots).Count,
        @($Schema.resources.kinds).Count,
        @($Schema.resources.types).Count
    )
    Write-Output "Diagnostics: $(@($Schema.diagnostics).Count)"
    if ($IncludeDiagnosticRows) {
        foreach ($diagnostic in @($Schema.diagnostics)) {
            Write-Output "  [$($diagnostic.severity)] $($diagnostic.code): $($diagnostic.message)"
        }
    }
}

function Write-EffectiveSchemaPresentationEntries {
    param(
        [string]$Label,
        [object[]]$Entries
    )

    Write-Output "  $Label ($(@($Entries).Count)):"
    if (@($Entries).Count -eq 0) {
        Write-Output '    - none'
    }
    foreach ($entry in @($Entries)) {
        Write-Output "    - $($entry.id) | $($entry.label): $($entry.description)"
    }
}

function Write-EffectiveSchemaOverview {
    param([object]$Schema)

    Write-Output 'Pack And Capability Overview'
    Write-Output "Selected Packs ($(@($Schema.packs).Count))"
    foreach ($row in @($Schema.packs)) {
        if ($null -eq $row.presentation) {
            $label = Get-EffectiveSchemaDisplayValue $row.label
            $description = Get-EffectiveSchemaDisplayValue $row.description
        }
        else {
            $label = $row.presentation.label
            $description = $row.presentation.short_description
        }
        Write-Output "- $label ($($row.id)): $description"
    }

    Write-Output "Capabilities ($(@($Schema.capabilities).Count))"
    foreach ($row in @($Schema.capabilities)) {
        if ($null -eq $row.presentation) {
            $label = Get-EffectiveSchemaDisplayValue $row.providers[0].label
            $description = Get-EffectiveSchemaDisplayValue $row.providers[0].description
        }
        else {
            $label = $row.presentation.label
            $description = $row.presentation.description
        }
        Write-Output "- $label ($($row.id)): $description"
    }
}

function Write-EffectiveSchemaPackRows {
    param(
        [object[]]$Rows,
        [string]$Heading
    )

    Write-Output "$Heading ($(@($Rows).Count))"
    foreach ($row in @($Rows)) {
        Write-Output (
            "- $($row.id) | lifecycle=$($row.lifecycle) | kind=$($row.kind) | " +
            "schema=$($row.schema_version) | version=$($row.pack_version)"
        )
        if ($null -eq $row.classification) {
            Write-Output '  classification: legacy / unavailable'
        }
        else {
            $domains = @($row.classification.domains) -join ','
            if ([string]::IsNullOrEmpty($domains)) {
                $domains = 'none'
            }
            $joins = @($row.classification.bridge_pack_ids) -join ','
            if ([string]::IsNullOrEmpty($joins)) {
                $joins = 'none'
            }
            Write-Output (
                "  classification: family=$($row.classification.family) | role=$($row.classification.role) | " +
                "scope=$($row.classification.scope) | domains=$domains | joins=$joins"
            )
        }
        if ($null -eq $row.presentation) {
            Write-Output "  label: $(Get-EffectiveSchemaDisplayValue $row.label)"
            Write-Output "  description: $(Get-EffectiveSchemaDisplayValue $row.description)"
        }
        else {
            Write-Output (
                "  presentation: key=$($row.presentation.localization_key) | " +
                "locale=$($row.presentation.default_locale) | maturity=$($row.presentation.maturity)"
            )
            Write-Output "  label: $($row.presentation.label)"
            Write-Output "  short description: $($row.presentation.short_description)"
            Write-Output "  long description: $($row.presentation.long_description)"
            $keywords = @($row.presentation.search_keywords) -join ', '
            if ([string]::IsNullOrEmpty($keywords)) {
                $keywords = 'none'
            }
            Write-Output "  search keywords: $keywords"
            if ($null -eq $row.presentation.visual) {
                Write-Output '  visual: none'
            }
            else {
                Write-Output (
                    "  visual: icon=$(Get-EffectiveSchemaDisplayValue $row.presentation.visual.icon_id) | " +
                    "accent=$(Get-EffectiveSchemaDisplayValue $row.presentation.visual.accent_token)"
                )
            }
            Write-EffectiveSchemaPresentationEntries 'intended audiences' $row.presentation.intended_audiences
            Write-EffectiveSchemaPresentationEntries 'use cases' $row.presentation.use_cases
            Write-EffectiveSchemaPresentationEntries 'examples' $row.presentation.examples
            Write-EffectiveSchemaPresentationEntries 'prerequisites' $row.presentation.prerequisites
            Write-EffectiveSchemaPresentationEntries 'provided behaviors' $row.presentation.provided_behaviors
            Write-EffectiveSchemaPresentationEntries 'exclusions' $row.presentation.exclusions
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
        $dependencies = @($row.dependencies)
        if ($dependencies.Count -eq 0) {
            Write-Output '  dependencies: none'
        }
        else {
            $values = @(
                $dependencies | ForEach-Object {
                    "$($_.pack_id)>=v$($_.minimum_version) (selected v$($_.selected_version), $($_.status))"
                }
            ) -join ', '
            Write-Output "  dependencies: $values"
        }
    }
}

function Write-EffectiveSchemaPacks {
    param([object]$Schema)

    Write-EffectiveSchemaPackRows @($Schema.packs) 'Selected Packs'
}

function Write-EffectiveSchemaCapabilityRows {
    param(
        [object[]]$Rows,
        [string]$Heading
    )

    Write-Output "$Heading ($(@($Rows).Count))"
    foreach ($row in @($Rows)) {
        $providerIds = @($row.providers | ForEach-Object pack_id) -join ','
        Write-Output (
            "- $($row.id) | lifecycle=$($row.effective_lifecycle) | " +
            "available=$(Get-EffectiveSchemaDisplayValue $row.available) | " +
            "enabled=$(Get-EffectiveSchemaDisplayValue $row.enabled) | " +
            "deprecated=$(Get-EffectiveSchemaDisplayValue $row.deprecated) | providers=$providerIds"
        )
        if ($null -eq $row.presentation) {
            Write-Output '  presentation: legacy / unavailable'
        }
        else {
            Write-Output "  presentation key: $($row.presentation.localization_key)"
            Write-Output "  label: $($row.presentation.label)"
            Write-Output "  description: $($row.presentation.description)"
        }
        foreach ($provider in @($row.providers)) {
            Write-Output (
                "  - $($provider.pack_id) | lifecycle=$($provider.lifecycle) | " +
                "label=$(Get-EffectiveSchemaDisplayValue $provider.label) | " +
                "description=$(Get-EffectiveSchemaDisplayValue $provider.description)"
            )
            if ($null -ne $provider.presentation) {
                Write-Output "    presentation key: $($provider.presentation.localization_key)"
            }
        }
    }
}

function Write-EffectiveSchemaCapabilities {
    param([object]$Schema)

    Write-EffectiveSchemaCapabilityRows @($Schema.capabilities) 'Capabilities'
}

function Write-EffectiveSchemaNamespaces {
    param([object]$Schema)

    Write-Output "Controlled-Value Namespaces ($(@($Schema.controlled_value_namespaces).Count))"
    foreach ($namespace in @($Schema.controlled_value_namespaces)) {
        Write-Output "- $($namespace.id) | values=$(@($namespace.values).Count)"
        foreach ($row in @($namespace.values)) {
            Write-Output (
                "  - $($row.id) | owner=$($row.owner_pack_id) | " +
                "broader=$(Get-EffectiveSchemaDisplayValue $row.broader_value_id) | " +
                "label=$(Get-EffectiveSchemaDisplayValue $row.label) | " +
                "description=$(Get-EffectiveSchemaDisplayValue $row.description)"
            )
        }
    }
}

function Write-EffectiveSchemaContent {
    param([object]$Schema)

    Write-Output 'Content'
    Write-Output "Roots ($(@($Schema.content.roots).Count))"
    foreach ($row in @($Schema.content.roots)) {
        Write-Output (
            "- $($row.id) | path=$($row.relative_path) | provenance=$($row.provenance_mode) | " +
            "label=$(Get-EffectiveSchemaDisplayValue $row.provenance_label)"
        )
    }
    Write-Output "Content Types ($(@($Schema.content.content_types).Count))"
    foreach ($row in @($Schema.content.content_types)) {
        Write-Output (
            "- $($row.id) | lifecycle=$($row.lifecycle) | " +
            "root=$(Get-EffectiveSchemaDisplayValue $row.content_root_id) | categories=$($row.category_policy) | " +
            "graph=$(Get-EffectiveSchemaDisplayValue $row.graph_enabled) | " +
            "qa=$(Get-EffectiveSchemaDisplayValue $row.qa_page_enabled) | " +
            "template=$(Get-EffectiveSchemaDisplayValue $row.default_template)"
        )
    }
    Write-Output "Categories ($(@($Schema.content.categories).Count))"
    foreach ($row in @($Schema.content.categories)) {
        Write-Output (
            "- $($row.id) | lifecycle=$($row.lifecycle) | " +
            "graph_class=$(Get-EffectiveSchemaDisplayValue $row.graph_class) | placements=$(@($row.placements).Count)"
        )
        foreach ($placement in @($row.placements)) {
            Write-Output (
                "  - $($placement.content_type_id) | " +
                "folder=$(Get-EffectiveSchemaDisplayValue $placement.relative_folder) | " +
                "template=$(Get-EffectiveSchemaDisplayValue $placement.template)"
            )
        }
    }
}

function Write-EffectiveSchemaResources {
    param([object]$Schema)

    Write-Output 'Resources'
    Write-Output "Roots ($(@($Schema.resources.roots).Count))"
    foreach ($row in @($Schema.resources.roots)) {
        Write-Output (
            "- $($row.id) | path=$($row.relative_path) | required=$(Get-EffectiveSchemaDisplayValue $row.required)"
        )
    }
    Write-Output "Kinds ($(@($Schema.resources.kinds).Count))"
    foreach ($row in @($Schema.resources.kinds)) {
        Write-Output "- $($row.id) | label=$($row.label) | plural=$($row.plural_label)"
    }
    Write-Output "Types ($(@($Schema.resources.types).Count))"
    foreach ($row in @($Schema.resources.types)) {
        Write-Output (
            "- $($row.id) | lifecycle=$($row.lifecycle) | kind=$($row.kind_id) | authority=$($row.authority) | " +
            "editor=$(Get-EffectiveSchemaDisplayValue $row.editor_enabled) | placements=$(@($row.placements).Count)"
        )
        foreach ($placement in @($row.placements)) {
            Write-Output (
                "  - $($placement.root_id) | path=$($placement.relative_path) | tracking=$($placement.tracking) | " +
                "required=$(Get-EffectiveSchemaDisplayValue $placement.required)"
            )
        }
    }
}

function Write-EffectiveSchemaDiagnostics {
    param([object]$Schema)

    $diagnostics = @($Schema.diagnostics)
    Write-Output "Diagnostics ($($diagnostics.Count))"
    if ($diagnostics.Count -eq 0) {
        Write-Output '- none'
    }
    foreach ($row in $diagnostics) {
        $relatedIds = @($row.related_ids) -join ','
        if ([string]::IsNullOrEmpty($relatedIds)) {
            $relatedIds = '-'
        }
        Write-Output (
            "- [$($row.severity)] $($row.code) | path=$(Get-EffectiveSchemaDisplayValue $row.path) | " +
            "related=$relatedIds"
        )
        Write-Output "  $($row.message)"
    }
}

function Get-EffectiveSchemaShowSections {
    param([string]$Value)

    $available = @('overview', 'packs', 'capabilities', 'namespaces', 'content', 'resources', 'diagnostics')
    $allSections = @('packs', 'capabilities', 'namespaces', 'content', 'resources', 'diagnostics')
    $selected = @()
    $values = if ([string]::IsNullOrWhiteSpace($Value)) {
        @()
    }
    else {
        @($Value.Split(','))
    }
    foreach ($requested in $values) {
        $requested = $requested.Trim()
        if ($requested -cnotin @($available + 'all')) {
            throw "Unknown effective-schema section ``$requested``; choose from: $($available -join ', '), all."
        }
        $candidates = if ($requested -eq 'all') {
            $allSections
        }
        else {
            @($requested)
        }
        foreach ($candidate in $candidates) {
            if ($selected -cnotcontains $candidate) {
                $selected += $candidate
            }
        }
    }
    return @($selected)
}

function Write-EffectiveSchemaReport {
    param(
        [object]$Schema,
        [string[]]$Sections,
        [AllowNull()][object]$Selection
    )

    Write-EffectiveSchemaSummary $Schema ($Sections -cnotcontains 'diagnostics')
    foreach ($section in $Sections) {
        Write-Output ''
        switch ($section) {
            'overview' {
                Write-EffectiveSchemaOverview $Schema
            }
            'packs' {
                Write-EffectiveSchemaPacks $Schema
            }
            'capabilities' {
                Write-EffectiveSchemaCapabilities $Schema
            }
            'namespaces' {
                Write-EffectiveSchemaNamespaces $Schema
            }
            'content' {
                Write-EffectiveSchemaContent $Schema
            }
            'resources' {
                Write-EffectiveSchemaResources $Schema
            }
            'diagnostics' {
                Write-EffectiveSchemaDiagnostics $Schema
            }
        }
    }
    if ($null -ne $Selection) {
        if (@($Selection.packs).Count -gt 0) {
            Write-Output ''
            Write-EffectiveSchemaPackRows @($Selection.packs) 'Pack Inspection'
        }
        if (@($Selection.capabilities).Count -gt 0) {
            Write-Output ''
            Write-EffectiveSchemaCapabilityRows @($Selection.capabilities) 'Capability Inspection'
        }
    }
}

if ($Help) {
    Show-Help
    exit 0
}

try {
    $resolvedRoot = Resolve-KnowledgeProjectRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
    $project = Get-KnowledgeProjectConfig $resolvedRoot
    $schema = Get-KnowledgeEffectiveProjectSchema -Root $resolvedRoot
    $selection = if (
        -not [string]::IsNullOrWhiteSpace($Pack) -or
        -not [string]::IsNullOrWhiteSpace($Capability)
    ) {
        New-KnowledgeEffectiveSchemaSelection `
            $schema `
        (Get-KnowledgeLookupKeyConfig $project) `
            $Pack `
            $Capability
    }
    else {
        $null
    }
    $serialized = ConvertTo-KnowledgeCanonicalJson $(if ($null -eq $selection) {
            $schema
        }
        else {
            $selection
        })
    $sections = @(Get-EffectiveSchemaShowSections $Show)
    if (-not [string]::IsNullOrWhiteSpace($Output)) {
        $outputPath = Resolve-EffectiveSchemaOutputPath $resolvedRoot $Output
        $parent = [System.IO.Path]::GetDirectoryName($outputPath)
        if (-not [string]::IsNullOrWhiteSpace($parent)) {
            [System.IO.Directory]::CreateDirectory($parent) | Out-Null
        }
        [System.IO.File]::WriteAllText($outputPath, $serialized, [System.Text.UTF8Encoding]::new($false))
    }
    if (-not [string]::IsNullOrWhiteSpace($ReportOutput)) {
        $reportOutputPath = Resolve-EffectiveSchemaOutputPath $resolvedRoot $ReportOutput
        $parent = [System.IO.Path]::GetDirectoryName($reportOutputPath)
        if (-not [string]::IsNullOrWhiteSpace($parent)) {
            [System.IO.Directory]::CreateDirectory($parent) | Out-Null
        }
        $reportLines = @(Write-EffectiveSchemaReport $schema $sections $selection)
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
            Write-EffectiveSchemaReport $schema $sections $selection
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
    if ($Json) {
        [Console]::Out.Write((ConvertTo-KnowledgeCanonicalJson (New-KnowledgeEffectiveSchemaFailure $_.Exception)))
    }
    else {
        [Console]::Error.WriteLine("Effective-schema composition failed: $($_.Exception.Message)")
    }
    exit 1
}
