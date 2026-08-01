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
  Assert-KnowledgeMapKeys $Raw @("kind","value","precision","certainty","inclusive") $Context
  $kind=Get-RequiredKnowledgeTemporalString $Raw "kind" $Context
  Assert-KnowledgeTemporalPackValue $SchemaPacks "temporal.bound-kind" $kind "$Context.kind"
  if($kind -eq "unknown"){
    $extra=@($Raw.Keys|Where-Object {$_ -cne "kind"})
    if($extra.Count -gt 0){throw "$Context unknown bounds cannot declare: $($extra -join ', ')."}
    return [pscustomobject]@{kind=$kind;value=$null;precision=$null;certainty=$null;inclusive=$null}
  }
  if($kind -ne "known"){throw "$Context.kind uses unsupported temporal behavior '$kind'."}
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
  return [pscustomobject]@{kind=$kind;value=$value;precision=$precision;certainty=$certainty;inclusive=[bool]$inclusive}
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
  if($kind -notin @("interval","unknown")){throw "$windowContext.kind uses unsupported temporal behavior '$kind'."}
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
  if($Bound.kind -ne "known" -or $null -eq $Bound.value -or $null -eq $Bound.precision){throw "Unknown temporal bounds do not have a comparable range."}
  $maximum=[datetime]::new(9999,12,31,23,59,59).AddTicks(9999990)
  switch($Bound.precision){
    "year"{$start=[datetime]::new([int]$Bound.value,1,1);$end=if($start.Year -eq 9999){$maximum}else{$start.AddYears(1).AddTicks(-10)}}
    "month"{$start=[datetime]::ParseExact($Bound.value,"yyyy-MM",[Globalization.CultureInfo]::InvariantCulture);$end=if($start.Year -eq 9999 -and $start.Month -eq 12){$maximum}else{$start.AddMonths(1).AddTicks(-10)}}
    "date"{$start=[datetime]::ParseExact($Bound.value,"yyyy-MM-dd",[Globalization.CultureInfo]::InvariantCulture);$end=if($start.Date -eq [datetime]::MaxValue.Date){$maximum}else{$start.AddDays(1).AddTicks(-10)}}
    default{$start=[datetimeoffset]::Parse($Bound.value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).UtcDateTime;$end=$start}
  }
  return [pscustomobject]@{lower=$start;upper=$end}
}

function Get-KnowledgeTemporalWindowLimits {
  param([object]$Window)
  if($Window.kind -eq "unknown"){return [pscustomobject]@{lower=$null;upper=$null}}
  $lower=$null;$upper=$null
  if($null -ne $Window.start -and $Window.start.kind -eq "known"){$range=Get-KnowledgeTemporalBoundRange $Window.start;$lower=[pscustomobject]@{instant=if($Window.start.inclusive){$range.lower}else{$range.upper};inclusive=[bool]$Window.start.inclusive}}
  if($null -ne $Window.end -and $Window.end.kind -eq "known"){$range=Get-KnowledgeTemporalBoundRange $Window.end;$upper=[pscustomobject]@{instant=if($Window.end.inclusive){$range.upper}else{$range.lower};inclusive=[bool]$Window.end.inclusive}}
  return [pscustomobject]@{lower=$lower;upper=$upper}
}

function Test-KnowledgeTemporalWindowUnknownBound {
  param([object]$Window)
  return ($null -ne $Window.start -and $Window.start.kind -eq "unknown") -or ($null -ne $Window.end -and $Window.end.kind -eq "unknown")
}

function Get-KnowledgeTemporalIndeterminateReason {
  param([object]$Window)
  $rank=@{announced=1;approximate=2;uncertain=3};$winner=$null;$winnerRank=0
  foreach($bound in @($Window.start,$Window.end)){
    if($null -ne $bound -and $bound.kind -eq "known" -and $rank.ContainsKey([string]$bound.certainty) -and $rank[[string]$bound.certainty] -gt $winnerRank){$winner=[string]$bound.certainty;$winnerRank=$rank[$winner]}
  }
  if($null -eq $winner){return $null}
  return "indeterminate-$winner"
}

function Get-KnowledgeTemporalOverlap {
  param([object]$Left,[object]$Right)
  if($null -eq $Left -or $null -eq $Right){return "overlap"}
  if($Left.kind -eq "unknown" -or $Right.kind -eq "unknown"){return "unknown"}
  $l=Get-KnowledgeTemporalWindowLimits $Left;$r=Get-KnowledgeTemporalWindowLimits $Right
  function Test-Before($Upper,$Lower){if($null -eq $Upper -or $null -eq $Lower){return $false};return $Upper.instant -lt $Lower.instant -or ($Upper.instant -eq $Lower.instant -and -not ($Upper.inclusive -and $Lower.inclusive))}
  $reasons=@((Get-KnowledgeTemporalIndeterminateReason $Left),(Get-KnowledgeTemporalIndeterminateReason $Right))|Where-Object {$null -ne $_}
  $hasUnknown=(Test-KnowledgeTemporalWindowUnknownBound $Left) -or (Test-KnowledgeTemporalWindowUnknownBound $Right)
  if($hasUnknown){if($reasons.Count -gt 0){return "unknown"};if((Test-Before $l.upper $r.lower) -or (Test-Before $r.upper $l.lower)){return "disjoint"};return "unknown"}
  if($reasons.Count -gt 0){$rank=@{"indeterminate-announced"=1;"indeterminate-approximate"=2;"indeterminate-uncertain"=3};return @($reasons|Sort-Object {$rank[$_]} -Descending)[0]}
  if((Test-Before $l.upper $r.lower) -or (Test-Before $r.upper $l.lower)){return "disjoint"}
  return "overlap"
}

