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
    param([scriptblock]$Action, [string]$Message)

    try {
        & $Action
    }
    catch {
        return
    }
    throw $Message
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

function Invoke-FixtureMutation {
    param([object]$Document, [object]$Operation)

    $path = @($Operation.path)
    $current = $Document
    for ($index = 0; $index -lt $path.Count - 1; $index += 1) {
        $current = $current[$path[$index]]
    }
    $final = $path[-1]
    $value = if ($Operation.PSObject.Properties.Name -ccontains 'value') {
        ConvertTo-MutableFixtureValue $Operation.value
    }
    else {
        $null
    }
    switch ([string]$Operation.op) {
        'set' {
            $current[$final] = $value
        }
        'append' {
            [void]$current[$final].Add($value)
        }
        'remove' {
            if ($current -is [System.Collections.ArrayList]) {
                $current.RemoveAt([int]$final)
            }
            else {
                [void]$current.Remove([string]$final)
            }
        }
        default {
            throw "Unknown fixture operation '$($Operation.op)'."
        }
    }
}

function Write-FixtureJson {
    param([string]$Path, [object]$Value)

    [System.IO.File]::WriteAllText(
        $Path,
        (($Value | ConvertTo-Json -Depth 100) + [Environment]::NewLine),
        $utf8NoBom
    )
}

function Get-FixtureProvider {
    $identities = [ordered]@{
        entity = [ordered]@{
            alpha = [pscustomobject]@{ id = 'alpha' }
            beta = [pscustomobject]@{ id = 'beta' }
        }
        'entity-incarnation' = [ordered]@{
            'gamma-incarnation' = [pscustomobject]@{ id = 'gamma-incarnation' }
        }
        'identity-phase' = [ordered]@{
            'beta-phase' = [pscustomobject]@{ id = 'beta-phase' }
        }
    }
    $relationships = [ordered]@{
        'entity-relationship' = [ordered]@{
            'beta-derived-from-alpha' = [pscustomobject]@{ id = 'beta-derived-from-alpha' }
        }
        'incarnation-relationship' = [ordered]@{}
        'identity-phase-relationship' = [ordered]@{}
    }
    return New-KnowledgeHostingIdentityProvider 'fixture' $identities $relationships
}

function Get-FixtureRegistry {
    param(
        [object]$Project,
        [object]$Packs,
        [object]$Occurrences,
        [object[]]$Providers,
        [string]$Path
    )

    $fixtureProject = $Project.PSObject.Copy()
    $fixtureProject.hosting_registry = $Path
    return Get-KnowledgeHostedIdentityRegistry $fixtureProject $Packs $Occurrences $Providers
}

function Assert-Ids {
    param([object[]]$Actual, [string[]]$Expected, [string]$Context)

    if ((@($Actual.id) -join ',') -cne (@($Expected) -join ',')) {
        throw "$Context changed."
    }
}

function Assert-Services {
    param([object]$Registry)

    Assert-Ids `
    (Get-KnowledgeHostCarrierOccupancies $Registry 'body-a') `
    @('alpha-controller', 'beta-controller', 'gamma-body-a') `
        'Carrier occupancy query'
    Assert-Ids `
    (Get-KnowledgeHostedIdentityOccupancies $Registry 'entity' 'alpha') `
    @('alpha-controller', 'alpha-runtime-source') `
        'Subject occupancy query'
    Assert-Ids `
    (Get-KnowledgeHostCarrierControllersAt $Registry 'body-a' 'protagonist-entry-04') `
    @('alpha-controller') `
        'Controller lookup before handoff'
    Assert-Ids `
    (Get-KnowledgeHostCarrierControllersAt $Registry 'body-a' 'protagonist-entry-05') `
    @('beta-controller') `
        'Controller lookup at handoff'
    Assert-Ids `
    (Get-KnowledgeHostCarrierOccupanciesAt $Registry 'body-b' 'protagonist-entry-10') `
    @('beta-copy-body-b', 'gamma-body-b') `
        'Co-resident occupancy lookup'
    if (-not (Test-KnowledgeHostCarrierActiveAt $Registry 'body-a' 'protagonist-entry-13')) {
        throw 'Carrier unexpectedly inactive before termination.'
    }
    if (Test-KnowledgeHostCarrierActiveAt $Registry 'body-a' 'protagonist-entry-14') {
        throw 'Carrier unexpectedly active at exclusive termination boundary.'
    }
    $target = Get-KnowledgeHostingProvenanceTarget `
        $Registry `
        'hosted-identity-transition' `
        'alpha-copy-to-beta'
    if ($target.transition_kind -cne 'copy') {
        throw 'Hosted identity provenance lookup changed.'
    }
    $reconciliation = Get-KnowledgeHostingReconciliationProvider $Registry
    if (@($reconciliation.targets.Keys) -join ',' -cne 'host-carrier') {
        throw 'Hosted identity reconciliation target boundary changed.'
    }
    return 9
}

