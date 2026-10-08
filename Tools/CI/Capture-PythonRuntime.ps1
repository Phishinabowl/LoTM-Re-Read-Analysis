#Requires -Version 7.4
param([ValidateSet('raw', 'candidate')][string]$Mode = 'raw')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PythonRuntimeCache.ps1')
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$pins = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Data/runtime-versions.json') -Raw | ConvertFrom-Json -AsHashtable
if ($env:TF_BUILD -cne 'True' -or $env:BUILD_REASON -cne 'Manual' -or
    $env:LOTM_RUNTIME_CAPTURE -cne 'hosted-capture-only' -or
    $env:BUILD_SOURCESDIRECTORY -cne $repo) {
    throw 'This capture entry point is restricted to the explicit Azure hosted pilot.'
}
$output = Get-CiPythonCachePath (Join-Path $repo '.tmp/ci-runtime-capture')
if (Test-Path -LiteralPath $output) {
    throw 'Capture output owner must be fresh.'
}
$null = New-Item -ItemType Directory -Path $output
Write-Host '##vso[task.setvariable variable=CAPTURE_OUTPUT_READY]true'
try {
    $root = Get-CiPythonNativeCaptureRoot -ToolsRoot $env:AGENT_TOOLSDIRECTORY `
        -SelectedLocation $env:NATIVE_PYTHON_LOCATION -RuntimeVersions $pins
    $context = @{ host = 'ado'
        event = $env:BUILD_REASON
        hosted = $true
        os = $(if ($IsWindows) {
                'windows'
            }
            else {
                'linux'
            })
        image_family = $env:CAPTURE_IMAGE
        architecture = 'x64'
        executed_commit = $env:BUILD_SOURCEVERSION
        capture_id = $env:CAPTURE_ID
    }
    $result = Get-CiPythonRuntimeCapture $context $pins $root -DeadlineUtc ([datetime]::UtcNow.AddMinutes(5))
    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $output 'capture.json') -Encoding utf8
    Write-Host "Raw capture: $($result.inventory.entries.Count) entries. No trusted seal, restoration or runtime handoff."
    if ($Mode -eq 'candidate') {
        $workspace = Get-CiPythonCachePath (Join-Path $repo '.tmp/ci-runtime-candidates')
        if (Test-Path -LiteralPath $workspace) {
            throw 'Candidate pilot workspace must be fresh.'
        }
        $null = New-Item -ItemType Directory -Path $workspace
        $destination = Join-Path $workspace 'runtime'
        $candidate = New-CiPythonRuntimeCandidate $root $workspace $destination $pins -DeadlineUtc ([datetime]::UtcNow.AddMinutes(5))
        $candidate | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $output 'candidate.json') -Encoding utf8
        $nativeExe = Join-Path $root $(if ($IsWindows) {
                'python.exe'
            }
            else {
                'bin/python3.14'
            })
        & $nativeExe -I -B (Join-Path $PSScriptRoot 'qualify_runtime_candidate.py') `
            --candidate $destination --receipt (Join-Path $output 'candidate.json') --output $output
        if ($LASTEXITCODE -ne 0) {
            throw 'Candidate qualification failed; see retained report and process diagnostics.'
        }
        $finalDeadline = [datetime]::UtcNow.AddMinutes(2)
        if ((Get-CiPythonRuntimeInventory $destination -SealModes -DeadlineUtc $finalDeadline).sha256 -cne $candidate.inventory.sha256 -or
            (Get-CiPythonRuntimeInventory $root -CaptureOnly -DeadlineUtc $finalDeadline).sha256 -cne $candidate.source_sha256) {
            throw 'Candidate or native source changed during qualification.'
        }
        Write-Host 'Normalized candidate and fresh locked environment qualified; no cache or restore admission.'
    }
}
catch {
    $message = $_.Exception.Message
    if ($message.Length -gt 800) {
        $message = $message.Substring(0, 800)
    }
    @{ contract = 'ci-python-runtime-capture-failure'
        error = $message
        trusted_seal = $false
        handoff_admitted = $false
        saved = $false
    } | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $output 'failure.json') -Encoding utf8
    throw
}
