$script:KnowledgeRfc3339Pattern = "^(?<date>\d{4}-\d{2}-\d{2})T(?<time>\d{2}:\d{2}:\d{2})(?:\.\d{1,6})?(?<zone>Z|(?<sign>[+-])(?<hour>\d{2}):(?<minute>\d{2}))$"
$script:KnowledgeCanonicalIntegerPattern = '^-?(?:0|[1-9][0-9]*)$'
$script:KnowledgeCanonicalMappingKeyPattern = '^[a-z0-9]+(?:[_.-][a-z0-9]+)*$'
$script:KnowledgeNumericLikePattern = '^[+-]?(?:[0-9][0-9_]*|0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|[0-9][0-9_]*(?::[0-9_]+)+|(?:[0-9][0-9_]*\.[0-9_]*|\.[0-9_]+)(?:[eE][+-]?[0-9_]+)?|[0-9][0-9_]*[eE][+-]?[0-9_]+|\.(?:inf|Inf|INF|nan|NaN|NAN))$'
$script:KnowledgeTimestampLikePattern = '^[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt ][0-9]{2}:[0-9]{2}:[0-9]{2}.*)?$'
$script:KnowledgeMaxYamlBytes = 16 * 1024 * 1024
$script:KnowledgeMaxYamlDepth = 128
$script:KnowledgeMaxYamlNodes = 500000
$script:KnowledgeMaxYamlScalarBytes = 4 * 1024 * 1024

function Import-KnowledgeYamlModule {
  try {
    Import-Module powershell-yaml -ErrorAction Stop
  } catch {
    throw "Project configuration requires the PowerShell module 'powershell-yaml'. Install it with: Install-Module powershell-yaml -Scope CurrentUser -Force -AllowClobber"
  }
}

function Get-KnowledgeYamlSchemaToken {
  param([string]$Text,[string]$Context)
  $trimmed=$Text.TrimStart()
  if($trimmed.StartsWith("{")){
    $matches=[regex]::Matches($Text,'(?m)^\s*"schema_version"\s*:\s*(?<value>[^,\s}]+)')
  }else{
    $matches=[regex]::Matches($Text,'(?m)^\uFEFF?schema_version\s*:\s*(?<value>[^\s,#}]+)')
  }
  if($matches.Count -ne 1){throw "$Context must declare exactly one root schema_version scalar."}
  return $matches[0].Groups['value'].Value
}

function Assert-KnowledgeYamlSource {
  param(
    [string]$Text,[string]$Context,[string]$Path,
    [int]$MaxBytes=$script:KnowledgeMaxYamlBytes,
    [int]$MaxDepth=$script:KnowledgeMaxYamlDepth,
    [int]$MaxNodes=$script:KnowledgeMaxYamlNodes,
    [int]$MaxScalarBytes=$script:KnowledgeMaxYamlScalarBytes
  )
  $byteCount=[System.Text.Encoding]::UTF8.GetByteCount($Text)
  if($byteCount -gt $MaxBytes){throw "$Context exceeds the $MaxBytes-byte YAML limit: $Path"}
  $reader=[System.IO.StringReader]::new($Text)
  $parser=[YamlDotNet.Core.Parser]::new($reader)
  $depth=0;$nodeCount=0
  $frames=New-Object 'System.Collections.Generic.List[object]'
  try{
    while($parser.MoveNext()){
      $event=$parser.Current;$type=$event.GetType().Name
      $isNode=$type -eq 'MappingStart' -or $type -eq 'SequenceStart' -or $type -eq 'Scalar'
      $isMappingKey=$false
      $parent=$null
      if($isNode -and $frames.Count -gt 0){
        $parent=$frames[$frames.Count-1]
        if($parent.kind -eq 'mapping'){
          $isMappingKey=[bool]$parent.expect_key
          $parent.expect_key=-not $parent.expect_key
        }
      }
      if($type -eq 'AnchorAlias'){throw "$Context uses unsupported YAML aliases: $Path"}
      if(($type -eq 'DocumentStart' -or $type -eq 'DocumentEnd') -and -not $event.IsImplicit){throw "$Context must be one implicit YAML document without document markers: $Path"}
      if($event -is [YamlDotNet.Core.Events.NodeEvent]){
        if(-not $event.Anchor.IsEmpty -or -not $event.Tag.IsEmpty){throw "$Context uses unsupported YAML anchors or tags: $Path"}
      }
      if($type -eq 'MappingStart' -or $type -eq 'SequenceStart'){
        if($isMappingKey){throw "$Context mapping keys must be scalar strings: $Path"}
        $depth++;$nodeCount++
        if($depth -gt $MaxDepth){throw "$Context exceeds YAML nesting depth $MaxDepth`: $Path"}
        if($type -eq 'MappingStart'){
          $frames.Add([pscustomobject]@{
            kind='mapping'
            expect_key=$true
            seen_keys=(New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal))
          })
        }else{$frames.Add([pscustomobject]@{kind='sequence';expect_key=$false;seen_keys=$null})}
      }elseif($type -eq 'MappingEnd' -or $type -eq 'SequenceEnd'){
        $depth--
        if($frames.Count -gt 0){$frames.RemoveAt($frames.Count-1)}
      }
      elseif($type -eq 'Scalar'){
        $nodeCount++;$value=[string]$event.Value
        $scalarBytes=[System.Text.Encoding]::UTF8.GetByteCount($value)
        if($scalarBytes -gt $MaxScalarBytes){throw "$Context contains a scalar larger than $MaxScalarBytes UTF-8 bytes: $Path"}
        if($isMappingKey){
          if($event.Style -eq [YamlDotNet.Core.ScalarStyle]::Plain -and (
            @('true','false','null') -ccontains $value -or $value -cmatch $script:KnowledgeNumericLikePattern
          )){throw "$Context mapping key '$value' must be quoted to remain a string: $Path"}
          if($value -cnotmatch $script:KnowledgeCanonicalMappingKeyPattern){throw "$Context contains noncanonical mapping key '$value'; keys must be lowercase machine identifiers: $Path"}
          if(-not $parent.seen_keys.Add($value)){throw "$Context contains duplicate mapping key '$value': $Path"}
        }
        if($event.Style -eq [YamlDotNet.Core.ScalarStyle]::Plain){
          if($value.Length -eq 0){throw "$Context must write null explicitly as lowercase 'null': $Path"}
          if($value -ceq '<<'){throw "$Context uses unsupported YAML merge keys: $Path"}
          if($value -ceq '~' -or ($value.ToLowerInvariant() -eq 'null' -and $value -cne 'null')){throw "$Context must use lowercase 'null': $Path"}
          if(@('true','false') -contains $value.ToLowerInvariant() -and @('true','false') -cnotcontains $value){throw "$Context must use lowercase Boolean scalars: $Path"}
          if($value -cmatch $script:KnowledgeNumericLikePattern -and $value -cnotmatch $script:KnowledgeCanonicalIntegerPattern){throw "$Context contains noncanonical numeric scalar '$value': $Path"}
          if($value -cmatch $script:KnowledgeTimestampLikePattern){throw "$Context must quote date and timestamp strings: $Path"}
        }
      }
      if($nodeCount -gt $MaxNodes){throw "$Context exceeds the $MaxNodes-node YAML limit: $Path"}
    }
  }catch{throw}
  finally{$reader.Dispose()}
}

