$script:SupportedLookupKeySchemaVersion = 1
$script:SupportedLookupKeyAlgorithm = "trim-nfc-default-casefold-nfc"
$script:LookupKeyConfigCache = @{}

$script:HangulSBase = 0xAC00
$script:HangulLBase = 0x1100
$script:HangulVBase = 0x1161
$script:HangulTBase = 0x11A7
$script:HangulLCount = 19
$script:HangulVCount = 21
$script:HangulTCount = 28
$script:HangulNCount = $script:HangulVCount * $script:HangulTCount
$script:HangulSCount = $script:HangulLCount * $script:HangulNCount

function Test-KnowledgeJsonInteger {
  param([object]$Value)

  return ($Value -is [sbyte] -or $Value -is [byte] -or $Value -is [int16] -or $Value -is [uint16] -or $Value -is [int32] -or $Value -is [uint32] -or $Value -is [int64] -or $Value -is [uint64])
}

function Assert-KnowledgeJsonObject {
  param([object]$Value, [string]$Context)

  if ($null -eq $Value -or $Value -isnot [System.Management.Automation.PSCustomObject]) {
    throw "Lookup-key registry '$Context' must be a mapping."
  }
}

function ConvertFrom-KnowledgeCodePointSequence {
  param([object]$Value, [string]$Context)

  if ($Value -isnot [System.Array] -or $Value.Count -eq 0) {
    throw "Lookup-key registry '$Context' must be a non-empty code-point list."
  }
  $result = New-Object 'System.Collections.Generic.List[int]'
  for ($index = 0; $index -lt $Value.Count; $index += 1) {
    $item = $Value[$index]
    if (-not (Test-KnowledgeJsonInteger $item)) {
      throw "Lookup-key registry '$Context[$index]' must be an integer."
    }
    Assert-KnowledgeUnicodeScalar ([int]$item) "$Context[$index]"
    $result.Add([int]$item)
  }
  return @($result)
}

function Assert-KnowledgeUnicodeScalar {
  param([int]$CodePoint, [string]$Context)

  if ($CodePoint -lt 0 -or $CodePoint -gt 0x10FFFF -or ($CodePoint -ge 0xD800 -and $CodePoint -le 0xDFFF)) {
    throw "Lookup-key registry '$Context' is not a Unicode scalar value."
  }
}

function ConvertFrom-KnowledgeHexCodePoint {
  param([string]$Value, [string]$Context)

  try {
    $codePoint = [Convert]::ToInt32($Value, 16)
  } catch {
    throw "Lookup-key registry '$Context' must be a hexadecimal code point."
  }
  Assert-KnowledgeUnicodeScalar $codePoint $Context
  return $codePoint
}

function ConvertTo-KnowledgeCodePoints {
  param([string]$Value)

  $result = New-Object 'System.Collections.Generic.List[int]'
  for ($index = 0; $index -lt $Value.Length; $index += 1) {
    $current = [int]$Value[$index]
    if ([char]::IsHighSurrogate($Value[$index])) {
      if ($index + 1 -ge $Value.Length -or -not [char]::IsLowSurrogate($Value[$index + 1])) {
        throw "Lookup-key input contains an unpaired high surrogate."
      }
      $result.Add([char]::ConvertToUtf32($Value[$index], $Value[$index + 1]))
      $index += 1
    } elseif ([char]::IsLowSurrogate($Value[$index])) {
      throw "Lookup-key input contains an unpaired low surrogate."
    } else {
      $result.Add($current)
    }
  }
  return @($result)
}