function Assert-InvalidQueries {
    param([object]$Registry)

    $actions = @(
        { Get-KnowledgeHostCarrierOccupancies $Registry 'missing' }
        { Get-KnowledgeHostedIdentityOccupancies $Registry 'entity' 'missing' }
        { Test-KnowledgeHostCarrierActiveAt $Registry 'body-a' 'missing' }
        { Test-KnowledgeHostCarrierActiveAt $Registry 'body-a' 'observer-entry-01' }
        { Get-KnowledgeHostCarrierOccupanciesAt $Registry 'missing' 'protagonist-entry-01' }
        { Get-KnowledgeHostingProvenanceTarget $Registry 'missing' 'body-a' }
        { Get-KnowledgeHostingProvenanceTarget $Registry 'host-carrier' 'missing' }
    )
    foreach ($action in $actions) {
        Assert-Rejected $action 'Hosted identity invalid query unexpectedly succeeded.'
    }
    return $actions.Count
}

function Get-ScaleResult {
    param(
        [object]$Project,
        [object]$Packs,
        [object]$Occurrences,
        [object]$Provider,
        [object]$Base,
        [string]$Path
    )

    $scale = ConvertTo-MutableFixtureValue $Base
    $scale['carriers'] = [ordered]@{}
    $scale['occupancies'] = New-Object System.Collections.ArrayList
    $scale['transitions'] = New-Object System.Collections.ArrayList
    for ($index = 0; $index -lt 128; $index += 1) {
        $carrierId = 'scale-carrier-{0:D3}' -f $index
        $scale['carriers'][$carrierId] = [ordered]@{
            lifecycle = 'active'
            carrier_kind = 'runtime'
            label = 'Scale Carrier {0:D3}' -f $index
            lifecycle_track_id = 'protagonist-experience'
            activated_at_entry_id = 'protagonist-entry-01'
            terminated_at_entry_id = $null
        }
        [void]$scale['occupancies'].Add([ordered]@{
                id = 'scale-occupancy-{0:D3}' -f $index
                subject_type = 'entity'
                subject_id = 'alpha'
                carrier_id = $carrierId
                role = 'active'
                activated_at_entry_id = 'protagonist-entry-01'
                terminated_at_entry_id = $null
            })
    }
    Write-FixtureJson $Path $scale
    $registry = Get-FixtureRegistry $Project $Packs $Occurrences @($Provider) $Path
    return [pscustomobject]@{
        carriers = $registry.carriers.Count
        occupancies = $registry.occupancies.Count
    }
}

$fixtureRoot = Join-Path $Root 'Framework\Data\Hosting'
$base = Get-Content -LiteralPath (Join-Path $fixtureRoot 'base\registry.json') -Raw | ConvertFrom-Json
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
$project = Get-KnowledgeProjectConfig $Root
$packs = Get-KnowledgeSchemaPackRegistry $project
$chronologyPath = Join-Path $Root 'Framework\Data\Chronology\valid-registry.yaml'
$chronologyData = ConvertFrom-KnowledgeYamlFile $chronologyPath 2 'chronology fixture'
$chronologyData['contexts'] = @(
    [ordered]@{
        id = 'recipient-context'
        label = 'Recipient Context'
        coordinate_system_id = 'mission-day'
        role = 'story'
        continuity_ids = @()
        work_ids = @('fixture-work')
        branch_id = 'main'
    },
    [ordered]@{
        id = 'agent-context'
        label = 'Agent Context'
        coordinate_system_id = 'control-step'
        role = 'time-travel-origin'
        continuity_ids = @()
        work_ids = @('fixture-work')
        branch_id = 'main'
    }
)
$chronologyData['context_relations'] = @()
$chronology = ConvertTo-KnowledgeChronologyRegistry `
    $chronologyData `
    $chronologyPath `
    $packs `
