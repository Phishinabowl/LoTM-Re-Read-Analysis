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
    ConvertFrom-KnowledgeYamlFile $validPath 2 'capability roadmap fixture'
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
    param($data) $data['capabilities']['scheduled-capability']['implementation_evidence'][0]['criterion'] = 'wish'
} 'must be one of'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['implementation_evidence'][0]['provider_pack_id'] = 'fixture-core'
} 'is not a provider'
Invoke-InvalidRoadmapCase {
    param($data) $data['capabilities']['scheduled-capability']['implementation_evidence'][0]['provider_pack_id'] = $null
} 'is required'

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

function New-TransitionEvidence {
    param([string[]]$Criteria, [string]$ProviderPackId = 'fixture-domain')

    return @(
        $Criteria | Sort-Object -CaseSensitive | ForEach-Object {
            $provider = if (
                $_.StartsWith('conformance-', [System.StringComparison]::Ordinal) -or
                $_ -cin @('contract', 'runtime-parity', 'runtime-support')
            ) {
                $ProviderPackId
            }
            else {
                $null
            }
            [ordered]@{
                criterion = $_
                reference = "evidence:$_"
                provider_pack_id = $provider
            }
        }
    )
}

$allEvidenceCriteria = @(
    'compatibility-impact'
    'conformance-ambiguity'
    'conformance-boundary'
    'conformance-malformed'
    'conformance-positive'
    'conformance-scale'
    'consumer-regression'
    'contract'
    'documentation'
    'emergency-decision'
    'evolution'
    'extraction-review'
    'migration-guidance'
    'runtime-parity'
    'runtime-support'
)
$promotionCriteria = @($allEvidenceCriteria | Where-Object { $_ -cnotin @('emergency-decision', 'migration-guidance') })
$promotionDecision = [ordered]@{
    transition = 'promotion'
    rationale = 'Executable contract and all permanent verification are complete.'
    replacement_capability_id = $null
    roadmap_before_present = $true
    roadmap_after_present = $false
    runtime_behavior_changed = $true
    runtime_parity_required = $true
    evidence = @(New-TransitionEvidence $promotionCriteria)
}
$promotion = Get-KnowledgeCapabilityLifecycleTransition `
    'scheduled-capability' `
    'fixture-domain' `
    'planned' `
    'available' `
    $promotionDecision `
@('scheduled-capability', 'replacement-capability')
if (-not $promotion.ready -or @($promotion.missing_criteria).Count -ne 0) {
    throw 'Complete promotion evidence did not pass the lifecycle gate.'
}

$incompleteDecision = [ordered]@{
    transition = 'promotion'
    rationale = 'One criterion is deliberately absent.'
    replacement_capability_id = $null
    roadmap_before_present = $true
    roadmap_after_present = $false
    runtime_behavior_changed = $true
    runtime_parity_required = $true
    evidence = @($promotionDecision.evidence | Where-Object criterion -CNE 'conformance-scale')
}
$incomplete = Get-KnowledgeCapabilityLifecycleTransition `
    'scheduled-capability' `
    'fixture-domain' `
    'planned' `
    'available' `
    $incompleteDecision
if ($incomplete.ready -or (@($incomplete.missing_criteria) -join ',') -cne 'conformance-scale') {
    throw 'Incomplete promotion evidence did not report its exact missing criterion.'
}

$incompleteDeprecationDecision = [ordered]@{
    transition = 'deprecation'
    rationale = 'Migration guidance is deliberately absent.'
    replacement_capability_id = $null
    roadmap_before_present = $false
    roadmap_after_present = $false
    runtime_behavior_changed = $false
    runtime_parity_required = $false
    evidence = @(
        New-TransitionEvidence @($allEvidenceCriteria | Where-Object { $_ -cne 'migration-guidance' })
    )
}
$incompleteDeprecation = Get-KnowledgeCapabilityLifecycleTransition `
    'scheduled-capability' `
    'fixture-domain' `
    'available' `
    'deprecated' `
    $incompleteDeprecationDecision
if (
    $incompleteDeprecation.ready -or
    (@($incompleteDeprecation.missing_criteria) -join ',') -cne 'migration-guidance'
) {
    throw 'Incomplete deprecation evidence did not report its exact missing criterion.'
}

