#Requires -Version 7.4
param()
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