function Test-KnowledgeTemporalWindowsOverlap {
  param([object]$Left,[object]$Right)
  return (Get-KnowledgeTemporalOverlap $Left $Right) -ne "disjoint"
}

function Test-KnowledgeTemporalMatchIndeterminate {
  param([string]$Value)
  return $Value -eq "unknown" -or $Value.StartsWith("indeterminate-",[System.StringComparison]::Ordinal)
}

function ConvertTo-KnowledgeTemporalInstant {
  param([object]$Value)
  if($null -eq $Value){return $null}
  if($Value -is [datetimeoffset]){if($Value.Ticks % 10 -ne 0){throw "Effective datetime objects cannot exceed microsecond precision."};$instant=$Value.UtcDateTime;return [pscustomobject]@{value=$Value.ToString("o");precision="datetime";lower=$instant;upper=$instant;label=$Value.ToString("o")}}
  if($Value -is [datetime]){if($Value.Ticks % 10 -ne 0){throw "Effective datetime objects cannot exceed microsecond precision."};$instant=if($Value.Kind -eq [DateTimeKind]::Local){$Value.ToUniversalTime()}elseif($Value.Kind -eq [DateTimeKind]::Utc){$Value}else{[datetime]::SpecifyKind($Value,[DateTimeKind]::Unspecified)};return [pscustomobject]@{value=$Value.ToString("o");precision="datetime";lower=$instant;upper=$instant;label=$Value.ToString("o")}}
  if($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value)){throw "Effective time must be an ISO year, month, date, RFC 3339 datetime, or null."}
  $label=$Value.Trim()
  $precision=if($label -cmatch '^\d{4}$'){"year"}elseif($label -cmatch '^\d{4}-\d{2}$'){"month"}elseif($label -cmatch '^\d{4}-\d{2}-\d{2}$'){"date"}else{$null}
  if($null -ne $precision){
    try{$range=Get-KnowledgeTemporalBoundRange ([pscustomobject]@{kind="known";value=$label;precision=$precision;certainty="exact";inclusive=$true})}catch{throw "Effective time must be an ISO year, month, date, or RFC 3339 datetime."}
    return [pscustomobject]@{value=$label;precision=$precision;lower=$range.lower;upper=$range.upper;label=$label}
  }
  if(-not (Test-KnowledgeRfc3339Timestamp $label)){throw "Effective time must be an ISO year, month, date, or RFC 3339 datetime."}
  $instant=[datetimeoffset]::Parse($label,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).UtcDateTime
  return [pscustomobject]@{value=$label;precision="datetime";lower=$instant;upper=$instant;label=$label}
}

function Get-KnowledgeTemporalMatch {
  param([object]$Window,[object]$Query)
  if($null -eq $Window){return "unbounded"}
  if($Window.kind -eq "unknown"){return "unknown"}
  if($null -eq $Query){return $null}
  $limits=Get-KnowledgeTemporalWindowLimits $Window
  $hasUnknown=Test-KnowledgeTemporalWindowUnknownBound $Window;$reason=Get-KnowledgeTemporalIndeterminateReason $Window
  if($hasUnknown -and $null -ne $reason){return "unknown"}
  if(-not $hasUnknown -and $null -ne $reason){return $reason}
  if($null -ne $limits.upper -and ($limits.upper.instant -lt $Query.lower -or ($limits.upper.instant -eq $Query.lower -and -not $limits.upper.inclusive))){return $null}
  if($null -ne $limits.lower -and ($limits.lower.instant -gt $Query.upper -or ($limits.lower.instant -eq $Query.upper -and -not $limits.lower.inclusive))){return $null}
  if($hasUnknown){return "unknown"}
  $lowerContains=$null -eq $limits.lower -or $Query.lower -gt $limits.lower.instant -or ($Query.lower -eq $limits.lower.instant -and $limits.lower.inclusive)
  $upperContains=$null -eq $limits.upper -or $Query.upper -lt $limits.upper.instant -or ($Query.upper -eq $limits.upper.instant -and $limits.upper.inclusive)
  if(-not ($lowerContains -and $upperContains)){return "indeterminate-partial"}
  return "effective"
}