function Add-KnowledgeCanonicalDecomposition {
  param(
    [int]$CodePoint,
    [object]$LookupKeyConfig,
    [System.Collections.Generic.List[int]]$Output
  )

  $hangulIndex = $CodePoint - $script:HangulSBase
  if ($hangulIndex -ge 0 -and $hangulIndex -lt $script:HangulSCount) {
    $Output.Add($script:HangulLBase + [Math]::Floor($hangulIndex / $script:HangulNCount))
    $Output.Add($script:HangulVBase + [Math]::Floor(($hangulIndex % $script:HangulNCount) / $script:HangulTCount))
    $trailingIndex = $hangulIndex % $script:HangulTCount
    if ($trailingIndex -ne 0) { $Output.Add($script:HangulTBase + $trailingIndex) }
    return
  }
  if (-not $LookupKeyConfig.canonical_decomposition.ContainsKey($CodePoint)) {
    $Output.Add($CodePoint)
    return
  }
  foreach ($item in @($LookupKeyConfig.canonical_decomposition[$CodePoint])) {
    Add-KnowledgeCanonicalDecomposition ([int]$item) $LookupKeyConfig $Output
  }
}

function Get-KnowledgeCombiningClass {
  param([int]$CodePoint, [object]$LookupKeyConfig)

  if ($LookupKeyConfig.canonical_combining_class.ContainsKey($CodePoint)) {
    return [int]$LookupKeyConfig.canonical_combining_class[$CodePoint]
  }
  return 0
}

function Get-KnowledgeCanonicalComposition {
  param([int]$First, [int]$Second, [object]$LookupKeyConfig)

  $leadingIndex = $First - $script:HangulLBase
  if ($leadingIndex -ge 0 -and $leadingIndex -lt $script:HangulLCount) {
    $vowelIndex = $Second - $script:HangulVBase
    if ($vowelIndex -ge 0 -and $vowelIndex -lt $script:HangulVCount) {
      return $script:HangulSBase + (($leadingIndex * $script:HangulVCount + $vowelIndex) * $script:HangulTCount)
    }
  }
  $syllableIndex = $First - $script:HangulSBase
  if ($syllableIndex -ge 0 -and $syllableIndex -lt $script:HangulSCount -and $syllableIndex % $script:HangulTCount -eq 0) {
    $trailingIndex = $Second - $script:HangulTBase
    if ($trailingIndex -gt 0 -and $trailingIndex -lt $script:HangulTCount) {
      return $First + $trailingIndex
    }
  }
  $key = "{0:X}+{1:X}" -f $First, $Second
  if ($LookupKeyConfig.canonical_composition.ContainsKey($key)) {
    return [int]$LookupKeyConfig.canonical_composition[$key]
  }
  return $null
}

function ConvertTo-KnowledgeNfcCodePoints {
  param([int[]]$CodePoints, [object]$LookupKeyConfig)

  $decomposed = New-Object 'System.Collections.Generic.List[int]'
  foreach ($codePoint in @($CodePoints)) {
    Add-KnowledgeCanonicalDecomposition $codePoint $LookupKeyConfig $decomposed
  }
  for ($index = 1; $index -lt $decomposed.Count; $index += 1) {
    $combiningClass = Get-KnowledgeCombiningClass $decomposed[$index] $LookupKeyConfig
    if ($combiningClass -eq 0) { continue }
    $cursor = $index
    while ($cursor -gt 0) {
      $previousClass = Get-KnowledgeCombiningClass $decomposed[$cursor - 1] $LookupKeyConfig
      if ($previousClass -eq 0 -or $previousClass -le $combiningClass) { break }
      $temporary = $decomposed[$cursor - 1]
      $decomposed[$cursor - 1] = $decomposed[$cursor]
      $decomposed[$cursor] = $temporary
      $cursor -= 1
    }
  }
  if ($decomposed.Count -eq 0) { return @() }

  $result = New-Object 'System.Collections.Generic.List[int]'
  $result.Add($decomposed[0])
  $starterPosition = 0
  $starter = $decomposed[0]
  $lastCombiningClass = 0
  for ($index = 1; $index -lt $decomposed.Count; $index += 1) {
    $codePoint = $decomposed[$index]
    $combiningClass = Get-KnowledgeCombiningClass $codePoint $LookupKeyConfig
    $composite = Get-KnowledgeCanonicalComposition $starter $codePoint $LookupKeyConfig
    if ($null -ne $composite -and ($lastCombiningClass -eq 0 -or $lastCombiningClass -lt $combiningClass)) {
      $result[$starterPosition] = $composite
      $starter = $composite
      continue
    }
    if ($combiningClass -eq 0) {
      $starterPosition = $result.Count
      $starter = $codePoint
    }
    $result.Add($codePoint)
    $lastCombiningClass = $combiningClass
  }
  return @($result)
}

