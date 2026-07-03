param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,
  [string[]]$OutputPath,
  [string]$SettingsPath = "Visualization/config/render-settings.json"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

function Resolve-RepoPath {
  param([string]$Path)

  if ([System.IO.Path]::IsPathRooted($Path)) {
    return $Path
  }

  return (Join-Path $repoRoot $Path)
}

function Get-MermaidRenderSize {
  param(
    [string]$GraphPath,
    [object]$Settings
  )

  $width = [int]$Settings.width
  $height = [int]$Settings.height

  if ($null -eq $Settings.autoSize -or -not [bool]$Settings.autoSize.enabled) {
    return [pscustomobject]@{
      Width = $width
      Height = $height
      NodeCount = 0
      EdgeCount = 0
      Complexity = 0
      ScaleSteps = 0
      MaxFanOut = 0
      FanOutSteps = 0
    }
  }

  $nodeIds = New-Object 'System.Collections.Generic.HashSet[string]'
  $edgeCount = 0
  $outgoingCounts = @{}
  $incomingCounts = @{}

  foreach ($line in Get-Content $GraphPath) {
    foreach ($match in [regex]::Matches($line, '(^|[\s])([A-Za-z0-9_]+)\s*(?:\["|\(|\{|\>)')) {
      [void]$nodeIds.Add($match.Groups[2].Value)
    }

    if ($line -match '\s-->|--\>|-.->|==>') {
      $edgeCount += 1
    }

    $edgeMatch = [regex]::Match($line, '^\s*([A-Za-z0-9_]+)\s*(?:-->|--\>|-.->|==>)\s*(?:\|[^|]*\|\s*)?([A-Za-z0-9_]+)')
    if ($edgeMatch.Success) {
      $source = $edgeMatch.Groups[1].Value
      $target = $edgeMatch.Groups[2].Value
      [void]$nodeIds.Add($source)
      [void]$nodeIds.Add($target)

      if (-not $outgoingCounts.ContainsKey($source)) {
        $outgoingCounts[$source] = 0
      }
      if (-not $incomingCounts.ContainsKey($target)) {
        $incomingCounts[$target] = 0
      }
      $outgoingCounts[$source] += 1
      $incomingCounts[$target] += 1
    }
  }

  $nodeCount = $nodeIds.Count
  $complexity = $nodeCount + $edgeCount
  $unit = if ($Settings.autoSize.complexityUnit) { [double]$Settings.autoSize.complexityUnit } else { 40.0 }
  $scaleSteps = [Math]::Max(0, [Math]::Ceiling([Math]::Sqrt($complexity / $unit)) - 1)

  $widthStep = if ($Settings.autoSize.widthStep) { [int]$Settings.autoSize.widthStep } else { 1200 }
  $heightStep = if ($Settings.autoSize.heightStep) { [int]$Settings.autoSize.heightStep } else { 600 }
  $maxWidth = if ($Settings.autoSize.maxWidth) { [int]$Settings.autoSize.maxWidth } else { $width }
  $maxHeight = if ($Settings.autoSize.maxHeight) { [int]$Settings.autoSize.maxHeight } else { $height }
  $fanOutThreshold = if ($Settings.autoSize.fanOutThreshold) { [int]$Settings.autoSize.fanOutThreshold } else { 6 }
  $fanOutWidthStep = if ($Settings.autoSize.fanOutWidthStep) { [int]$Settings.autoSize.fanOutWidthStep } else { 900 }

  $maxOutgoing = 0
  $maxIncoming = 0
  foreach ($count in $outgoingCounts.Values) {
    $maxOutgoing = [Math]::Max($maxOutgoing, [int]$count)
  }
  foreach ($count in $incomingCounts.Values) {
    $maxIncoming = [Math]::Max($maxIncoming, [int]$count)
  }
  $maxFanOut = [Math]::Max($maxOutgoing, $maxIncoming)
  $fanOutSteps = if ($fanOutThreshold -gt 0) {
    [Math]::Max(0, [Math]::Ceiling(($maxFanOut - $fanOutThreshold) / [double]$fanOutThreshold))
  } else {
    0
  }

  $width = [Math]::Min($maxWidth, $width + ($scaleSteps * $widthStep) + ($fanOutSteps * $fanOutWidthStep))
  $height = [Math]::Min($maxHeight, $height + ($scaleSteps * $heightStep))

  return [pscustomobject]@{
    Width = [int]$width
    Height = [int]$height
    NodeCount = $nodeCount
    EdgeCount = $edgeCount
    Complexity = $complexity
    ScaleSteps = [int]$scaleSteps
    MaxFanOut = [int]$maxFanOut
    FanOutSteps = [int]$fanOutSteps
  }
}