@('fixture-work') `
@()
$occurrencePath = Join-Path $Root 'Framework\Data\Occurrence\valid-registry.yaml'
$occurrenceData = ConvertFrom-KnowledgeYamlFile $occurrencePath 10 'occurrence fixture'
$occurrences = ConvertTo-KnowledgeOccurrenceRegistry `
    $occurrenceData `
    $occurrencePath `
    $packs `
    $chronology `
([ordered]@{ character = @('protagonist', 'observer') }) `
([ordered]@{
        'state-record' = @('protagonist-health')
        'credential-record' = @('protagonist-qualification')
    })
$provider = Get-FixtureProvider
$temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('hosting-conformance-' + [guid]::NewGuid())
[void](New-Item -ItemType Directory -Path $temporaryRoot)
$path = Join-Path $temporaryRoot 'registry.json'
try {
    Write-FixtureJson $path $base
    $registry = Get-FixtureRegistry $project $packs $occurrences @($provider) $path
    $counts = [ordered]@{
        carriers = $registry.carriers.Count
        occupancies = $registry.occupancies.Count
        transitions = $registry.transitions.Count
        provenance_target_types = (Get-KnowledgeHostingProvenanceTargets $registry).Count
        reconciliation_target_types = (Get-KnowledgeHostingReconciliationProvider $registry).targets.Count
    }
    foreach ($property in $expectations.counts.PSObject.Properties) {
        if ([int]$counts[$property.Name] -ne [int]$property.Value) {
            throw "Hosted identity fixture count '$($property.Name)' changed."
        }
    }
    $serviceAssertions = Assert-Services $registry
    $invalidQueries = Assert-InvalidQueries $registry
    if ($invalidQueries -ne [int]$expectations.invalid_queries) {
        throw 'Hosted identity invalid-query count changed.'
    }

    $invalidConfigurations = 0
    foreach ($case in @($expectations.invalid_cases)) {
        $candidate = ConvertTo-MutableFixtureValue $base
        foreach ($operation in @($case.operations)) {
            Invoke-FixtureMutation $candidate $operation
        }
        Write-FixtureJson $path $candidate
        Assert-Rejected `
        { Get-FixtureRegistry $project $packs $occurrences @($provider) $path } `
            "Hosted identity invalid case '$($case.id)' unexpectedly succeeded."
        $invalidConfigurations += 1
    }

    $disabledPacks = $packs.PSObject.Copy()
    $disabledPacks.enabled_capabilities = @(
        $packs.enabled_capabilities | Where-Object { $_ -cne 'hosted-identity-embodiment' }
    )
    Write-FixtureJson $path $base
    Assert-Rejected `
    { Get-FixtureRegistry $project $disabledPacks $occurrences @($provider) $path } `
        'Disabled hosted identity capability unexpectedly loaded.'
    $invalidConfigurations += 1
    Assert-Rejected `
    { Get-FixtureRegistry $project $packs $occurrences @($provider, $provider) $path } `
        'Duplicate hosted identity provider unexpectedly loaded.'
    $invalidConfigurations += 1
    $scale = Get-ScaleResult $project $packs $occurrences $provider $base $path
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    schema_version = [int]$registry.schema_version
    counts = $counts
    service_assertions = $serviceAssertions
    invalid_configurations = $invalidConfigurations
    invalid_queries = $invalidQueries
    scale_carriers = [int]$scale.carriers
    scale_occupancies = [int]$scale.occupancies
}
if ($Json) {
    $summary | ConvertTo-Json -Compress -Depth 10
}
else {
    Write-Output 'Hosted identity conformance passed.'
    $summary | ConvertTo-Json -Depth 10
}