function ConvertTo-KnowledgeLookupKey {
  param([string]$Value, [object]$LookupKeyConfig)

  if ($null -eq $Value) { throw "Lookup-key input must be a string." }
  $codePoints = @(ConvertTo-KnowledgeCodePoints $Value)
  $start = 0
  $end = $codePoints.Count
  while ($start -lt $end -and $LookupKeyConfig.trim_codepoints.Contains([int]$codePoints[$start])) { $start += 1 }
  while ($end -gt $start -and $LookupKeyConfig.trim_codepoints.Contains([int]$codePoints[$end - 1])) { $end -= 1 }
  if ($end -le $start) { return ,([string]::Empty) }
  $trimmed = if ($end -gt $start) { @($codePoints[$start..($end - 1)]) } else { @() }
  $normalized = @(ConvertTo-KnowledgeNfcCodePoints $trimmed $LookupKeyConfig)
  $folded = New-Object 'System.Collections.Generic.List[int]'
  foreach ($codePoint in $normalized) {
    if ($LookupKeyConfig.case_folding.ContainsKey([int]$codePoint)) {
      foreach ($item in @($LookupKeyConfig.case_folding[[int]$codePoint])) { $folded.Add([int]$item) }
    } else {
      $folded.Add([int]$codePoint)
    }
  }
  if ($folded.Count -eq 0) { return ,([string]::Empty) }
  $final = @(ConvertTo-KnowledgeNfcCodePoints @($folded) $LookupKeyConfig)
  $builder = New-Object System.Text.StringBuilder
  foreach ($codePoint in $final) { [void]$builder.Append([char]::ConvertFromUtf32($codePoint)) }
  return ,$builder.ToString()
}

