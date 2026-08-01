[CmdletBinding()]
param([string]$Root)

$ErrorActionPreference="Stop"
if([string]::IsNullOrWhiteSpace($Root)){$Root=Split-Path -Parent $PSScriptRoot}
$Root=[System.IO.Path]::GetFullPath($Root)
. (Join-Path $PSScriptRoot "Project-Config.ps1")
. (Join-Path $PSScriptRoot "Schema-Pack-Config.ps1")
. (Join-Path $PSScriptRoot "Temporal-Config.ps1")
$project=Get-KnowledgeProjectConfig $Root
$packs=Get-KnowledgeSchemaPackRegistry $project
$fixtures=Join-Path $Root "Framework\Data\Temporal"
$valid=ConvertFrom-KnowledgeYamlFile (Join-Path $fixtures "valid-windows.yaml") 2 "Temporal fixture"
$windows=[ordered]@{}
foreach($entry in $valid.windows.GetEnumerator()){$windows[$entry.Key]=ConvertTo-KnowledgeTemporalWindow ([ordered]@{window=$entry.Value}) "window" "windows.$($entry.Key)" $packs}
$malformed=ConvertFrom-KnowledgeYamlFile (Join-Path $fixtures "invalid-windows.yaml") 2 "Temporal fixture"
foreach($entry in $malformed.windows.GetEnumerator()){$rejected=$false;try{$null=ConvertTo-KnowledgeTemporalWindow ([ordered]@{window=$entry.Value}) "window" "windows.$($entry.Key)" $packs}catch{$rejected=$true};if(-not $rejected){throw "Malformed temporal window was accepted: $($entry.Key)"}}
$expected=Get-Content -Raw (Join-Path $fixtures "expectations.json")|ConvertFrom-Json
foreach($case in @($expected.matches)){$query=ConvertTo-KnowledgeTemporalInstant $case[1];$outcome=Get-KnowledgeTemporalMatch $windows[$case[0]] $query;if($null -eq $outcome){$outcome="not-effective"};if($outcome -ne $case[2]){throw "Temporal match vector failed for $($case[0]) at $($case[1]): $outcome"}}
foreach($case in @($expected.overlaps)){$outcome=Get-KnowledgeTemporalOverlap $windows[$case[0]] $windows[$case[1]];if($outcome -ne $case[2]){throw "Temporal overlap vector failed for $($case[0]) / $($case[1]): $outcome"}}
$subMicrosecond=[datetimeoffset]::new(2025,1,1,0,0,0,[timespan]::Zero).AddTicks(1);$rejected=$false;try{$null=ConvertTo-KnowledgeTemporalInstant $subMicrosecond}catch{$rejected=$true};if(-not $rejected){throw "A runtime datetime finer than microsecond precision was accepted."}
Write-Output "Temporal conformance passed: $($windows.Count) valid windows, $($malformed.windows.Count) malformed windows, $(@($expected.matches).Count) match and $(@($expected.overlaps).Count) overlap vectors."
