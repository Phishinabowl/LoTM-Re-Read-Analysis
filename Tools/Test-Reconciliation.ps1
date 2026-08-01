[CmdletBinding()]
param(
  [string]$Root,
  [int]$DeepChain = 1500
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = Split-Path -Parent $PSScriptRoot }
$Root = [System.IO.Path]::GetFullPath($Root)

. (Join-Path $PSScriptRoot "Taxonomy-Config.ps1")
. (Join-Path $PSScriptRoot "Resource-Config.ps1")
. (Join-Path $PSScriptRoot "Source-Config.ps1")
. (Join-Path $PSScriptRoot "Entity-Config.ps1")
. (Join-Path $PSScriptRoot "Reconciliation-Config.ps1")

$project=Get-KnowledgeProjectConfig $Root
$packs=Get-KnowledgeSchemaPackRegistry $project
$taxonomy=Get-KnowledgeTaxonomyConfig $project
$resources=Get-KnowledgeResourceConfig $project
$sources=Get-KnowledgeSourceRegistry $project $resources $packs
$entities=Get-KnowledgeEntityRegistry $project $taxonomy $sources $packs
$providers=@(
  (Get-KnowledgeTaxonomyReconciliationProvider $taxonomy),
  (Get-KnowledgeResourceReconciliationProvider $resources),
  (Get-KnowledgeSourceReconciliationProvider $sources),
  (Get-KnowledgeEntityReconciliationProvider $entities)
)
$providers[0].targets["category"]["current-category"]=[pscustomobject]@{id="current-category"}
$providers[0].targets["category"]["history-source"]=[pscustomobject]@{id="history-source"}
$providers[0].targets["category"]["reversed-source"]=[pscustomobject]@{id="reversed-source"}
$providers[0].targets["content-type"]["current-content-type"]=[pscustomobject]@{id="current-content-type"}
$providers[0].aliases["category"]=[ordered]@{"old-alias"="current-category"}

function Get-TestRegistry([string]$Path) {
  $testProject=$project.PSObject.Copy()
  $testProject.reconciliation_registry=[System.IO.Path]::GetFullPath($Path)
  return Get-KnowledgeReconciliationRegistry $testProject $providers $packs
}

function ConvertTo-NormalizedResolution([object]$Resolution) {
  $canonical=@($Resolution.canonical_targets|ForEach-Object {"$($_.target_type):$($_.target_id)"})
  $branchList=New-Object 'System.Collections.Generic.List[object]'
  foreach($branch in @($Resolution.branches)) {
    $target=$null
    if($null -ne $branch.canonical_target){$target="$($branch.canonical_target.target_type):$($branch.canonical_target.target_id)"}
    $branchList.Add(@([string]$branch.outcome,$target,@($branch.reconciliation_ids)))
  }
  return [ordered]@{target_type=$Resolution.requested_type;target_id=$Resolution.requested_id;outcome=$Resolution.outcome;canonical=@($canonical);branches=$branchList.ToArray()}
}

$fixtures=Join-Path $Root "Framework\Data\Reconciliation"
$strictYamlFixtures=Join-Path $Root "Framework\Data\Strict-Yaml"
$mappingKeys=ConvertFrom-KnowledgeYamlFile (Join-Path $strictYamlFixtures "valid-mapping-keys.yaml") 1 "Strict YAML fixture"
$expectedKeys=@("1","true","on","dotted.key","hyphen-key","underscore_key")
$actualKeys=@($mappingKeys.mapping_keys.Keys|Sort-Object)
if(($actualKeys -join "|") -cne (($expectedKeys|Sort-Object) -join "|")){throw "Canonical mapping-key fixture did not preserve string keys."}
foreach($key in $actualKeys){if($key -isnot [string]){throw "Canonical mapping-key fixture produced a non-string key."}}
foreach($name in @("invalid-boolean-key.yaml","invalid-integer-key.yaml","invalid-empty-key.yaml","invalid-uppercase-key.yaml","invalid-case-collision.yaml","invalid-unicode-key.yaml","invalid-punctuation-key.yaml","invalid-complex-key.yaml","invalid-duplicate-key.yaml")){
  $rejected=$false
  try{$null=ConvertFrom-KnowledgeYamlFile (Join-Path $strictYamlFixtures $name) 1 "Strict YAML fixture"}catch{$rejected=$true}
  if(-not $rejected){throw "Noncanonical mapping-key fixture was accepted: $name"}
}
$registry=Get-TestRegistry (Join-Path $fixtures "valid-v4.yaml")
$scalarRegistry=Get-TestRegistry (Join-Path $fixtures "valid-scalar-parity.yaml")
if([string]$scalarRegistry.records[0].source_label -cne "on"){throw "Legacy YAML Boolean word did not remain a string."}
$expectations=Get-Content -Raw (Join-Path $fixtures "expectations.json")|ConvertFrom-Json
foreach($case in @($expectations.resolutions)){
  $actual=ConvertTo-NormalizedResolution (Resolve-KnowledgeReconciliationTarget $registry $case.target_type $case.target_id)
  $actualJson=$actual|ConvertTo-Json -Depth 20 -Compress
  $expectedJson=$case|ConvertTo-Json -Depth 20 -Compress
  if($actualJson -ne $expectedJson){throw "Reconciliation resolution vector failed for $($case.target_type):$($case.target_id).`nExpected: $expectedJson`nActual:   $actualJson"}
}

