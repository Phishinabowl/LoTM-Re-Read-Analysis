$script:KnowledgeRfc3339Pattern = "^(?<date>\d{4}-\d{2}-\d{2})T(?<time>\d{2}:\d{2}:\d{2})(?:\.\d+)?(?<zone>Z|(?<sign>[+-])(?<hour>\d{2}):(?<minute>\d{2}))$"

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
  $text=[System.IO.File]::ReadAllText($Path,[System.Text.UTF8Encoding]::new($true))
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
  if($Matches.hour){$hour=[int]$Matches.hour;$minute=[int]$Matches.minute;if($hour -gt 14 -or ($hour -eq 14 -and $minute -ne 0)){return $false}}
  $parsed=[DateTimeOffset]::MinValue
  return [DateTimeOffset]::TryParse($Value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind,[ref]$parsed)
}
