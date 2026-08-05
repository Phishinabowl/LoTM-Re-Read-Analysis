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
$targetPaths = @{
    registry = 'registry.json'
    'fixture-core' = 'packs\fixture-core.json'
    'fixture-domain' = 'packs\fixture-domain.json'
    'fixture-extension' = 'packs\fixture-extension.json'
}

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
        [object]$Operation
    )

    $location = Get-FixtureMutationParent $Document @($Operation.path)
    $operationValue = if ($Operation.PSObject.Properties.Name -ccontains 'value') {
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

function Assert-ValidSchemaPackFixture {
    param(
        [object]$Registry,
        [object]$Expected
    )

    if ((@($Registry.selection_order) -join '|') -cne (@($Expected.selection_order) -join '|')) {
        throw 'Schema-pack fixture selection order changed.'
    }
    if (@($Registry.declared_capabilities).Count -ne [int]$Expected.declared_capabilities) {
        throw 'Schema-pack declared capability count changed.'
    }
    if (@($Registry.available_capabilities).Count -ne [int]$Expected.available_capabilities) {
        throw 'Schema-pack available capability count changed.'
    }
    if (@($Registry.enabled_capabilities).Count -ne [int]$Expected.enabled_capabilities) {
        throw 'Schema-pack enabled capability count changed.'
    }
    if (
        (@($Registry.capability_providers['shared-capability']) -join '|') -cne
        (@($Expected.shared_capability_providers) -join '|')
    ) {
        throw 'Schema-pack multiple-provider composition changed.'
    }
    if (
        (@(Get-SchemaPackAllowedValues $Registry 'fixture.kind') -join '|') -cne
        (@($Expected.kind_values) -join '|')
    ) {
        throw 'Schema-pack cross-pack controlled-value order changed.'
    }
    if (
        (@(Get-SchemaPackAllowedValues $Registry 'fixture.mode') -join '|') -cne
        (@($Expected.mode_values) -join '|')
    ) {
        throw 'Schema-pack extension values changed.'
    }
    if ([string]$Registry.controlled_value_owners['fixture.kind|domain-kind'] -cne [string]$Expected.domain_kind_owner) {
        throw 'Schema-pack controlled-value ownership changed.'
    }
    $definition = Get-SchemaPackValueDefinition $Registry 'fixture.kind' 'domain-kind'
    if ($null -eq $definition -or [string]$definition.broader_value -cne [string]$Expected.domain_kind_broader) {
        throw 'Schema-pack cross-pack broader-value resolution changed.'
    }
    if (Test-SchemaPackCapabilityAvailable $Registry 'planned-capability') {
        throw 'Planned schema-pack capability became available.'
    }
    if (Test-SchemaPackCapabilityEnabled $Registry 'planned-capability') {
        throw 'Planned schema-pack capability became enabled.'
    }
    if (-not (Test-SchemaPackCapabilityAvailable $Registry 'deprecated-capability')) {
        throw 'Deprecated schema-pack capability lost compatibility availability.'
    }
    foreach ($property in $Expected.semantic_declarations.PSObject.Properties) {
        if ([int]$Registry.($property.Name).Count -ne [int]$property.Value) {
            throw "Schema-pack typed semantic count changed for '$($property.Name)'."
        }
    }
}

function New-ScaleSchemaPackFixture {
    param(
        [string]$FixtureRoot,
        [int]$PackCount
    )

    $packsRoot = Join-Path $FixtureRoot 'packs'
    $null = New-Item -ItemType Directory -Path $packsRoot -Force
    $selections = @()
    $enabled = @()
    for ($index = 0; $index -lt $PackCount; $index += 1) {
        $packId = if ($index -eq 0) {
            'scale-core'
        }
        else {
            'scale-pack-{0:d3}' -f $index
        }
        $capability = 'scale-capability-{0:d3}' -f $index
        $value = 'scale-value-{0:d3}' -f $index
        $filename = "$packId.json"
        $selections += [ordered]@{pack_id=$packId
            path = "packs/$filename"
        }
        $enabled += $capability
        [object[]]$dependencies = @()
        if ($index -ne 0) {
            $dependencies = @([ordered]@{pack_id='scale-core'
                    minimum_version = 1
                })
        }
        $pack = [ordered]@{
            schema_version = 3
            pack_id = $packId
            pack_version = 1
            lifecycle = 'active'
            pack_kind = if ($index -eq 0) {
                'core'
            }
            else {
                'extension'
            }
            label = 'Scale Pack {0:d3}' -f $index
            description = 'Generated schema-pack scale fixture.'
            dependencies = $dependencies
            capabilities = @($capability)
            controlled_values = [ordered]@{'scale.value'=@($value)
            }
        }
        Write-FixtureJson (Join-Path $packsRoot $filename) $pack
    }
    $registryPath = Join-Path $FixtureRoot 'registry.json'
    $registry = [ordered]@{
        schema_version = 2
        selected_packs = @($selections)
        capability_activation = [ordered]@{default='disabled'
            enabled = @($enabled)
        }
    }
    Write-FixtureJson $registryPath $registry
    return $registryPath
}

function Assert-TypedDelimiterCollision {
    param([object]$Project, [string]$BaseRoot, [string]$TempRoot)

    $collisionRoot = Join-Path $TempRoot 'delimiter-collision'
    Copy-Item -LiteralPath $BaseRoot -Destination $collisionRoot -Recurse
    $corePath = Join-Path $collisionRoot 'packs\fixture-core.json'
    $core = ConvertTo-MutableFixtureValue (Get-Content -LiteralPath $corePath -Raw | ConvertFrom-Json)
    $effectKinds = @('a', 'a-with-b', 'b-with-c', 'c')
    foreach ($effectKind in $effectKinds) {
        [void]$core['controlled_values']['occurrence.rule-effect-kind'].Add($effectKind)
        [void]$core['semantic_declarations']['occurrence']['effect_target_compatibilities'].Add(
            [ordered]@{effect_kind=$effectKind
                target_type='subject'
            }
        )
        [void]$core['semantic_declarations']['occurrence']['rule_effect_compatibilities'].Add(
            [ordered]@{rule_kind='add'
                effect_kind=$effectKind
            }
        )
        [void]$core['semantic_declarations']['occurrence']['effect_policies'].Add(
            [ordered]@{effect_kind=$effectKind
                repetition_policy='idempotent'
            }
        )
    }
    [void]$core['semantic_declarations']['occurrence']['effect_incompatibilities'].Add(
        [ordered]@{members=@('a', 'b-with-c')
            scope='global'
        }
    )
    [void]$core['semantic_declarations']['occurrence']['effect_incompatibilities'].Add(
        [ordered]@{members=@('a-with-b', 'c')
            scope='same-target'
        }
    )
    Write-FixtureJson $corePath $core
    $collisionProject = $Project.PSObject.Copy()
    $collisionProject.root = $collisionRoot
    $collisionProject.schema_packs_registry = Join-Path $collisionRoot 'registry.json'
    $registry = Get-KnowledgeSchemaPackRegistry $collisionProject
    if (
        $registry.effect_incompatibilities['a|b-with-c'] -cne 'global' -or
        $registry.effect_incompatibilities['a-with-b|c'] -cne 'same-target'
    ) {
        throw 'Typed delimiter-collision declarations did not remain distinct.'
    }
    return 2
}

$project = Get-KnowledgeProjectConfig $Root
$canonical = Get-KnowledgeSchemaPackRegistry $project
$fixtureRoot = Join-Path $Root 'Framework\Data\Schema-Packs'
$baseRoot = Join-Path $fixtureRoot 'base'
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
if (-not (Test-KnowledgeJsonInteger $expectations.schema_version) -or [int]$expectations.schema_version -ne 1) {
    throw 'Unsupported schema-pack conformance expectation schema.'
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-schema-pack-{0}" -f [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
try {
    $validRoot = Join-Path $tempRoot 'valid'
    Copy-Item -LiteralPath $baseRoot -Destination $validRoot -Recurse
    $validProject = $project.PSObject.Copy()
    $validProject.root = $validRoot
    $validProject.schema_packs_registry = Join-Path $validRoot 'registry.json'
    $fixtureRegistry = Get-KnowledgeSchemaPackRegistry $validProject
    Assert-ValidSchemaPackFixture $fixtureRegistry $expectations.valid
    $typedCollisionPairs = Assert-TypedDelimiterCollision $project $baseRoot $tempRoot

    foreach ($case in @($expectations.invalid_cases)) {
        $caseRoot = Join-Path $tempRoot ([string]$case.id)
        Copy-Item -LiteralPath $baseRoot -Destination $caseRoot -Recurse
        $targetPath = Join-Path $caseRoot $targetPaths[[string]$case.target]
        $document = ConvertTo-MutableFixtureValue (Get-Content -LiteralPath $targetPath -Raw | ConvertFrom-Json)
        foreach ($operation in @($case.operations)) {
            Invoke-FixtureMutation $document $operation
        }
        Write-FixtureJson $targetPath $document
        $caseProject = $project.PSObject.Copy()
        $caseProject.root = $caseRoot
        $caseProject.schema_packs_registry = Join-Path $caseRoot 'registry.json'
        Assert-Rejected {
            $null = Get-KnowledgeSchemaPackRegistry $caseProject
        } "Malformed schema-pack composition was accepted: $($case.id)"
    }

    $scaleRoot = Join-Path $tempRoot 'scale'
    $scaleCount = [int]$expectations.scale_pack_count
    $scaleProject = $project.PSObject.Copy()
    $scaleProject.root = $scaleRoot
    $scaleProject.schema_packs_registry = New-ScaleSchemaPackFixture $scaleRoot $scaleCount
    $scaleRegistry = Get-KnowledgeSchemaPackRegistry $scaleProject
    if (
        @($scaleRegistry.selection_order).Count -ne $scaleCount -or
        @($scaleRegistry.declared_capabilities).Count -ne $scaleCount -or
        @($scaleRegistry.enabled_capabilities).Count -ne $scaleCount -or
        @(Get-SchemaPackAllowedValues $scaleRegistry 'scale.value').Count -ne $scaleCount
    ) {
        throw 'Schema-pack scale composition counts changed.'
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$fixtureControlledValueCount = 0
foreach ($namespace in $fixtureRegistry.controlled_values.Keys) {
    $fixtureControlledValueCount += @($fixtureRegistry.controlled_values[$namespace]).Count
}
$summary = [ordered]@{
    canonical_selected_packs = [int]@($canonical.selection_order).Count
    fixture_available_capabilities = [int]@($fixtureRegistry.available_capabilities).Count
    fixture_controlled_values = [int]$fixtureControlledValueCount
    fixture_declared_capabilities = [int]@($fixtureRegistry.declared_capabilities).Count
    fixture_enabled_capabilities = [int]@($fixtureRegistry.enabled_capabilities).Count
    fixture_selected_packs = [int]@($fixtureRegistry.selection_order).Count
    invalid_composition_cases = [int]@($expectations.invalid_cases).Count
    scale_pack_count = [int]$scaleCount
    typed_collision_pairs = [int]$typedCollisionPairs
    schema_version = 1
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Schema-pack conformance passed: {0} canonical packs, {1} synthetic packs, ' +
        '{2} malformed compositions, and {3} scale packs.' -f
        $summary.canonical_selected_packs,
        $summary.fixture_selected_packs,
        $summary.invalid_composition_cases,
        $summary.scale_pack_count
    )
}
