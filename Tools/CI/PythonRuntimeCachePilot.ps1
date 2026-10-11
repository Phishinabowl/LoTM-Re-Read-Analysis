#Requires -Version 7.4
# Repository-owned pilot decisions; Cache@2 owns transport and post-job storage.

function Get-CiPythonRuntimePilotRepository {
    [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
}

function Invoke-CiPythonRuntimePilotNativeQualification {
    & (Join-Path $PSScriptRoot 'Capture-PythonRuntime.ps1') -Mode candidate
}

function Get-CiPythonRuntimePilotRoute {
    param([Parameter(Mandatory)]$Plan, [Parameter(Mandatory)][string]$StagingRoot,
        [Parameter(Mandatory)][string]$CacheHit, [Parameter(Mandatory)][string]$ToolsRoot,
        [ValidateSet('none', 'corrupt', 'missing-state')][string]$Fault = 'none',
        [datetime]$DeadlineUtc = [datetime]::MaxValue)
    if ($Fault -ne 'none' -and $CacheHit -cne 'true') {
        throw 'Fault qualification requires a real exact cache hit.'
    }
    $decision = Get-CiPythonSealedCacheDecision $Plan $StagingRoot $CacheHit -DeadlineUtc $DeadlineUtc
    $expected = Get-CiPythonCachePath $ToolsRoot "Python/$($Plan.identity.python_version)/x64"
    $comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if (-not $expected.Equals([IO.Path]::GetFullPath($Plan.identity.prefix), $comparison)) {
        throw 'Pilot tools root differs from the declared native prefix.'
    }
    $slot = Get-Item -LiteralPath $expected -Force -ErrorAction SilentlyContinue
    $completion = Get-Item -LiteralPath ($expected + '.complete') -Force -ErrorAction SilentlyContinue
    $occupied = [bool]$slot
    $marker = [bool]$completion
    if (-not $occupied -and $marker) {
        throw 'Absent runtime with stale completion marker is blocked.'
    }
    if ($occupied) {
        $null = Get-CiPythonCachePath $expected
        $executable = Get-Item -LiteralPath (Get-CiPythonCachePath $expected $Plan.identity.executable) -Force -ErrorAction SilentlyContinue
        if (-not $slot.PSIsContainer -or -not $marker -or $completion.PSIsContainer -or $completion.LinkType -or
            ($completion.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $completion.Length -ne 0 -or
            -not $executable -or $executable.PSIsContainer -or $executable.LinkType -or
            ($executable.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Occupied native slot is incomplete or unsafe; do not delegate an overwrite to native setup.'
        }
    }
    $route = if (-not $decision.cache_hit -or $occupied) {
        'native'
    }
    else {
        'restore'
    }
    if ($route -eq 'restore') {
        $null = Get-CiPythonRestorationDestination $Plan $ToolsRoot $StagingRoot -DeadlineUtc $DeadlineUtc
    }
    [pscustomobject]@{ route = $route
        cache_hit = $decision.cache_hit
        staged_integrity_verified = $decision.integrity_verified
        native_slot_present = $occupied
        reason = $(if (-not $decision.cache_hit) {
                'cache-miss'
            }
            elseif ($occupied) {
                'native-slot-present'
            }
            else {
                'sealed-hit-absent-slot'
            })
    }
}

function Read-CiPythonRuntimePilotState {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Plan,
        [Parameter(Mandatory)][string]$Strategy, [Parameter(Mandatory)][string]$Namespace)
    $state = (Read-CiPythonReferenceJson $Path).value
    if ($state.contract -cne 'ci-python-runtime-cache-pilot' -or
        ($state.schema_version -isnot [int] -and $state.schema_version -isnot [long]) -or $state.schema_version -ne 1 -or
        $state.executed_commit -cne $Plan.executed_commit -or $state.cache_key -cne $Plan.cache_key -or
        $state.strategy -cne $Strategy -or $state.cache_namespace -cne $Namespace -or
        $state.build_id -cne $env:BUILD_BUILDID) {
        throw 'Pilot receipt differs from current source/key/build/strategy.'
    }
    $state
}

function Invoke-CiPythonRuntimeCachePilot {
    param([ValidateSet('prepare', 'route', 'complete', 'report')][string]$Phase,
        [ValidateSet('native', 'cache')][string]$Strategy,
        [Parameter(Mandatory)][string]$Namespace,
        [ValidateSet('none', 'corrupt', 'missing-state')][string]$Fault = 'none')
    $phaseStart = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $context = Get-CiPythonHostedRestorationContext
    if ($Namespace -cnotmatch '^[a-z0-9][a-z0-9-]{0,39}$' -or ($Strategy -eq 'native' -and $Fault -ne 'none')) {
        throw 'Safe explicit cache namespace and cache-only fault mode required.'
    }
    $repo = Get-CiPythonRuntimePilotRepository
    $pins = (Read-CiPythonReferenceJson (Join-Path $PSScriptRoot 'Data/runtime-versions.json')).value
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $plan = Get-CiPythonSealedCachePlan $context $pins
    $planSeconds = $clock.Elapsed.TotalSeconds
    $output = Get-CiPythonCachePath $repo '.tmp/ci-runtime-cache-pilot'
    $stage = Get-CiPythonCachePath $repo '.tmp/ci-runtime-staging'
    $statePath = Join-Path $output 'pilot.json'
    if ($Phase -eq 'report') {
        $failurePath = Join-Path $output 'failure.json'
        $failed = [bool](Get-Item -LiteralPath $failurePath -Force -ErrorAction SilentlyContinue)
        $state = if (Test-Path -LiteralPath $statePath) {
            Read-CiPythonRuntimePilotState $statePath $plan $Strategy $Namespace
        }
        else {
            @{}
        }
        if (-not $state.Count -and -not $failed) {
            throw 'Pilot report requires owned result or failure evidence.'
        }
        $status = if ($failed -or $env:AGENT_JOBSTATUS -ceq 'Failed') {
            'failed'
        }
        elseif ($env:AGENT_JOBSTATUS -ceq 'Canceled') {
            'cancelled'
        }
        elseif ($state.status -ceq 'pilot-qualified') {
            'pilot-qualified'
        }
        else {
            'incomplete'
        }
        $failure = if ($failed) {
            (Read-CiPythonReferenceJson $failurePath).value
        }
        else {
            @{}
        }
        $routeLabel = if ($state.route) {
            $state.route.route
        }
        else {
            'not selected'
        }
        $reasonLabel = if ($state.route) {
            $state.route.reason
        }
        else {
            'admission not completed'
        }
        $hitLabel = if ($state.cache_hit) {
            $state.cache_hit
        }
        elseif ($failure.cache_hit) {
            $failure.cache_hit
        }
        else {
            'not recorded'
        }
        $restoreLabel = if ($state.restoration_exercised -eq $true) {
            'yes'
        }
        elseif ($state.restoration_exercised -eq $false) {
            'no'
        }
        else {
            'not reached'
        }
        $lines = [Collections.Generic.List[string]]::new()
        $lines.Add("# Python cache pilot: $status")
        $lines.Add('')
        $lines.Add("Image: $($context.image_family). Strategy: $Strategy. Build: $($env:BUILD_BUILDID).")
        $lines.Add("Source: $($plan.executed_commit).")
        $lines.Add('')
        $lines.Add("Route: $routeLabel. Reason: $reasonLabel. Exact cache result: $hitLabel.")
        $lines.Add("Real restoration exercised: $restoreLabel. Adoption: undecided; ordinary CI unchanged.")
        $lines.Add('')
        $lines.Add('| Measured component | Seconds |')
        $lines.Add('| --- | ---: |')
        foreach ($pair in @(
                @('Repository plan', 'plan'), @('Cache restore envelope', 'restore_envelope'),
                @('Staging admission and routing', 'route_admission'), @('Native setup envelope', 'native_setup_envelope'),
                @('Cold seed copy and verification', 'seed_copy_and_verify'), @('Qualification and preparation', 'qualification_and_preparation'))) {
            if ($state.seconds -and $state.seconds.Contains($pair[1])) {
                $lines.Add('| ' + $pair[0] + ' | ' + ([double]$state.seconds[$pair[1]]).ToString('F3', [Globalization.CultureInfo]::InvariantCulture) + ' |')
            }
        }
        $lines.Add('')
        $lines.Add('Envelopes include between-step overhead. Native/cache task durations, post-job save outcome/time, ' +
            'and whole-job/queue costs require the completed Azure timeline audit.')
        $lines.Add('Save eligibility is not proof of a saved cache. Native candidate-copy work is qualification/seed overhead, ' +
            'not ordinary native setup cost. An occupied-slot hit is not restoration proof.')
        $lines.Add('This is workload evidence; later artifact/cache post-job failures can still fail the hosted job.')
        if ($failed) {
            $lines.Add('')
            $lines.Add('Failure phase: ' + $failure.phase)
            $lines.Add('')
            $lines.Add('```text')
            $lines.Add($failure.error)
            $lines.Add('```')
        }
        $summary = Get-CiPythonCachePath $output ("python-cache-$($context.image_family).md")
        $lines | Set-Content -LiteralPath $summary -Encoding utf8
        Write-Host "##vso[task.uploadsummary]$summary"
        return
    }
    if ($Phase -eq 'prepare') {
        if ((Get-Item -LiteralPath $output -Force -ErrorAction SilentlyContinue) -or
            (Get-Item -LiteralPath $stage -Force -ErrorAction SilentlyContinue)) {
            throw 'Pilot diagnostic and staging owners must be fresh.'
        }
        $null = New-Item -ItemType Directory -Path $output
        $state = [ordered]@{ contract = 'ci-python-runtime-cache-pilot'
            schema_version = 1
            executed_commit = $plan.executed_commit
            build_id = $env:BUILD_BUILDID
            image = $context.image_family
            strategy = $Strategy
            cache_namespace = $Namespace
            cache_key = $plan.cache_key
            status = 'prepared'
            seconds = @{ plan = $planSeconds }
            cache_save_verified = $false
            handoff_admitted = $false
            adoption = 'undecided'
            prepared_at_unix_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        }
        $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding utf8
        Write-Host '##vso[task.setvariable variable=PILOT_OUTPUT_READY]true'
        Write-Host "##vso[task.setvariable variable=PILOT_PYTHON_VERSION]$($pins.python)"
        Write-Host "##vso[task.setvariable variable=PILOT_CACHE_KEY]$($plan.cache_key)"
        Write-Host "##vso[task.setvariable variable=PILOT_CACHE_NAMESPACE]$Namespace"
        Write-Host "##vso[task.setvariable variable=PILOT_STAGE]$stage"
        return
    }
    $state = $null
    $hit = $null
    try {
        $state = Read-CiPythonRuntimePilotState $statePath $plan $Strategy $Namespace
        $deadline = [datetime]::UtcNow.AddMinutes(5)
        if ($Phase -eq 'route') {
            if ($state.status -cne 'prepared') {
                throw 'Pilot routing requires the original prepared receipt.'
            }
            $state.seconds.restore_envelope = if ($Strategy -eq 'cache') {
                ($phaseStart - $state.prepared_at_unix_ms) / 1000.0
            }
            else {
                0
            }
            $hit = if ($Strategy -eq 'cache') {
                $env:PILOT_CACHE_HIT
            }
            else {
                'false'
            }
            $state.cache_hit = $hit
            $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding utf8
            if ($Fault -ne 'none' -and $hit -cne 'true') {
                throw 'Fault qualification requires a real exact cache hit.'
            }
            if ($Fault -eq 'missing-state') {
                # Remove only this freshly owned diagnostic receipt, never cache or native bytes.
                [IO.File]::Delete($statePath)
                $null = Read-CiPythonRuntimePilotState $statePath $plan $Strategy $Namespace
            }
            elseif ($Fault -eq 'corrupt') {
                $null = Get-CiPythonSealedCacheDecision $plan $stage true -DeadlineUtc $deadline
                [IO.File]::WriteAllText((Get-CiPythonCachePath $stage $plan.identity.executable), 'deliberate private-stage corruption')
            }
            $routeClock = [Diagnostics.Stopwatch]::StartNew()
            $route = Get-CiPythonRuntimePilotRoute $plan $stage $hit $env:AGENT_TOOLSDIRECTORY -Fault $Fault -DeadlineUtc $deadline
            $state.route = $route
            $state.seconds.route_admission = $routeClock.Elapsed.TotalSeconds
            $state.cache_hit = $hit
            # Envelope includes between-step overhead; task timeline supplies authoritative transport duration.
            $state.native_envelope_start_unix_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
            $state.status = 'routed'
            $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding utf8
            Write-Host "##vso[task.setvariable variable=PILOT_ROUTE]$($route.route)"
            Write-Host "Pilot route: $($route.route); $($route.reason). No ordinary handoff."
            return
        }
        if ($state.status -cne 'routed' -or $state.route.route -cnotin 'native', 'restore') {
            throw 'Pilot completion requires the original routed receipt.'
        }
        $workClock = [Diagnostics.Stopwatch]::StartNew()
        if ($state.route.route -ceq 'native') {
            $state.seconds.native_setup_envelope = ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() - $state.native_envelope_start_unix_ms) / 1000.0
            Invoke-CiPythonRuntimePilotNativeQualification
            $qualification = (Read-CiPythonReferenceJson (Join-Path $repo '.tmp/ci-runtime-capture/candidate-qualification.json')).value
            Test-CiPythonCompletedQualification $qualification $plan.executed_commit
            $candidateRoot = Get-CiPythonCachePath $repo '.tmp/ci-runtime-candidates/runtime'
            $null = Get-CiPythonSealedCacheDecision $plan $candidateRoot true -DeadlineUtc ([datetime]::UtcNow.AddMinutes(5))
            if ($Strategy -eq 'cache' -and $state.cache_hit -ceq 'false') {
                $null = Get-CiPythonSealedCacheDecision $plan $stage false -DeadlineUtc ([datetime]::UtcNow.AddMinutes(5))
                # Cache@2 may create an empty miss owner; remove only the verified empty scratch directory.
                if (Test-Path -LiteralPath $stage) {
                    [IO.Directory]::Delete($stage, $false)
                }
                $copyClock = [Diagnostics.Stopwatch]::StartNew()
                $null = New-CiPythonSealedPrivateCopy $plan $candidateRoot $repo $stage -DeadlineUtc ([datetime]::UtcNow.AddMinutes(5))
                $state.seconds.seed_copy_and_verify = $copyClock.Elapsed.TotalSeconds
            }
            if ($Strategy -eq 'cache') {
                $null = Get-CiPythonSealedCacheDecision $plan $stage true -DeadlineUtc ([datetime]::UtcNow.AddMinutes(5))
            }
            $state.restoration_exercised = $false
        }
        else {
            if ($Strategy -cne 'cache' -or $state.cache_hit -cne 'true') {
                throw 'Restoration requires a verified exact cache hit.'
            }
            # Use a child shell so the driver's explicit exit cannot terminate this receipt owner.
            & (Join-Path $PSHOME $(if ($IsWindows) {
                        'pwsh.exe'
                    }
                    else {
                        'pwsh'
                    })) -NoProfile -File (Join-Path $PSScriptRoot 'Restore-PythonRuntime.ps1')
            $exitCode = $LASTEXITCODE
            $restored = (Read-CiPythonReferenceJson (Join-Path $repo '.tmp/ci-runtime-restore/restoration-qualification.json')).value
            if ($exitCode -ne 0 -or $restored.status -cne 'restoration-qualified' -or $restored.restoration_verified -isnot [bool] -or
                -not $restored.restoration_verified -or
                $restored.executed_commit -cne $plan.executed_commit -or $restored.cache_key -cne $plan.cache_key) {
                throw 'Real restored qualification failed; retain nested receipts.'
            }
            $state.restoration_exercised = $true
        }
        $state.seconds.qualification_and_preparation = $workClock.Elapsed.TotalSeconds
        $state.status = 'pilot-qualified'
        $state.cache_save_eligible = ($Strategy -eq 'cache' -and $state.cache_hit -ceq 'false')
        $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding utf8
        Write-Host 'Pilot qualified. Cache save is a later Azure post-job task, not confirmed by this receipt.'
    }
    catch {
        @{ contract = 'ci-python-runtime-cache-pilot-failure'
            executed_commit = $plan.executed_commit
            build_id = $env:BUILD_BUILDID
            phase = $Phase
            fault = $Fault
            cache_hit = $(if ($hit) {
                    $hit
                }
                else {
                    $state.cache_hit
                })
            failure_type = $_.Exception.GetType().Name
            error = $_.Exception.Message.Substring(0, [Math]::Min(800, $_.Exception.Message.Length))
            handoff_admitted = $false
            cache_save_eligible = $false
            adoption = 'undecided'
        } |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'failure.json') -Encoding utf8
        throw
    }
}