function Get-MermaidClassValidation {
  param(
    [string]$GraphPath,
    [object]$Settings
  )

  $declaredNodes = New-Object 'System.Collections.Generic.HashSet[string]'
  $usedNodes = New-Object 'System.Collections.Generic.HashSet[string]'
  $classAssignments = @{}
  $classDefs = New-Object 'System.Collections.Generic.HashSet[string]'

  foreach ($line in Get-Content $GraphPath) {
    if ($line -match '^\s*classDef\s+([A-Za-z0-9_-]+)') {
      [void]$classDefs.Add($matches[1])
      continue
    }

    if ($line -match '^\s*class\s+(.+?)\s+([A-Za-z0-9_-]+)\s*;?\s*$') {
      $className = $matches[2]
      foreach ($nodeId in @($matches[1] -split ',')) {
        $nodeId = $nodeId.Trim()
        if ([string]::IsNullOrWhiteSpace($nodeId)) {
          continue
        }

        if (-not $classAssignments.ContainsKey($nodeId)) {
          $classAssignments[$nodeId] = New-Object 'System.Collections.Generic.HashSet[string]'
        }
        [void]$classAssignments[$nodeId].Add($className)
      }
      continue
    }

    foreach ($match in [regex]::Matches($line, '(^|[\s])([A-Za-z0-9_]+)\s*(?:\["|\(|\{|\>)')) {
      [void]$declaredNodes.Add($match.Groups[2].Value)
      [void]$usedNodes.Add($match.Groups[2].Value)
    }

    foreach ($match in [regex]::Matches($line, '([A-Za-z0-9_]+)\s*(?:-->|--\>|-.->|==>)')) {
      [void]$usedNodes.Add($match.Groups[1].Value)
    }

    foreach ($match in [regex]::Matches($line, '(?:-->|--\>|-.->|==>)\s*(?:\|[^|]*\|\s*)?([A-Za-z0-9_]+)')) {
      [void]$usedNodes.Add($match.Groups[1].Value)
    }
  }

  $issues = @()
  $graphUsesClasses = $classDefs.Count -gt 0 -or $classAssignments.Keys.Count -gt 0
  $validationSettings = $Settings.classValidation
  $requireClassCoverage = $graphUsesClasses -and ($null -eq $validationSettings -or [bool]$validationSettings.requireClassesWhenGraphUsesClasses)

  if ($requireClassCoverage) {
    foreach ($nodeId in @($usedNodes | Sort-Object)) {
      if (-not $classAssignments.ContainsKey($nodeId)) {
        $issues += ('Node `{0}` is used but has no explicit class assignment.' -f $nodeId)
      }
    }
  }

  foreach ($nodeId in @($classAssignments.Keys | Sort-Object)) {
    if (-not $usedNodes.Contains($nodeId) -and -not $declaredNodes.Contains($nodeId)) {
      $issues += ('Class assignment references missing node `{0}`.' -f $nodeId)
    }

    foreach ($className in $classAssignments[$nodeId]) {
      if ($classDefs.Count -gt 0 -and -not $classDefs.Contains($className)) {
        $issues += ('Node `{0}` uses undefined class `{1}`.' -f $nodeId, $className)
      }
    }
  }

  if ($null -ne $validationSettings -and $null -ne $validationSettings.semanticPatterns) {
    foreach ($rule in @($validationSettings.semanticPatterns)) {
      foreach ($nodeId in @($usedNodes | Sort-Object)) {
        $matchesRule = $false
        foreach ($pattern in @($rule.patterns)) {
          if ($nodeId -match $pattern) {
            $matchesRule = $true
            break
          }
        }

        if ($matchesRule -and (-not $classAssignments.ContainsKey($nodeId) -or -not $classAssignments[$nodeId].Contains($rule.className))) {
          $issues += ('Node `{0}` matches semantic class `{1}` but is not assigned to that class.' -f $nodeId, $rule.className)
        }
      }
    }
  }

  return @($issues)
}