function Assert-KnowledgeSchemaVersion {
  param([object]$Mapping,[int]$Expected,[string]$Context,[string]$SourceText)
  $token=Get-KnowledgeYamlSchemaToken $SourceText $Context
  if($token -cnotmatch '^[1-9][0-9]*$'){throw "$Context schema_version must be an unquoted positive integer; found '$token'."}
  $value=$null
  if($Mapping -is [System.Collections.IDictionary] -and $Mapping.Contains('schema_version')){$value=$Mapping['schema_version']}
  elseif($null -ne $Mapping){$property=$Mapping.PSObject.Properties['schema_version'];if($null -ne $property){$value=$property.Value}}
  if($value -isnot [int] -or $value -ne $Expected){throw "Unsupported $Context schema_version '$value'; expected integer $Expected."}
  return [int]$value
}

function ConvertFrom-KnowledgeYamlFile {
  param([string]$Path,[int]$ExpectedSchemaVersion,[string]$Context)
  Import-KnowledgeYamlModule
  $bytes=[System.IO.File]::ReadAllBytes($Path)
  if($bytes.Length -gt $script:KnowledgeMaxYamlBytes){throw "$Context exceeds the $($script:KnowledgeMaxYamlBytes)-byte YAML limit: $Path"}
  if($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF){throw "$Context must not use a UTF-8 BOM: $Path"}
  try{$text=[System.Text.UTF8Encoding]::new($false,$true).GetString($bytes)}catch{throw "$Context must be valid UTF-8: $Path`: $($_.Exception.Message)"}
  Assert-KnowledgeYamlSource $text $Context $Path
  try{$mapping=ConvertFrom-Yaml -Yaml $text -Ordered}catch{throw "Unable to parse $Context $Path`: $($_.Exception.Message)"}
  if($mapping -isnot [System.Collections.IDictionary]){throw "$Context root must be a mapping: $Path"}
  $null=Assert-KnowledgeSchemaVersion $mapping $ExpectedSchemaVersion $Context $text
  return $mapping
}

function Assert-KnowledgeMapKeys {
  param([object]$Mapping,[string[]]$Allowed,[string]$Context)
  if($Mapping -isnot [System.Collections.IDictionary]){throw "$Context must be a mapping."}
  $unknown=@($Mapping.Keys|Where-Object {$Allowed -cnotcontains [string]$_})
  if($unknown.Count -gt 0){throw "$Context contains unsupported field(s): $($unknown -join ', ')."}
}

function Test-KnowledgeRfc3339Timestamp {
  param([string]$Value)
  if($Value -cnotmatch $script:KnowledgeRfc3339Pattern){return $false}
  if($Matches.sign -ceq '-' -and $Matches.hour -ceq '00' -and $Matches.minute -ceq '00'){return $false}
  $timeParts=$Matches.time.Split(':');if([int]$timeParts[0] -gt 23 -or [int]$timeParts[1] -gt 59 -or [int]$timeParts[2] -gt 59){return $false}
  if($Matches.hour){$hour=[int]$Matches.hour;$minute=[int]$Matches.minute;if($minute -gt 59 -or $hour -gt 14 -or ($hour -eq 14 -and $minute -ne 0)){return $false}}
  $parsed=[DateTimeOffset]::MinValue
  return [DateTimeOffset]::TryParse($Value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind,[ref]$parsed)
}