function Get-KnowledgeLookupKeyConfig {
  param([object]$ProjectConfig)

  $path = [System.IO.Path]::GetFullPath($ProjectConfig.lookup_keys_registry)
  if ($script:LookupKeyConfigCache.ContainsKey($path)) {
    return $script:LookupKeyConfigCache[$path]
  }
  try {
    $registry = ConvertFrom-Json -InputObject ([System.IO.File]::ReadAllText($path, [System.Text.Encoding]::ASCII))
  } catch {
    throw "Unable to parse lookup-key registry $path`: $($_.Exception.Message)"
  }
  Assert-KnowledgeJsonObject $registry "root"
  if (-not (Test-KnowledgeJsonInteger $registry.schema_version) -or [int]$registry.schema_version -ne $script:SupportedLookupKeySchemaVersion) {
    throw "Unsupported lookup-key schema_version '$($registry.schema_version)'; expected $script:SupportedLookupKeySchemaVersion."
  }
  if ([string]$registry.algorithm -ne $script:SupportedLookupKeyAlgorithm) {
    throw "Unsupported lookup-key algorithm '$($registry.algorithm)'; expected '$script:SupportedLookupKeyAlgorithm'."
  }
  if ([string]::IsNullOrWhiteSpace([string]$registry.unicode_version)) {
    throw "Lookup-key registry 'unicode_version' must be a non-empty string."
  }

  if ($registry.trim_codepoints -isnot [System.Array]) {
    throw "Lookup-key registry 'trim_codepoints' must be a code-point list."
  }
  $trimCodePoints = New-Object 'System.Collections.Generic.HashSet[int]'
  foreach ($item in @($registry.trim_codepoints)) {
    if (-not (Test-KnowledgeJsonInteger $item)) { throw "Lookup-key registry 'trim_codepoints' values must be integers." }
    Assert-KnowledgeUnicodeScalar ([int]$item) "trim_codepoints"
    [void]$trimCodePoints.Add([int]$item)
  }
  Assert-KnowledgeJsonObject $registry.case_folding "case_folding"
  $caseFolding = @{}
  foreach ($property in $registry.case_folding.PSObject.Properties) {
    $source = ConvertFrom-KnowledgeHexCodePoint $property.Name "case_folding.$($property.Name)"
    $caseFolding[$source] = @(ConvertFrom-KnowledgeCodePointSequence $property.Value "case_folding.$($property.Name)")
  }
  Assert-KnowledgeJsonObject $registry.canonical_decomposition "canonical_decomposition"
  $decomposition = @{}
  foreach ($property in $registry.canonical_decomposition.PSObject.Properties) {
    $source = ConvertFrom-KnowledgeHexCodePoint $property.Name "canonical_decomposition.$($property.Name)"
    $decomposition[$source] = @(ConvertFrom-KnowledgeCodePointSequence $property.Value "canonical_decomposition.$($property.Name)")
  }
  Assert-KnowledgeJsonObject $registry.canonical_combining_class "canonical_combining_class"
  $combiningClasses = @{}
  foreach ($property in $registry.canonical_combining_class.PSObject.Properties) {
    $source = ConvertFrom-KnowledgeHexCodePoint $property.Name "canonical_combining_class.$($property.Name)"
    if (-not (Test-KnowledgeJsonInteger $property.Value)) { throw "Lookup-key registry canonical combining classes must be integers from 1 through 255." }
    $value = [int]$property.Value
    if ($value -le 0 -or $value -gt 255) { throw "Lookup-key registry combining classes must be integers from 1 through 255." }
    $combiningClasses[$source] = $value
  }
  Assert-KnowledgeJsonObject $registry.canonical_composition "canonical_composition"
  $composition = @{}
  foreach ($property in $registry.canonical_composition.PSObject.Properties) {
    $parts = $property.Name.Split("+")
    if ($parts.Count -ne 2) { throw "Lookup-key registry composition key '$($property.Name)' must contain two code points." }
    $first = ConvertFrom-KnowledgeHexCodePoint $parts[0] "canonical_composition.$($property.Name)"
    $second = ConvertFrom-KnowledgeHexCodePoint $parts[1] "canonical_composition.$($property.Name)"
    if (-not (Test-KnowledgeJsonInteger $property.Value)) { throw "Lookup-key registry composition '$($property.Name)' must target an integer code point." }
    Assert-KnowledgeUnicodeScalar ([int]$property.Value) "canonical_composition.$($property.Name)"
    $composition[("{0:X}+{1:X}" -f $first, $second)] = [int]$property.Value
  }
  $config = [pscustomobject]@{
    path = $path
    schema_version = [int]$registry.schema_version
    unicode_version = [string]$registry.unicode_version
    algorithm = [string]$registry.algorithm
    trim_codepoints = $trimCodePoints
    case_folding = $caseFolding
    canonical_decomposition = $decomposition
    canonical_combining_class = $combiningClasses
    canonical_composition = $composition
  }
  $actualCounts = [ordered]@{
    case_folding = $caseFolding.Count
    canonical_decomposition = $decomposition.Count
    canonical_combining_class = $combiningClasses.Count
    canonical_composition = $composition.Count
  }
  Assert-KnowledgeJsonObject $registry.counts "counts"
  if (@($registry.counts.PSObject.Properties).Count -ne $actualCounts.Count) {
    throw "Lookup-key registry declared counts do not match its mapping data."
  }
  foreach ($key in $actualCounts.Keys) {
    $declaredCount = $registry.counts.$key
    if (-not (Test-KnowledgeJsonInteger $declaredCount) -or [int]$declaredCount -ne $actualCounts[$key]) {
      throw "Lookup-key registry declared counts do not match its mapping data."
    }
  }
  $script:LookupKeyConfigCache[$path] = $config
  return $config
}