function Assert-MermaidClassValidation {
  param(
    [string]$GraphPath,
    [object]$Settings
  )

  if ($null -ne $Settings.classValidation -and -not [bool]$Settings.classValidation.enabled) {
    return
  }

  $issues = Get-MermaidClassValidation $GraphPath $Settings
  if ($issues.Count -gt 0) {
    throw "Mermaid class validation failed for $GraphPath`n- $($issues -join "`n- ")"
  }
}

function Get-MermaidLayoutValidation {
  param(
    [string]$GraphPath,
    [object]$Settings
  )

  $classAssignments = @{}
  $nodeLabels = @{}
  $edges = @()

  foreach ($line in Get-Content $GraphPath) {
    if ($line -match '^\s*class\s+(.+?)\s+([A-Za-z0-9_-]+)\s*;?\s*$') {
      $className = $matches[2]
      foreach ($nodeId in @($matches[1] -split ',')) {
        $nodeId = $nodeId.Trim()
        if ([string]::IsNullOrWhiteSpace($nodeId)) {
          continue
        }

        if (-not $classAssignments.ContainsKey($nodeId)) {
          $classAssignments[$nodeId] = New-Object 'System.Collections.Generic.HashSet[string]'
        }
        [void]$classAssignments[$nodeId].Add($className)
      }
      continue
    }

    foreach ($match in [regex]::Matches($line, '(^|[\s])([A-Za-z0-9_]+)\s*\["([^"]+)"\]')) {
      $nodeLabels[$match.Groups[2].Value] = (($match.Groups[3].Value -replace '<br/>', ' ') -replace '\s+', ' ').Trim()
    }

    $edgeMatch = [regex]::Match($line, '^\s*([A-Za-z0-9_]+)\s*(?:-->|--\>|-.->|==>)\s*(?:\|[^|]*\|\s*)?([A-Za-z0-9_]+)')
    if ($edgeMatch.Success) {
      $edges += [pscustomobject]@{
        Source = $edgeMatch.Groups[1].Value
        Target = $edgeMatch.Groups[2].Value
      }
    }
  }

  $layoutSettings = $Settings.layoutValidation
  $sectionClasses = if ($null -ne $layoutSettings -and $null -ne $layoutSettings.sectionClassNames) { @($layoutSettings.sectionClassNames) } else { @("group") }
  $crossSectionTargetClasses = if ($null -ne $layoutSettings -and $null -ne $layoutSettings.crossSectionTargetClasses) { @($layoutSettings.crossSectionTargetClasses) } else { @("holder", "sequence") }
  $duplicateLabelIgnoreClasses = if ($null -ne $layoutSettings -and $null -ne $layoutSettings.duplicateLabelIgnoreClasses) { @($layoutSettings.duplicateLabelIgnoreClasses) } else { @("relationship") }
  $proxyNodeIdPatterns = if ($null -ne $layoutSettings -and $null -ne $layoutSettings.proxyNodeIdPatterns) { @($layoutSettings.proxyNodeIdPatterns) } else { @("(^|_)ref(erence)?$", "(^|_)proxy$", "_ref_", "_proxy_") }
  $proxyLabelPatterns = if ($null -ne $layoutSettings -and $null -ne $layoutSettings.proxyLabelPatterns) { @($layoutSettings.proxyLabelPatterns) } else { @("reference", "proxy", "see ", "reconstruction", "summary") }
  $orderedSeriesSettings = if ($null -ne $layoutSettings -and $null -ne $layoutSettings.orderedSeriesValidation) { $layoutSettings.orderedSeriesValidation } else { $null }

  function Test-NodeHasAnyClass {
    param(
      [string]$NodeId,
      [string[]]$ClassNames
    )

    if (-not $classAssignments.ContainsKey($NodeId)) {
      return $false
    }

    foreach ($className in $ClassNames) {
      if ($classAssignments[$NodeId].Contains($className)) {
        return $true
      }
    }

    return $false
  }

  function Test-LabelMatchesAnyPattern {
    param(
      [string]$Label,
      [string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
      if ($Label -match $pattern) {
        return $true
      }
    }

    return $false
  }

  $issues = @()

  $labelsByText = @{}
  foreach ($nodeId in @($nodeLabels.Keys | Sort-Object)) {
    if (Test-NodeHasAnyClass $nodeId $duplicateLabelIgnoreClasses) {
      continue
    }

    $label = $nodeLabels[$nodeId]
    if ([string]::IsNullOrWhiteSpace($label)) {
      continue
    }

    if (-not $labelsByText.ContainsKey($label)) {
      $labelsByText[$label] = @()
    }
    $labelsByText[$label] += $nodeId
  }

  foreach ($label in @($labelsByText.Keys | Sort-Object)) {
    $nodeIds = @($labelsByText[$label] | Sort-Object -Unique)
    if ($nodeIds.Count -gt 1) {
      $issues += ('Duplicate visual label `{0}` appears on multiple node IDs: {1}. Use one canonical node or label local references/proxies explicitly.' -f $label, ($nodeIds -join ", "))
    }
  }

  foreach ($nodeId in @($nodeLabels.Keys | Sort-Object)) {
    $isProxyLike = $false
    foreach ($pattern in $proxyNodeIdPatterns) {
      if ($nodeId -match $pattern) {
        $isProxyLike = $true
        break
      }
    }

    if (-not $isProxyLike) {
      continue
    }

    $label = $nodeLabels[$nodeId]
    $hasProxyLabel = $false
    foreach ($pattern in $proxyLabelPatterns) {
      if ($label -match $pattern) {
        $hasProxyLabel = $true
        break
      }
    }

    if (-not $hasProxyLabel) {
      $issues += ('Proxy/reference-like node `{0}` must label itself as a reference, proxy, reconstruction, summary, or `see ...` node. Current label: `{1}`.' -f $nodeId, $label)
    }
  }

  foreach ($edge in $edges) {
    if (-not (Test-NodeHasAnyClass $edge.Source $sectionClasses)) {
      continue
    }

    if (-not (Test-NodeHasAnyClass $edge.Target $crossSectionTargetClasses)) {
      continue
    }

    $otherIncoming = @($edges | Where-Object {
      $_.Target -eq $edge.Target -and
      $_.Source -ne $edge.Source -and
      -not (Test-NodeHasAnyClass $_.Source $sectionClasses)
    })

    if ($otherIncoming.Count -gt 0) {
      $owners = ($otherIncoming | ForEach-Object { $_.Source } | Sort-Object -Unique) -join ", "
      $issues += ('Section node `{0}` links directly to `{1}`, but `{1}` already has non-section incoming owner(s): {2}. Use a local reference/proxy node inside the section instead.' -f $edge.Source, $edge.Target, $owners)
    }
  }

  if ($null -ne $orderedSeriesSettings -and [bool]$orderedSeriesSettings.enabled) {
    $maxDirectChildren = if ($orderedSeriesSettings.maxDirectChildren) { [int]$orderedSeriesSettings.maxDirectChildren } else { 2 }
    $childLabelPatterns = if ($null -ne $orderedSeriesSettings.childLabelPatterns) {
      @($orderedSeriesSettings.childLabelPatterns)
    } else {
      @("^Seq\s*[0-9]", "^Sequence\s*[0-9]", "^Ch(?:apter)?\s*[0-9]", "^Episode\s*[0-9]", "^Step\s*[0-9]", "^Phase\s*[0-9]", "^Stage\s*[0-9]", "^Rank\s*[0-9]", "^Level\s*[0-9]")
    }

    foreach ($edgeGroup in @($edges | Group-Object Source)) {
      $orderedChildren = @()
      foreach ($edge in @($edgeGroup.Group)) {
        if (-not $nodeLabels.ContainsKey($edge.Target)) {
          continue
        }

        if (Test-LabelMatchesAnyPattern $nodeLabels[$edge.Target] $childLabelPatterns) {
          $orderedChildren += $edge.Target
        }
      }

      $orderedChildren = @($orderedChildren | Sort-Object -Unique)
      if ($orderedChildren.Count -gt $maxDirectChildren) {
        $issues += ('Node `{0}` has {1} direct ordered-series children: {2}. Ordered ladders, timelines, ranks, phases, chapters, steps, and sequences should usually chain child-to-child or use intermediate grouping nodes instead of wide sibling fan-out.' -f $edgeGroup.Name, $orderedChildren.Count, ($orderedChildren -join ", "))
      }
    }
  }

  return @($issues)
}

function Assert-MermaidLayoutValidation {
  param(
    [string]$GraphPath,
    [object]$Settings
  )

  if ($null -ne $Settings.layoutValidation -and -not [bool]$Settings.layoutValidation.enabled) {
    return
  }

  $issues = Get-MermaidLayoutValidation $GraphPath $Settings
  if ($issues.Count -gt 0) {
    throw "Mermaid layout validation failed for $GraphPath`n- $($issues -join "`n- ")"
  }
}

