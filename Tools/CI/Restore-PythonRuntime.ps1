#Requires -Version 7.4
# Manual pilot only; no cache tasks, registration, save or ordinary runtime handoff.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PythonRuntimeCache.ps1')
$context = Get-CiPythonHostedRestorationContext
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$pins = (Read-CiPythonReferenceJson (Join-Path $PSScriptRoot 'Data/runtime-versions.json')).value
$plan = Get-CiPythonSealedCachePlan $context $pins
$stage = Get-CiPythonCachePath $repo '.tmp/ci-runtime-staging'
$output = Get-CiPythonCachePath $repo '.tmp/ci-runtime-restore'
if (Get-Item -LiteralPath $output -Force -ErrorAction SilentlyContinue) {
    throw 'Restoration diagnostic owner must be fresh.'
}
$null = New-Item -ItemType Directory -Path $output
Write-Host '##vso[task.setvariable variable=RESTORE_OUTPUT_READY]true'
$report = [ordered]@{ contract = 'ci-python-runtime-restoration-qualification'
    schema_version = 1
    executed_commit = $context.executed_commit
    cache_key = $plan.cache_key
    identity = $plan.identity
    status = 'failed'
    exit_code = 1
    executed = $false
    execution_attempted = $false
    integrity_verified = $false
    runtime_probe_verified = $false
    environment_verified = $false
    restoration_verified = $false
    handoff_admitted = $false
    saved = $false
}
try {
    $deadline = [datetime]::UtcNow.AddMinutes(5)
    $destination = Get-CiPythonRestorationDestination $plan $env:AGENT_TOOLSDIRECTORY $stage -DeadlineUtc $deadline
    $copy = Copy-CiPythonSealedRuntime $plan $stage $env:AGENT_TOOLSDIRECTORY $destination.target -Restoration -DeadlineUtc $deadline
    $copy | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $output 'restored-copy.json') -Encoding utf8
    $reference = Get-CiPythonPlatformReference $context.os $pins -DeadlineUtc $deadline
    # Adapt to the existing qualification protocol; the external PowerShell seal remains authoritative.
    $candidate = [ordered]@{ contract = 'ci-python-runtime-candidate'
        schema_version = $(if ($IsLinux) {
                2
            }
            else {
                1
            })
        normalization = $reference.identity.normalization
        status = 'candidate-complete'
        inventory = $reference.inventory
        trusted_seal = $false
        runtime_probe_verified = $false
        handoff_admitted = $false
        saved = $false
    }
    if ($IsLinux) {
        $candidate.reference = @{ identity = $reference.identity
            sha256 = $reference.reference_sha256
            inventory_sha256 = $reference.inventory.sha256
        }
        $candidate.source_root_mode = 493
        $candidate.mode_changes = @()
    }
    $receipt = Join-Path $output 'candidate.json'
    $candidate | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receipt -Encoding utf8
    # Recheck full external seals immediately before the first restored-byte execution.
    $null = Get-CiPythonSealedCacheDecision $plan $destination.target true -DeadlineUtc $deadline
    $report.integrity_verified = $true
    $report.execution_attempted = $true
    & (Join-Path $destination.target $plan.identity.executable) -I -B (Join-Path $PSScriptRoot 'qualify_runtime_candidate.py') `
        --candidate $destination.target --receipt $receipt --output $output --restored
    $report.executed = $true
    if ($LASTEXITCODE -ne 0) {
        if ($LASTEXITCODE -eq 130) {
            $report.status = 'cancelled'
            $report.exit_code = 130
        }
        elseif ($LASTEXITCODE -eq 124) {
            $report.status = 'timed-out'
            $report.exit_code = 124
        }
        throw 'Restored runtime probes failed; retain qualification diagnostics.'
    }
    $qualified = (Read-CiPythonReferenceJson (Join-Path $output 'candidate-qualification.json')).value
    Test-CiPythonCompletedQualification $qualified $context.executed_commit
    $finalDeadline = [datetime]::UtcNow.AddMinutes(2)
    $null = Get-CiPythonSealedCacheDecision $plan $destination.target true -DeadlineUtc $finalDeadline
    $null = Get-CiPythonSealedCacheDecision $plan $stage true -DeadlineUtc $finalDeadline
    $report.status = 'restoration-qualified'
    $report.exit_code = 0
    $report.runtime_probe_verified = $true
    $report.environment_verified = $true
    $report.restoration_verified = $true
    Write-Host 'Owned restoration and fresh environment qualified; no cache save or ordinary handoff.'
}
catch {
    $report.failure_type = $_.Exception.GetType().Name
    $report.error = $_.Exception.Message.Substring(0, [Math]::Min(800, $_.Exception.Message.Length))
    if ($_.Exception -is [OperationCanceledException]) {
        $report.status = 'cancelled'
        $report.exit_code = 130
    }
    elseif ($_.Exception -is [TimeoutException]) {
        $report.status = 'timed-out'
        $report.exit_code = 124
    }
}
finally {
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $output 'restoration-qualification.json') -Encoding utf8
}
exit $report.exit_code