$transitionVectors = @(
    [pscustomobject]@{ transition = 'withdrawal'
        before = 'planned'
        after = $null
        runtime_changed = $false
    }
    [pscustomobject]@{ transition = 'deprecation'
        before = 'available'
        after = 'deprecated'
        runtime_changed = $false
    }
    [pscustomobject]@{ transition = 'rescission'
        before = 'deprecated'
        after = 'available'
        runtime_changed = $true
    }
    [pscustomobject]@{ transition = 'removal'
        before = 'deprecated'
        after = $null
        runtime_changed = $false
    }
    [pscustomobject]@{ transition = 'emergency-removal'
        before = 'available'
        after = $null
        runtime_changed = $true
    }
    [pscustomobject]@{ transition = 'material-reshape'
        before = 'available'
        after = 'available'
        runtime_changed = $false
    }
)
$transitionReadyCases = 1
foreach ($vector in $transitionVectors) {
    $transition = [string]$vector.transition
    $runtimeChanged = [bool]$vector.runtime_changed
    $decision = [ordered]@{
        transition = $transition
        rationale = "Exercise $transition governance."
        replacement_capability_id = if ($transition -cin @('deprecation', 'removal')) {
            'replacement-capability'
        }
        else {
            $null
        }
        roadmap_before_present = [string]$vector.before -ceq 'planned'
        roadmap_after_present = [string]$vector.after -ceq 'planned'
        runtime_behavior_changed = $runtimeChanged
        runtime_parity_required = $runtimeChanged
        evidence = @(New-TransitionEvidence $allEvidenceCriteria)
    }
    $result = Get-KnowledgeCapabilityLifecycleTransition `
        'scheduled-capability' `
        'fixture-domain' `
    ([string]$vector.before) `
        $vector.after `
        $decision `
    @('scheduled-capability', 'replacement-capability')
    if (-not $result.ready) {
        throw "Complete $transition evidence did not pass the lifecycle gate."
    }
    $transitionReadyCases++
}

$transitionInvalidCases = 0
$invalidTransitionDecision = [ordered]@{} + $promotionDecision
Assert-Rejected {
    Get-KnowledgeCapabilityLifecycleTransition `
        'scheduled-capability' 'fixture-domain' 'available' 'planned' $invalidTransitionDecision
} 'is invalid'
$transitionInvalidCases++

$runtimeMissingDecision = [ordered]@{} + $promotionDecision
$runtimeMissingDecision['runtime_behavior_changed'] = $false
Assert-Rejected {
    Get-KnowledgeCapabilityLifecycleTransition `
        'scheduled-capability' 'fixture-domain' 'planned' 'available' $runtimeMissingDecision
} 'must declare changed runtime behavior'
$transitionInvalidCases++

$replacementDecision = [ordered]@{} + $promotionDecision
$replacementDecision['transition'] = 'withdrawal'
$replacementDecision['replacement_capability_id'] = 'missing-capability'
Assert-Rejected {
    Get-KnowledgeCapabilityLifecycleTransition `
        'scheduled-capability' 'fixture-domain' 'planned' $null $replacementDecision @('scheduled-capability')
} 'unknown replacement'
$transitionInvalidCases++

$roadmapDriftDecision = [ordered]@{} + $promotionDecision
$roadmapDriftDecision['roadmap_after_present'] = $true
Assert-Rejected {
    Get-KnowledgeCapabilityLifecycleTransition `
        'scheduled-capability' 'fixture-domain' 'planned' 'available' $roadmapDriftDecision
} 'roadmap/lifecycle drift'
$transitionInvalidCases++

$providerDecision = [ordered]@{} + $promotionDecision
$providerDecision['evidence'] = @(
    [ordered]@{
        criterion = 'contract'
        reference = 'evidence:contract'
        provider_pack_id = 'other-pack'
    }
)
Assert-Rejected {
    Get-KnowledgeCapabilityLifecycleTransition `
        'scheduled-capability' 'fixture-domain' 'planned' 'available' $providerDecision
} 'must name provider'
$transitionInvalidCases++
$invalidCases += $transitionInvalidCases

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
    transition_invalid_cases = $transitionInvalidCases
    transition_not_ready_cases = 2
    transition_ready_cases = $transitionReadyCases
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