function Invoke-MermaidRender {
  param(
    [string]$InputFile,
    [string]$OutputFile,
    [object]$Settings,
    [string]$PuppeteerConfig
  )

  Assert-MermaidClassValidation $InputFile $Settings
  Assert-MermaidLayoutValidation $InputFile $Settings
  $renderSize = Get-MermaidRenderSize $InputFile $Settings
  $outputDirectory = Split-Path -Parent $OutputFile
  if (-not [string]::IsNullOrWhiteSpace($outputDirectory) -and -not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
  }

  $args = @(
    "-p", $PuppeteerConfig,
    "-i", $InputFile,
    "-o", $OutputFile,
    "-b", $Settings.background,
    "-w", $renderSize.Width,
    "-H", $renderSize.Height
  )

  if ([System.IO.Path]::GetExtension($OutputFile).ToLowerInvariant() -eq ".png") {
    $args += @("-s", $Settings.pngScale)
  }

  Write-Output ('Rendering {0} -> {1} ({2}x{3}, nodes={4}, edges={5}, maxFanOut={6})' -f $InputFile, $OutputFile, $renderSize.Width, $renderSize.Height, $renderSize.NodeCount, $renderSize.EdgeCount, $renderSize.MaxFanOut)
  & mmdc @args
  if ($LASTEXITCODE -ne 0) {
    throw "Mermaid render failed for $InputFile with exit code $LASTEXITCODE"
  }
}

$settingsFullPath = Resolve-RepoPath $SettingsPath
$settings = Get-Content $settingsFullPath -Raw | ConvertFrom-Json
$puppeteerConfig = Resolve-RepoPath $settings.puppeteerConfig
$inputFullPath = Resolve-RepoPath $InputPath

if (-not (Test-Path $inputFullPath)) {
  throw "Input Mermaid file not found: $InputPath"
}

if ($null -eq $OutputPath -or $OutputPath.Count -eq 0) {
  $baseName = [System.IO.Path]::GetFileNameWithoutExtension($inputFullPath)
  $OutputPath = @(
    "Visualization/rendered/$baseName.svg",
    "Visualization/rendered/$baseName.png"
  )
}

foreach ($output in $OutputPath) {
  Invoke-MermaidRender $inputFullPath (Resolve-RepoPath $output) $settings $puppeteerConfig
}
