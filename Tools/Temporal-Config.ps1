$projectConfigHelper = Join-Path $PSScriptRoot "Project-Config.ps1"
if (-not (Get-Command Get-ProjectMapValue -ErrorAction SilentlyContinue)) { . $projectConfigHelper }
$schemaPackConfigHelper = Join-Path $PSScriptRoot "Schema-Pack-Config.ps1"
if (-not (Get-Command Get-SchemaPackAllowedValues -ErrorAction SilentlyContinue)) { . $schemaPackConfigHelper }

function Get-RequiredKnowledgeTemporalString {
  param([object]$Map,[string]$Key,[string]$Context)
  $value=Get-ProjectMapValue $Map $Key
  if($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)){throw "$Context.$Key must be a non-empty string."}
  return $value.Trim()
}

function Assert-KnowledgeTemporalPackValue {
  param([object]$SchemaPacks,[string]$Namespace,[string]$Value,[string]$Context)
  $allowed=@(Get-SchemaPackAllowedValues $SchemaPacks $Namespace)
  if($allowed.Count -eq 0){throw "Selected schema packs do not provide temporal namespace '$Namespace' required by '$Context'."}
  if($allowed -cnotcontains $Value){throw "$Context uses '$Value', which is not provided in '$Namespace'."}
}

function ConvertTo-KnowledgeTemporalBound {
  param([object]$Raw,[string]$Context,[object]$SchemaPacks)
  if($Raw -isnot [System.Collections.IDictionary]){throw "$Context must be a mapping."}
  Assert-KnowledgeMapKeys $Raw @("value","precision","certainty","inclusive") $Context
  $value=Get-RequiredKnowledgeTemporalString $Raw "value" $Context
  $precision=Get-RequiredKnowledgeTemporalString $Raw "precision" $Context
  $certainty=Get-RequiredKnowledgeTemporalString $Raw "certainty" $Context
  $inclusive=Get-ProjectMapValue $Raw "inclusive"
  if($inclusive -isnot [bool]){throw "$Context.inclusive must be true or false."}
  Assert-KnowledgeTemporalPackValue $SchemaPacks "temporal.precision" $precision "$Context.precision"
  Assert-KnowledgeTemporalPackValue $SchemaPacks "temporal.certainty" $certainty "$Context.certainty"
  $valid=$false
  switch($precision){
    "year"{$parsed=[datetime]::MinValue;$valid=$value -cmatch '^\d{4}$' -and [datetime]::TryParseExact("$value-01-01","yyyy-MM-dd",[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$parsed)}
    "month"{$parsed=[datetime]::MinValue;$valid=[datetime]::TryParseExact($value,"yyyy-MM",[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$parsed)}
    "date"{$parsed=[datetime]::MinValue;$valid=[datetime]::TryParseExact($value,"yyyy-MM-dd",[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$parsed)}
    "datetime"{$valid=Test-KnowledgeRfc3339Timestamp $value}
  }
  if(-not $valid){throw "$Context.value does not match temporal precision '$precision': $value"}
  return [pscustomobject]@{value=$value;precision=$precision;certainty=$certainty;inclusive=[bool]$inclusive}
}

function ConvertTo-KnowledgeTemporalWindow {
  param([object]$Map,[string]$Key,[string]$Context,[object]$SchemaPacks)
  $raw=Get-ProjectMapValue $Map $Key
  if($null -eq $raw){return $null}
  $windowContext="$Context.$Key"
  if($raw -isnot [System.Collections.IDictionary]){throw "$windowContext must be a mapping."}
  Assert-KnowledgeMapKeys $raw @("kind","start","end") $windowContext
  $kind=Get-RequiredKnowledgeTemporalString $raw "kind" $windowContext
  Assert-KnowledgeTemporalPackValue $SchemaPacks "temporal.window-kind" $kind "$windowContext.kind"
  $start=if($raw.Contains("start")){ConvertTo-KnowledgeTemporalBound (Get-ProjectMapValue $raw "start") "$windowContext.start" $SchemaPacks}else{$null}
  $end=if($raw.Contains("end")){ConvertTo-KnowledgeTemporalBound (Get-ProjectMapValue $raw "end") "$windowContext.end" $SchemaPacks}else{$null}
  if($kind -eq "unknown"){
    if($null -ne $start -or $null -ne $end){throw "$windowContext unknown windows cannot declare bounds."}
    return [pscustomobject]@{kind=$kind;start=$null;end=$null}
  }
  if($null -eq $start -and $null -eq $end){throw "$windowContext interval windows require at least one bound."}
  $result=[pscustomobject]@{kind=$kind;start=$start;end=$end}
  $limits=Get-KnowledgeTemporalWindowLimits $result
  if($null -ne $limits.lower -and $null -ne $limits.upper){
    if($limits.lower.instant -gt $limits.upper.instant -or ($limits.lower.instant -eq $limits.upper.instant -and -not ($limits.lower.inclusive -and $limits.upper.inclusive))){throw "$windowContext has an empty or reversed interval."}
  }
  return $result
}

function Get-KnowledgeTemporalBoundRange {
  param([object]$Bound)
  switch($Bound.precision){
    "year"{$start=[datetime]::new([int]$Bound.value,1,1);$end=$start.AddYears(1).AddTicks(-1)}
    "month"{$start=[datetime]::ParseExact($Bound.value,"yyyy-MM",[Globalization.CultureInfo]::InvariantCulture);$end=$start.AddMonths(1).AddTicks(-1)}
    "date"{$start=[datetime]::ParseExact($Bound.value,"yyyy-MM-dd",[Globalization.CultureInfo]::InvariantCulture);$end=$start.AddDays(1).AddTicks(-1)}
    default{$start=[datetimeoffset]::Parse($Bound.value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).UtcDateTime;$end=$start}
  }
  return [pscustomobject]@{lower=$start;upper=$end}
}

function Get-KnowledgeTemporalWindowLimits {
  param([object]$Window)
  if($Window.kind -eq "unknown"){return [pscustomobject]@{lower=$null;upper=$null}}
  $lower=$null;$upper=$null
  if($null -ne $Window.start){$range=Get-KnowledgeTemporalBoundRange $Window.start;$lower=[pscustomobject]@{instant=if($Window.start.inclusive){$range.lower}else{$range.upper};inclusive=[bool]$Window.start.inclusive}}
  if($null -ne $Window.end){$range=Get-KnowledgeTemporalBoundRange $Window.end;$upper=[pscustomobject]@{instant=if($Window.end.inclusive){$range.upper}else{$range.lower};inclusive=[bool]$Window.end.inclusive}}
  return [pscustomobject]@{lower=$lower;upper=$upper}
}

function Test-KnowledgeTemporalWindowUncertain {
  param([object]$Window)
  return ($null -ne $Window.start -and $Window.start.certainty -ne "exact") -or ($null -ne $Window.end -and $Window.end.certainty -ne "exact")
}

function Get-KnowledgeTemporalOverlap {
  param([object]$Left,[object]$Right)
  if($null -eq $Left -or $null -eq $Right){return "overlap"}
  if($Left.kind -eq "unknown" -or $Right.kind -eq "unknown"){return "unknown"}
  if((Test-KnowledgeTemporalWindowUncertain $Left) -or (Test-KnowledgeTemporalWindowUncertain $Right)){return "indeterminate"}
  $l=Get-KnowledgeTemporalWindowLimits $Left;$r=Get-KnowledgeTemporalWindowLimits $Right
  function Test-Before($Upper,$Lower){if($null -eq $Upper -or $null -eq $Lower){return $false};return $Upper.instant -lt $Lower.instant -or ($Upper.instant -eq $Lower.instant -and -not ($Upper.inclusive -and $Lower.inclusive))}
  if((Test-Before $l.upper $r.lower) -or (Test-Before $r.upper $l.lower)){return "disjoint"}
  return "overlap"
}

function Test-KnowledgeTemporalWindowsOverlap {
  param([object]$Left,[object]$Right)
  return (Get-KnowledgeTemporalOverlap $Left $Right) -ne "disjoint"
}

function ConvertTo-KnowledgeTemporalInstant {
  param([object]$Value)
  if($null -eq $Value){return $null}
  if($Value -is [datetimeoffset]){return [pscustomobject]@{instant=$Value.UtcDateTime;label=$Value.ToString("o")}}
  if($Value -is [datetime]){$instant=if($Value.Kind -eq [DateTimeKind]::Local){$Value.ToUniversalTime()}elseif($Value.Kind -eq [DateTimeKind]::Utc){$Value}else{[datetime]::SpecifyKind($Value,[DateTimeKind]::Unspecified)};return [pscustomobject]@{instant=$instant;label=$Value.ToString("o")}}
  if($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value)){throw "Effective time must be an ISO date, RFC 3339 datetime, or null."}
  $label=$Value.Trim()
  if($label -cmatch '^\d{4}-\d{2}-\d{2}$'){$parsed=[datetime]::MinValue;if(-not [datetime]::TryParseExact($label,"yyyy-MM-dd",[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$parsed)){throw "Effective time must be an ISO date or RFC 3339 datetime."};return [pscustomobject]@{instant=$parsed;label=$label}}
  if(-not (Test-KnowledgeRfc3339Timestamp $label)){throw "Effective time must be an ISO date or RFC 3339 datetime."}
  return [pscustomobject]@{instant=[datetimeoffset]::Parse($label,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).UtcDateTime;label=$label}
}

function Get-KnowledgeTemporalMatch {
  param([object]$Window,[object]$EffectiveInstant)
  if($null -eq $Window){return "unbounded"}
  if($Window.kind -eq "unknown"){return "unknown"}
  if($null -eq $EffectiveInstant){return $null}
  if(Test-KnowledgeTemporalWindowUncertain $Window){return "indeterminate"}
  $limits=Get-KnowledgeTemporalWindowLimits $Window
  if($null -ne $limits.lower -and ($EffectiveInstant -lt $limits.lower.instant -or ($EffectiveInstant -eq $limits.lower.instant -and -not $limits.lower.inclusive))){return $null}
  if($null -ne $limits.upper -and ($EffectiveInstant -gt $limits.upper.instant -or ($EffectiveInstant -eq $limits.upper.instant -and -not $limits.upper.inclusive))){return $null}
  return "effective"
}