foreach($name in @("invalid-operation-reason.yaml","invalid-alias-conflict.yaml","invalid-audit.yaml","invalid-reclassify.yaml","invalid-active-cycle.yaml","invalid-unknown-terminal.yaml","invalid-source-state.yaml","invalid-label-mode.yaml","invalid-supersession-cycle.yaml","invalid-duplicate-key.yaml","invalid-schema-string.yaml","invalid-unknown-field.yaml","invalid-timestamp-case.yaml","invalid-timestamp-offset.yaml","invalid-resolution-type.yaml","invalid-resolution-field.yaml","invalid-schema-decimal.yaml","invalid-record-field.yaml","invalid-target-field.yaml","invalid-audit-field.yaml","invalid-present-retire.yaml","invalid-uppercase-controlled-value.yaml","invalid-schema-explicit-tag.yaml","invalid-schema-hex.yaml","invalid-schema-plus.yaml","invalid-schema-leading-zero.yaml","invalid-merge-key.yaml","invalid-timestamp-hour.yaml","invalid-timestamp-zone-minute.yaml","invalid-present-merge.yaml","invalid-record-limit.yaml","invalid-target-limit.yaml","invalid-document-marker.yaml","invalid-unquoted-timestamp.yaml","invalid-leading-zero-limit.yaml","invalid-trailing-decimal.yaml","invalid-negative-trailing-decimal.yaml","invalid-trailing-decimal-exponent.yaml","invalid-tilde-null.yaml","invalid-empty-null.yaml")){
  $rejected=$false
  try{$null=Get-TestRegistry (Join-Path $fixtures $name)}catch{$rejected=$true}
  if(-not $rejected){throw "Malformed reconciliation fixture was accepted: $name"}
}

$limited=Get-TestRegistry (Join-Path $fixtures "branch-limit.yaml")
$limitRejected=$false
try{$null=Resolve-KnowledgeReconciliationTarget $limited "category" "branch-limit-source"}catch{$limitRejected=$true}
if(-not $limitRejected){throw "Reconciliation branch limit did not stop expansion."}

$stepLimited=Get-TestRegistry (Join-Path $fixtures "resolution-step-limit.yaml")
$stepRejected=$false
try{$null=Resolve-KnowledgeReconciliationTarget $stepLimited "category" "step-limit-a"}catch{$stepRejected=$true}
if(-not $stepRejected){throw "Reconciliation step limit did not stop traversal."}

$records=New-Object 'System.Collections.Generic.List[object]'
for($i=0;$i -lt $DeepChain;$i++){
  $sourceId="deep-{0:D4}" -f $i
  if($i+1 -lt $DeepChain){$targetId="deep-{0:D4}" -f ($i+1)}else{$targetId="current-category"}
  $records.Add([ordered]@{
    id="deep-record-{0:D4}" -f $i;source_type="category";source_id=$sourceId;source_state="tombstone";source_label_mode="omitted"
    operation="redirect";targets=@([ordered]@{target_type="category";target_id=$targetId});reason="renamed";status="active";audit=[ordered]@{mode="repository-history"}
  })
}
$tempPath=Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-reconciliation-{0}.yaml" -f [guid]::NewGuid().ToString("N"))
$byteTestPath=Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-yaml-bytes-{0}.yaml" -f [guid]::NewGuid().ToString("N"))
try{
  foreach($case in @(
    [pscustomobject]@{Name="invalid UTF-8";Bytes=[byte[]](0x73,0x63,0x68,0x65,0x6D,0x61,0x5F,0x76,0x65,0x72,0x73,0x69,0x6F,0x6E,0x3A,0x20,0x34,0x0A,0xFF)},
    [pscustomobject]@{Name="UTF-8 BOM";Bytes=[byte[]](@(0xEF,0xBB,0xBF)+[System.IO.File]::ReadAllBytes((Join-Path $fixtures "valid-v4.yaml")))}
  )){
    [System.IO.File]::WriteAllBytes($byteTestPath,$case.Bytes)
    $rejected=$false
    try{$null=Get-TestRegistry $byteTestPath}catch{$rejected=$true}
    if(-not $rejected){throw "Byte-level YAML fixture was accepted: $($case.Name)"}
  }
  $emoji=[char]::ConvertFromUtf32(0x1F600)
  $rejected=$false
  try{Assert-KnowledgeYamlSource "value: $emoji$emoji`n" "Test registry" $byteTestPath -MaxScalarBytes 7}catch{$rejected=$true}
  if(-not $rejected){throw "UTF-8 scalar-byte budget did not reject two emoji."}
  $rejected=$false
  try{Assert-KnowledgeYamlSource "value: 12`n" "Test registry" $byteTestPath -MaxBytes 9}catch{$rejected=$true}
  if(-not $rejected){throw "UTF-8 file-byte budget was not enforced."}

  [System.IO.File]::WriteAllText($tempPath,([ordered]@{schema_version=4;resolution=[ordered]@{max_branches=65536;max_records=[Math]::Max($DeepChain+1,100000);max_targets_per_record=4096;max_resolution_steps=[Math]::Max($DeepChain+1,250000)};records=$records.ToArray()}|ConvertTo-Json -Depth 10),[System.Text.UTF8Encoding]::new($false))
  $deep=Get-TestRegistry $tempPath
  $result=Resolve-KnowledgeReconciliationTarget $deep "category" "deep-0000"
  if($result.outcome -ne "redirected" -or @($result.reconciliation_ids).Count -ne $DeepChain){throw "Deep reconciliation chain did not resolve completely."}
}finally{
  if(Test-Path -LiteralPath $tempPath){Remove-Item -LiteralPath $tempPath -Force}
  if(Test-Path -LiteralPath $byteTestPath){Remove-Item -LiteralPath $byteTestPath -Force}
}

Write-Output "Reconciliation conformance passed: $(@($expectations.resolutions).Count) vectors, 40 malformed reconciliation fixtures, 9 malformed mapping-key fixtures, byte/scalar/key parity, branch and step limits, $DeepChain-hop chain."
