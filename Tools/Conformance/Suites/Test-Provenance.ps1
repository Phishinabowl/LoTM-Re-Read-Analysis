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
    param([object]$Document, [object[]]$Path)

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
    param([object]$Document, [object]$Operation)

    $location = Get-FixtureMutationParent $Document @($Operation.path)
    $value = if ($Operation.PSObject.Properties.Name -ccontains 'value') {
        ConvertTo-MutableFixtureValue $Operation.value
    }
    else {
        $null
    }
    switch ([string]$Operation.op) {
        'set' {
            $location.parent[$location.final] = $value
        }
        'append' {
            $target = $location.parent[$location.final]
            if ($target -isnot [System.Collections.ArrayList]) {
                throw 'Fixture append target must be a mutable list.'
            }
            [void]$target.Add($value)
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
    param([string]$Path, [object]$Value)

    $content = ($Value | ConvertTo-Json -Depth 100) + [Environment]::NewLine
    [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
}

function New-TaxonomyFixtureProject {
    param([object]$Project, [string]$FixtureRoot)

    $fixture = $Project.PSObject.Copy()
    $fixture.root = $FixtureRoot
    $fixture.taxonomy_registry = Join-Path $FixtureRoot 'registry.json'
    $fixture.content_roots = @(
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
    return $fixture
}

function New-SourceFixtureProject {
    param([object]$Project, [string]$FixtureRoot)

    $fixture = $Project.PSObject.Copy()
    $fixture.root = $FixtureRoot
    $fixture.resources_registry = Join-Path $FixtureRoot 'resources.json'
    $fixture.sources_registry = Join-Path $FixtureRoot 'registry.json'
    $fixture.resource_roots = @(
        [pscustomobject]@{
            id = 'source-files'
            relative_path = 'source-files'
            path = Join-Path $FixtureRoot 'source-files'
            required = $true
        }
    )
    return $fixture
}

function Add-ProvenanceSourceExtensions {
    param([object]$Document)

    foreach ($definition in @(
            [pscustomobject]@{
                id = 'corroborating-source'
                label = 'Corroborating Source'
                comparison_group = 'sample-narrative'
            }
            [pscustomobject]@{
                id = 'incomparable-source'
                label = 'Incomparable Source'
                comparison_group = 'external-comparison'
            }
        )) {
        $source = ConvertTo-MutableFixtureValue $Document.sources['primary-source']
        $source.label = $definition.label
        $source.aliases = New-Object System.Collections.ArrayList
        $source.observations = New-Object System.Collections.ArrayList
        $source.coverage = New-Object System.Collections.ArrayList
        $source.resource_bindings = New-Object System.Collections.ArrayList
        $source.comparison_group = $definition.comparison_group
        $Document.sources[$definition.id] = $source
    }
    [void]$Document.applicability_scopes.Add([ordered]@{
            id = 'reported-alpha-name-scope'
            target_type = 'provenance-claim'
            target_id = 'reported-alpha-name'
            territory_ids = New-Object System.Collections.ArrayList
            precedence = 20
        })
    [void]$Document.applicability_scopes.Add([ordered]@{
            id = 'confirmed-alpha-name-scope'
            target_type = 'provenance-claim'
            target_id = 'confirmed-alpha-name'
            territory_ids = New-Object System.Collections.ArrayList
            precedence = 10
        })
    [void]$Document.applicability_scopes.Add([ordered]@{
            id = 'inner-loop-cardinality-scope'
            target_type = 'provenance-claim'
            target_id = 'inner-loop-minimum-cardinality'
            territory_ids = New-Object System.Collections.ArrayList
            effective_window = [ordered]@{
                kind = 'interval'
                start = [ordered]@{
                    kind = 'known'
                    value = '2025-01-01'
                    precision = 'date'
                    certainty = 'exact'
                    inclusive = $true
                }
            }
            precedence = 30
        })
}

function Get-FixtureProvenanceRegistry {
    param(
        [object]$Project,
        [object]$Sources,
        [object]$Entities,
        [object]$Reconciliations,
        [object]$Packs,
        [object]$Occurrences,
        [object]$Interpretations,
        [object]$Hosting,
        [string]$Path
    )

    $fixture = $Project.PSObject.Copy()
    $fixture.provenance_registry = $Path
    return Get-KnowledgeProvenanceRegistry `
        $fixture `
        $Sources `
        $Entities `
        $Reconciliations `
        $Packs `
        $Occurrences `
        $Interpretations `
        $Hosting
}

function Assert-ProvenanceFixtureCounts {
    param([object]$Registry, [object]$Expected)

    $links = @($Registry.assertions | ForEach-Object { @($_.evidence_links) })
    $locators = @($links | ForEach-Object { @($_.locators) })
    $claimKeys = @($Registry.assertions.claim_key | Sort-Object -Unique)
    if ($Registry.assertions.Count -ne [int]$Expected.assertions -or
        $Registry.claim_supersessions.Count -ne [int]$Expected.claim_supersessions -or
        $claimKeys.Count -ne [int]$Expected.claim_keys -or
        $links.Count -ne [int]$Expected.evidence_links -or
        $locators.Count -ne [int]$Expected.locators) {
        throw 'Provenance fixture counts changed.'
    }
}

function Assert-ProvenanceAuthorityVectors {
    param([object]$Registry, [object[]]$Vectors)

    foreach ($expected in $Vectors) {
        $actual = Get-KnowledgeClaimAuthorityEvaluation $Registry 'comparison-profile' $expected.claim_key
        $actualRank = if ($null -eq $actual.best_rank) {
            $null
        }
        else {
            [int]$actual.best_rank
        }
        $expectedRank = if ($null -eq $expected.best_rank) {
            $null
        }
        else {
            [int]$expected.best_rank
        }
        if ($actual.outcome -cne $expected.outcome -or
            $actualRank -ne $expectedRank -or
            (@($actual.winning_assertion_ids) -join '|') -cne (@($expected.winning_assertion_ids) -join '|')) {
            throw "Authority vector changed: $($expected.claim_key)"
        }
        foreach ($item in @($actual.decisions)) {
            if (-not $Registry.sources.sources.Contains($item.decision.source_id)) {
                throw 'Authority decision lost its source identity.'
            }
            if ([int]$item.decision.rank -lt 0) {
                throw 'Authority decision produced a negative rank.'
            }
        }
    }
}

function Assert-ProvenanceFixtureServices {
    param([object]$Registry)

    $claimAssertions = @($Registry.assertions | Where-Object claim_key -eq 'authority-winner')
    if (($claimAssertions.id -join '|') -cne 'winner-primary|winner-adaptation') {
        throw 'Claim assertion lookup changed.'
    }
    $entity = Get-KnowledgeProvenanceTarget $Registry 'entity' 'alpha-concept'
    if (-not [object]::ReferenceEquals($entity, $Registry.entities.entities['alpha-concept'])) {
        throw 'Cross-registry provenance target lookup changed.'
    }
    $supersession = Get-KnowledgeProvenanceTarget `
        $Registry `
        'claim-supersession' `
        'confirmed-name-supersedes-reported-name'
    if ($supersession.source_claim_key -cne 'confirmed-alpha-name') {
        throw 'Claim-supersession target lookup changed.'
    }
    $cardinality = Get-KnowledgeProvenanceTarget `
        $Registry `
        'recurrence-cardinality' `
        'inner-minimum-count'
    if ([long]$cardinality.minimum_count -ne 1) {
        throw 'Recurrence-cardinality provenance target lookup changed.'
    }
    $participation = Get-KnowledgeProvenanceTarget `
        $Registry `
        'occurrence-participation' `
        'protagonist-self-intervention-agent'
    if ($participation.role -cne 'agent') {
        throw 'Occurrence-participation provenance target lookup changed.'
    }
    $trackEntry = Get-KnowledgeProvenanceTarget `
        $Registry `
        'occurrence-track-entry' `
        'protagonist-entry-14'
    if ($trackEntry.participation_id -cne $participation.id -or [int]$trackEntry.ordinal -ne 14) {
        throw 'Occurrence-track-entry provenance target lookup changed.'
    }
    $chronologyBinding = Get-KnowledgeProvenanceTarget `
        $Registry `
        'occurrence-participation-chronology-binding' `
        'agent-personal-binding'
    if (
        $chronologyBinding.target_id -cne $participation.id -or
        $chronologyBinding.chronology_context_id -cne 'agent-context'
    ) {
        throw 'Participation chronology-binding provenance target lookup changed.'
    }
    $state = Get-KnowledgeProvenanceTarget `
        $Registry `
        'state-transition' `
        'protagonist-completes-inner-step-knowledge'
    if ($state.state_profile -cne 'epistemic-access' -or $state.resulting_completeness -cne 'complete') {
        throw 'Epistemic state-transition provenance target lookup changed.'
    }
    $exact = Get-KnowledgeProvenanceApplicabilityDecision `
        $Registry `
        'provenance-claim' `
        'reported-alpha-name'
    if ((@($exact.winning_scope_ids) -join '|') -cne 'reported-alpha-name-scope' -or
        [int]$exact.highest_precedence -ne 20) {
        throw 'Provenance-claim applicability resolution changed.'
    }
    $delegated = Get-KnowledgeProvenanceApplicabilityDecision $Registry 'work' 'adaptation-work'
    if ((@($delegated.winning_scope_ids) -join '|') -cne 'adaptation-work-scope') {
        throw 'Delegated source applicability resolution changed.'
    }
    $cardinalityScope = Get-KnowledgeProvenanceApplicabilityDecision `
        $Registry `
        'provenance-claim' `
        'inner-loop-minimum-cardinality' `
        -EffectiveAt '2025-02-01'
    if ((@($cardinalityScope.winning_scope_ids) -join '|') -cne 'inner-loop-cardinality-scope' -or
        [int]$cardinalityScope.highest_precedence -ne 30) {
        throw 'Recurrence-cardinality claim applicability resolution changed.'
    }
}

function Assert-InvalidProvenanceQueries {
    param([object]$Registry)

    $actions = @(
        { Get-KnowledgeProvenanceTarget $Registry 'unknown' 'alpha-concept' }
        { Get-KnowledgeProvenanceTarget $Registry 'entity' 'unknown' }
        { Get-KnowledgeClaimAuthorityEvaluation $Registry 'comparison-profile' 'unknown-claim' }
        { Get-KnowledgeClaimAuthorityEvaluation $Registry 'comparison-profile' 'context-only-claim' }
        { Get-KnowledgeProvenanceApplicabilityDecision $Registry 'provenance-claim' 'unknown-claim' }
    )
    for ($index = 0; $index -lt $actions.Count; $index += 1) {
        Assert-Rejected $actions[$index] "Invalid provenance service query was accepted: $index"
    }
    return $actions.Count
}

function Add-ScaleAssertions {
    param([object]$Document, [int]$Count)

    for ($index = 0; $index -lt $Count; $index += 1) {
        [void]$Document.assertions.Add([ordered]@{
                id = 'scale-assertion-{0:d3}' -f $index
                claim_key = 'scale-claim-{0:d3}' -f $index
                subject_type = 'entity'
                subject_id = 'alpha-concept'
                claim_namespace = 'canonical-content'
                field_path = 'label'
                asserted_value = 'Scale Value {0:d3}' -f $index
                assertion_status = 'verified'
                evidence_links = [System.Collections.ArrayList]@(
                    [ordered]@{
                        source_id = 'primary-source'
                        evidence_role = 'supports'
                        locators = [System.Collections.ArrayList]@(
                            [ordered]@{
                                id = 'scale-locator-{0:d3}' -f $index
                                medium_id = 'novel'
                                evidence_mode = 'canonical-text'
                                locator_type = 'point'
                                position = [ordered]@{work = 'primary-work'
                                    volume = 1
                                    chapter = 1
                                }
                            }
                        )
                    }
                )
            })
    }
}

$project = Get-KnowledgeProjectConfig $Root
$packs = Get-KnowledgeSchemaPackRegistry $project
$canonicalTaxonomy = Get-KnowledgeTaxonomyConfig $project
$canonicalResources = Get-KnowledgeResourceConfig $project
$canonicalSources = Get-KnowledgeSourceRegistry $project $canonicalResources $packs
$canonicalEntities = Get-KnowledgeEntityRegistry $project $canonicalTaxonomy $canonicalSources $packs
$chronology = Get-KnowledgeChronologyRegistry `
    $project `
    $packs `
@($canonicalSources.works.Keys) `
@($canonicalSources.continuities.Keys)
$occurrences = Get-KnowledgeOccurrenceRegistry $project $packs $chronology
$canonicalHosting = Get-KnowledgeHostedIdentityRegistry `
    $project `
    $packs `
    $occurrences `
@((New-KnowledgeHostingEntityProvider $canonicalEntities))
$canonicalProviders = @(
    (Get-KnowledgeTaxonomyReconciliationProvider $canonicalTaxonomy)
    (Get-KnowledgeResourceReconciliationProvider $canonicalResources)
    (Get-KnowledgeSourceReconciliationProvider $canonicalSources)
    (Get-KnowledgeEntityReconciliationProvider $canonicalEntities)
    (Get-KnowledgeHostingReconciliationProvider $canonicalHosting)
)
$reconciliations = Get-KnowledgeReconciliationRegistry $project $canonicalProviders $packs
$canonical = Get-KnowledgeProvenanceRegistry `
    $project `
    $canonicalSources `
    $canonicalEntities `
    $reconciliations `
    $packs `
    $occurrences `
    $null `
    $canonicalHosting
$chronologyContextTarget = Get-KnowledgeProvenanceTarget `
    $canonical `
    'chronology-context' `
    'lotm-novel-main-story-chronology'
if ($chronologyContextTarget.id -cne 'lotm-novel-main-story-chronology') {
    throw 'Chronology-context provenance dispatch returned the wrong target.'
}

$fixtureRoot = Join-Path $Root 'Framework\Data\Provenance'
$baseDocument = ConvertTo-MutableFixtureValue (
    Get-Content -LiteralPath (Join-Path $fixtureRoot 'base\registry.json') -Raw | ConvertFrom-Json
)
$expectations = Get-Content -LiteralPath (Join-Path $fixtureRoot 'expectations.json') -Raw | ConvertFrom-Json
if ([int]$expectations.schema_version -ne 1) {
    throw 'Unsupported provenance conformance expectation schema.'
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('knowledge-provenance-' + [guid]::NewGuid().ToString('N'))
try {
    [void](New-Item -ItemType Directory -Path $tempRoot)
    $sourceRoot = Join-Path $tempRoot 'sources'
    Copy-Item -LiteralPath (Join-Path $Root 'Framework\Data\Sources\base') -Destination $sourceRoot -Recurse
    $sourceDocument = ConvertTo-MutableFixtureValue (
        Get-Content -LiteralPath (Join-Path $sourceRoot 'registry.json') -Raw | ConvertFrom-Json
    )
    Add-ProvenanceSourceExtensions $sourceDocument
    Write-FixtureJson (Join-Path $sourceRoot 'registry.json') $sourceDocument
    $sourceProject = New-SourceFixtureProject $project $sourceRoot
    $resources = Get-KnowledgeResourceConfig $sourceProject
    $sources = Get-KnowledgeSourceRegistry $sourceProject $resources $packs

    $taxonomyRoot = Join-Path $Root 'Framework\Data\Taxonomy\base'
    $taxonomy = Get-KnowledgeTaxonomyConfig (New-TaxonomyFixtureProject $project $taxonomyRoot)
    $entityProject = $project.PSObject.Copy()
    $entityProject.entities_registry = Join-Path $Root 'Framework\Data\Entities\base\registry.json'
    $entities = Get-KnowledgeEntityRegistry $entityProject $taxonomy $sources $packs

    $chronologyFixturePath = Join-Path $Root 'Framework\Data\Chronology\valid-registry.yaml'
    $chronologyFixtureData = ConvertFrom-KnowledgeYamlFile $chronologyFixturePath 2 'chronology fixture'
    $chronologyFixtureData['contexts'] = @(
        [ordered]@{id='recipient-context'
            label='Recipient Context'
            coordinate_system_id='mission-day'
            role='story'
            continuity_ids=@()
            work_ids=@('fixture-work')
            branch_id='main'
        },
        [ordered]@{id='agent-context'
            label='Agent Context'
            coordinate_system_id='control-step'
            role='time-travel-origin'
            continuity_ids=@()
            work_ids=@('fixture-work')
            branch_id='main'
        }
    )
    $chronologyFixtureData['context_relations'] = @()
    $chronologyFixture = ConvertTo-KnowledgeChronologyRegistry `
        $chronologyFixtureData $chronologyFixturePath $packs @('fixture-work') @()
    $occurrenceFixturePath = Join-Path $Root 'Framework\Data\Occurrence\valid-registry.yaml'
    $occurrenceFixtureData = ConvertFrom-KnowledgeYamlFile $occurrenceFixturePath 10 'occurrence fixture'
    $subjectTargets = [ordered]@{character = @('protagonist', 'observer') }
    $payloadTargets = [ordered]@{
        'state-record' = @('protagonist-health')
        'credential-record' = @('protagonist-qualification')
    }
    $fixtureOccurrences = ConvertTo-KnowledgeOccurrenceRegistry `
        $occurrenceFixtureData `
        $occurrenceFixturePath `
        $packs `
        $chronologyFixture `
        $subjectTargets `
        $payloadTargets
    $hostingProject = $project.PSObject.Copy()
    $hostingFixturePath = Join-Path $Root 'Framework\Data\Hosting\base\registry.json'
    $hostingDocument = ConvertTo-MutableFixtureValue (
        ConvertFrom-KnowledgeYamlFile $hostingFixturePath 2 'hosted identity registry'
    )
    $vessel = ConvertTo-MutableFixtureValue $hostingDocument['carriers']['body-a']
    $vessel['carrier_kind'] = 'vessel'
    $vessel['label'] = 'Vessel A'
    $hostingDocument['carriers'] = [ordered]@{
        'vessel-a' = $vessel
        'body-b' = $hostingDocument['carriers']['body-b']
    }
    $hostingDocument['bindings'] = [System.Collections.ArrayList]@(
        [ordered]@{
            id = 'vessel-body-b'
            child_carrier_id = 'vessel-a'
            parent_carrier_id = 'body-b'
            binding_kind = 'installed-in'
            child_activated_at_entry_id = 'protagonist-entry-01'
            parent_activated_at_entry_id = 'protagonist-entry-01'
            child_terminated_at_entry_id = 'protagonist-entry-10'
            parent_terminated_at_entry_id = 'protagonist-entry-10'
        }
    )
    $hostingDocument['occupancies'] = [System.Collections.ArrayList]@()
    $hostingDocument['transitions'] = [System.Collections.ArrayList]@()
    $hostingPath = Join-Path $tempRoot 'hosting.json'
    Write-FixtureJson $hostingPath $hostingDocument
    $hostingProject.hosting_registry = $hostingPath
    $fixtureHosting = Get-KnowledgeHostedIdentityRegistry `
        $hostingProject `
        $packs `
        $fixtureOccurrences `
    @((New-KnowledgeHostingEntityProvider $entities))

    $interpretationDocument = ConvertTo-MutableFixtureValue (
        ConvertFrom-KnowledgeYamlFile `
            $project.interpretations_registry `
            1 `
            'structural interpretation registry'
    )
    $interpretationDocument['interpretations'] = [ordered]@{
        'candidate-structure' = [ordered]@{
            lifecycle = 'active'
            label = 'Candidate Structure'
            description = 'A provenance composition probe.'
        }
    }
    $interpretationDocument['members'] = [System.Collections.ArrayList]@(
        [ordered]@{
            id = 'candidate-entity'
            interpretation_id = 'candidate-structure'
            target_type = 'entity'
            target_id = 'alpha-concept'
        },
        [ordered]@{
            id = 'candidate-claim'
            interpretation_id = 'candidate-structure'
            target_type = 'provenance-claim'
            target_id = 'forward-structure-label'
        }
    )
    $interpretationPath = Join-Path $tempRoot 'interpretations.json'
    Write-FixtureJson $interpretationPath $interpretationDocument
    $interpretationProject = $project.PSObject.Copy()
    $interpretationProject.interpretations_registry = $interpretationPath
    $interpretationProviders = Get-KnowledgeInterpretationProjectTargetProviders `
        $sources `
        $entities `
        $reconciliations `
        $chronologyFixture `
        $fixtureOccurrences `
        $fixtureHosting
    $interpretations = Get-KnowledgeInterpretationRegistry `
        $interpretationProject `
        $packs `
        $interpretationProviders

    $interpretationAssertion = ConvertTo-MutableFixtureValue $baseDocument.assertions[0]
    $interpretationAssertion['id'] = 'interpretation-support'
    $interpretationAssertion['claim_key'] = 'forward-structure-label'
    $interpretationAssertion['subject_type'] = 'structural-interpretation'
    $interpretationAssertion['subject_id'] = 'candidate-structure'
    $interpretationAssertion['claim_namespace'] = 'structural-interpretation'
    $interpretationAssertion['field_path'] = 'label'
    $interpretationAssertion['asserted_value'] = 'Candidate Structure'
    $interpretationAssertion['evidence_links'][0]['locators'][0]['id'] = 'interpretation-support-locator'
    [void]$baseDocument.assertions.Add($interpretationAssertion)

    $bindingAssertion = ConvertTo-MutableFixtureValue $baseDocument.assertions[0]
    $bindingAssertion['id'] = 'carrier-binding-kind-support'
    $bindingAssertion['claim_key'] = 'vessel-body-b-binding-kind'
    $bindingAssertion['subject_type'] = 'host-carrier-binding'
    $bindingAssertion['subject_id'] = 'vessel-body-b'
    $bindingAssertion['claim_namespace'] = 'canonical-content'
    $bindingAssertion['field_path'] = 'binding_kind'
    $bindingAssertion['asserted_value'] = 'installed-in'
    $bindingAssertion['evidence_links'][0]['locators'][0]['id'] = 'carrier-binding-kind-support-locator'
    [void]$baseDocument.assertions.Add($bindingAssertion)

    $validPath = Join-Path $tempRoot 'valid.json'
    Write-FixtureJson $validPath $baseDocument
    $registry = Get-FixtureProvenanceRegistry `
        $project `
        $sources `
        $entities `
        $reconciliations `
        $packs `
        $fixtureOccurrences `
        $interpretations `
        $fixtureHosting `
        $validPath
    $interpretationTarget = Get-KnowledgeProvenanceTarget `
        $registry `
        'structural-interpretation' `
        'candidate-structure'
    if ($interpretationTarget.label -cne 'Candidate Structure') {
        throw 'Structural interpretation provenance dispatch returned the wrong target.'
    }
    $bindingTarget = Get-KnowledgeProvenanceTarget `
        $registry `
        'host-carrier-binding' `
        'vessel-body-b'
    if ($bindingTarget.binding_kind -cne 'installed-in') {
        throw 'Host-carrier-binding provenance dispatch returned the wrong target.'
    }
    Assert-ProvenanceFixtureCounts $registry $expectations.valid_counts
    Assert-ProvenanceAuthorityVectors $registry @($expectations.authority_vectors)
    Assert-ProvenanceFixtureServices $registry
    $invalidQueryCount = Assert-InvalidProvenanceQueries $registry
    if ($invalidQueryCount -ne [int]$expectations.invalid_query_cases) {
        throw 'Provenance invalid-query expectation count changed.'
    }

    foreach ($case in $expectations.invalid_cases) {
        $document = ConvertTo-MutableFixtureValue $baseDocument
        foreach ($operation in $case.operations) {
            Invoke-FixtureMutation $document $operation
        }
        $casePath = Join-Path $tempRoot ($case.id + '.json')
        Write-FixtureJson $casePath $document
        Assert-Rejected {
            Get-FixtureProvenanceRegistry `
                $project `
                $sources `
                $entities `
                $reconciliations `
                $packs `
                $fixtureOccurrences `
                $interpretations `
                $fixtureHosting `
                $casePath
        } "Malformed provenance configuration was accepted: $($case.id)"
    }

    $scaleDocument = ConvertTo-MutableFixtureValue $baseDocument
    $scaleCount = [int]$expectations.scale_additional_assertions
    Add-ScaleAssertions $scaleDocument $scaleCount
    $scalePath = Join-Path $tempRoot 'scale.json'
    Write-FixtureJson $scalePath $scaleDocument
    $scaleRegistry = Get-FixtureProvenanceRegistry `
        $project `
        $sources `
        $entities `
        $reconciliations `
        $packs `
        $fixtureOccurrences `
        $interpretations `
        $fixtureHosting `
        $scalePath
    if ($scaleRegistry.assertions.Count -ne $registry.assertions.Count + $scaleCount) {
        throw 'Provenance scale composition count changed.'
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

$summary = [ordered]@{
    schema_version = 1
    canonical_assertions = $canonical.assertions.Count
    canonical_claim_supersessions = $canonical.claim_supersessions.Count
    fixture_assertions = $registry.assertions.Count
    fixture_claim_supersessions = $registry.claim_supersessions.Count
    authority_vector_cases = @($expectations.authority_vectors).Count
    invalid_configuration_cases = @($expectations.invalid_cases).Count
    invalid_query_cases = $invalidQueryCount
    scale_additional_assertions = $scaleCount
}
if ($Json) {
    $summary | ConvertTo-Json -Compress
}
else {
    Write-Host (
        'Provenance conformance passed: {0} fixture assertions, {1} authority vectors, ' +
        '{2} malformed configurations, and {3} additional scale assertions.' -f
        $summary.fixture_assertions,
        $summary.authority_vector_cases,
        $summary.invalid_configuration_cases,
        $summary.scale_additional_assertions
    )
}
