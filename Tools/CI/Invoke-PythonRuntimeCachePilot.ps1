#Requires -Version 7.4
param([Parameter(Mandatory)][ValidateSet('prepare', 'route', 'complete', 'report')][string]$Phase,
    [Parameter(Mandatory)][ValidateSet('native', 'cache')][string]$Strategy,
    [Parameter(Mandatory)][string]$Namespace,
    [ValidateSet('none', 'corrupt', 'missing-state')][string]$Fault = 'none')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PythonRuntimeCache.ps1')
. (Join-Path $PSScriptRoot 'PythonRuntimeCachePilot.ps1')
Invoke-CiPythonRuntimeCachePilot -Phase $Phase -Strategy $Strategy -Namespace $Namespace -Fault $Fault
