[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$toolsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeModule = Join-Path $toolsRoot 'Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
Import-Module $runtimeModule -Force

function Assert-Rejected {
    param([scriptblock]$Action, [string]$ExpectedText)

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

$actualRoot = Resolve-KnowledgeFrameworkRoot -ExplicitRoot $Root -ExecutablePath $PSCommandPath
$fixtureRoot = Join-Path $actualRoot 'Framework\Data\Capability-Roadmap'
$validPath = Join-Path $fixtureRoot 'valid-roadmap.json'
$catalog = ConvertFrom-Json -InputObject ([System.IO.File]::ReadAllText((Join-Path $fixtureRoot 'catalog.json')))
$config = Get-KnowledgeFrameworkConfig $actualRoot
$invalidCases = 0

function Get-ValidRoadmapData {
    ConvertFrom-KnowledgeYamlFile $validPath 1 'capability roadmap fixture'
}

function Invoke-InvalidRoadmapCase {
    param([scriptblock]$Mutation, [string]$ExpectedText)

    $data = Get-ValidRoadmapData
    & $Mutation $data
    Assert-Rejected {
        ConvertTo-KnowledgeCapabilityRoadmap $data $config $catalog
    } $ExpectedText
    $script:invalidCases++
}

$model = ConvertTo-KnowledgeCapabilityRoadmap (Get-ValidRoadmapData) $config $catalog
$repeated = ConvertTo-KnowledgeCapabilityRoadmap (Get-ValidRoadmapData) $config $catalog
if (($model | ConvertTo-Json -Depth 30 -Compress) -cne ($repeated | ConvertTo-Json -Depth 30 -Compress)) {
    throw 'Capability-roadmap normalization is not deterministic.'
}
if ((@($model.capabilities | ForEach-Object capability_id) -join ',') -cne 'deferred-capability,scheduled-capability') {
    throw 'Capability-roadmap mappings are not sorted by stable capability ID.'
}
if ($model.capabilities[0].disposition -cne 'accepted-deferral') {
    throw 'Accepted-deferral fixture did not retain its disposition.'
}
if ($model.capabilities[1].delivery_target_id -cne 'platform-phase-alpha') {
    throw 'Scheduled fixture did not retain its delivery target.'
}

Invoke-InvalidRoadmapCase { param($data) $data['unexpected'] = $true } 'unsupported field'
Invoke-InvalidRoadmapCase { param($data) $data['registry_id'] = 'other-roadmap' } "must be 'capability-roadmap'"
Invoke-InvalidRoadmapCase {
    param($data) $data['delivery_targets']['platform-phase-alpha']['kind'] = 'milestone'
} 'must be one of'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['unknown-capability'] = $data['capabilities']['scheduled-capability']
} 'unknown capability ID'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities'].Remove('deferred-capability')
} 'missing planned capability'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['available-capability'] = $data['capabilities']['scheduled-capability']
} 'non-planned capability'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['delivery_target_id'] = 'platform-phase-missing'
} 'unknown delivery target'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['disposition'] = 'maybe'
} 'must be one of'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['deferred-capability'].Remove('review_trigger')
} 'review_trigger'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['platform_prerequisite_ids'] = @(
        'platform-phase-missing'
    )
} 'unknown delivery target'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['platform_prerequisite_ids'] = @(
        'platform-phase-alpha'
    )
} 'own delivery target'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['domain_capability_dependency_ids'] = @(
        'unknown-capability'
    )
} 'unknown capability'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['domain_capability_dependency_ids'] = @(
        'scheduled-capability'
    )
} 'cannot depend on itself'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['deferred-capability']['domain_capability_dependency_ids'] = @(
        'scheduled-capability'
    )
} 'contain a cycle'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['domain_capability_dependency_ids'] = @(
        'deferred-capability'
        'deferred-capability'
    )
} 'duplicate values'
Invoke-InvalidRoadmapCase {
    param($data) $data['delivery_targets']['platform-phase-alpha']['plan_path'] = '../platform-implementation-plan.md'
} 'confined framework-relative path'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['implementation_evidence'][0]['kind'] = 'wish'
} 'must be one of'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['implementation_evidence'][0]['provider_pack_id'] = 'fixture-core'
} 'is not a provider'

$tempPath = Join-Path ([System.IO.Path]::GetTempPath()) ('capability-roadmap-duplicate-' + [guid]::NewGuid().ToString('N') + '.yaml')
try {
    [System.IO.File]::WriteAllText(
        $tempPath,
        "schema_version: 1`nregistry_id: capability-roadmap`nregistry_id: duplicate`n",
        [System.Text.UTF8Encoding]::new($false)
    )
    Assert-Rejected {
        $data = ConvertFrom-KnowledgeYamlFile $tempPath 1 'capability roadmap'
        ConvertTo-KnowledgeCapabilityRoadmap $data $config $catalog
    } 'duplicate mapping key'
    $invalidCases++
}
finally {
    if (Test-Path -LiteralPath $tempPath) {
        Remove-Item -LiteralPath $tempPath -Force
    }
}

$scaleData = Get-ValidRoadmapData
$scaleData['capabilities'] = [ordered]@{}
$scaleCapabilities = @()
for ($index = 0; $index -lt 128; $index++) {
    $capabilityId = 'scale-capability-{0:d3}' -f $index
    $scaleCapabilities += [pscustomobject]@{
        id = $capabilityId
        planned = $true
        providers = @([pscustomobject]@{ pack_id = 'fixture-domain' })
    }
    $scaleData['capabilities'][$capabilityId] = [ordered]@{
        disposition = 'scheduled'
        delivery_target_id = 'platform-phase-alpha'
        rationale = 'Generated scale mapping.'
        platform_prerequisite_ids = @()
        domain_capability_dependency_ids = @()
        implementation_evidence = @()
    }
}
$scaleCatalog = [pscustomobject]@{
    contract = 'framework-catalog'
    capabilities = $scaleCapabilities
}
$scale = ConvertTo-KnowledgeCapabilityRoadmap $scaleData $config $scaleCatalog
if (@($scale.capabilities).Count -ne 128) {
    throw 'Capability-roadmap scale fixture did not retain all 128 mappings.'
}

$canonical = Get-KnowledgeCapabilityRoadmap $actualRoot
if (@($canonical.delivery_targets).Count -ne 8 -or @($canonical.capabilities).Count -ne 13) {
    throw 'Canonical capability-roadmap counts differ from the Phase 3.4.2 baseline.'
}

$summary = [ordered]@{
    canonical_capabilities = @($canonical.capabilities).Count
    canonical_delivery_targets = @($canonical.delivery_targets).Count
    invalid_cases = $invalidCases
    neutral_capabilities = @($model.capabilities).Count
    scale_capabilities = @($scale.capabilities).Count
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Output (
        'Capability-roadmap conformance passed: ' +
        "$(@($canonical.capabilities).Count) canonical mappings, $invalidCases invalid cases, " +
        "$(@($scale.capabilities).Count) scale mappings."
    )
}
