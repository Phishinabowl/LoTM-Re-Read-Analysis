param(
  [Alias("Action")]
  [string]$Mode = "Refresh",
  [Alias("Input", "Graph")]
  [string]$InputPath,
  [Alias("Output", "Out")]
  [string[]]$OutputPath,
  [Alias("Settings")]
  [string]$SettingsPath = "Visualization/config/render-settings.json",
  [Alias("NoRender")]
  [switch]$SkipRender
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$SlugPrefixes = @(
  "artifact",
  "character",
  "concept",
  "deity",
  "event",
  "faction",
  "item",
  "location",
  "pathway",
  "tarot-card",
  "uniqueness"
)

$SlugPattern = "\b(?:" + (($SlugPrefixes | ForEach-Object { [regex]::Escape($_) }) -join "|") + ")-[a-z0-9][a-z0-9-]*\b"

function Resolve-RepoPath {
  param([string]$Path)

  if ([System.IO.Path]::IsPathRooted($Path)) {
    return $Path
  }

  return (Join-Path $repoRoot $Path)
}

function Resolve-VisualizationMode {
  param([string]$Name)

  switch -Regex ($Name) {
    '^(?i:refresh|update|generate)$' { return "Refresh" }
    '^(?i:render|manual-render|pure-render)$' { return "Render" }
    '^(?i:validate|check|test)$' { return "Validate" }
    default {
      throw "Unsupported visualization mode: $Name. Use Refresh, Render, or Validate. Aliases include Update, Generate, Manual-Render, Pure-Render, Check, and Test."
    }
  }
}

function ConvertFrom-Scalar {
  param([string]$Value)

  $value = $Value.Trim()
  if ($value -in @("", "null", "Null", "NULL")) {
    return ""
  }
  if ($value.Length -ge 2 -and ($value[0] -eq $value[$value.Length - 1]) -and $value[0] -in @("'", '"')) {
    return $value.Substring(1, $value.Length - 2)
  }
  return $value
}

function ConvertFrom-InlineMapping {
  param([string]$Value)

  $result = @{}
  $value = (ConvertFrom-Scalar $Value).Trim()
  if (-not ($value.StartsWith("{") -and $value.EndsWith("}"))) {
    return $result
  }
  $inner = $value.Substring(1, $value.Length - 2).Trim()
  if (-not $inner) {
    return $result
  }
  foreach ($part in $inner -split ",") {
    if (-not $part.Contains(":")) {
      continue
    }
    $pieces = $part.Split(":", 2)
    $result[$pieces[0].Trim()] = ConvertFrom-Scalar $pieces[1]
  }
  return $result
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
  $classDefLines = @{}
  $nodeLabels = @{}

  foreach ($line in Get-Content $GraphPath) {
    if ($line -match '^\s*classDef\s+([A-Za-z0-9_-]+)') {
      [void]$classDefs.Add($matches[1])
      $classDefLines[$matches[1]] = $line
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

    foreach ($match in [regex]::Matches($line, '(^|[\s])([A-Za-z0-9_]+)\s*\["([^"]+)"\]')) {
      $nodeLabels[$match.Groups[2].Value] = (($match.Groups[3].Value -replace '<br/>', ' ') -replace '\s+', ' ').Trim()
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
  $classDefs = New-Object 'System.Collections.Generic.HashSet[string]'
  $nodeLabels = @{}
  $edges = @()
  $subgraphCount = 0

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

    if ($line -match '^\s*subgraph\s+') {
      $subgraphCount += 1
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
  $denseGraphSettings = if ($null -ne $layoutSettings -and $null -ne $layoutSettings.denseGraphValidation) { $layoutSettings.denseGraphValidation } else { $null }
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

  if ($null -ne $denseGraphSettings -and [bool]$denseGraphSettings.enabled) {
    $graphNodeIds = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($nodeId in $nodeLabels.Keys) {
      [void]$graphNodeIds.Add($nodeId)
    }
    foreach ($edge in $edges) {
      [void]$graphNodeIds.Add($edge.Source)
      [void]$graphNodeIds.Add($edge.Target)
    }

    $minNodeCount = if ($denseGraphSettings.minNodeCount) { [int]$denseGraphSettings.minNodeCount } else { 20 }
    if ($graphNodeIds.Count -ge $minNodeCount) {
      if ([bool]$denseGraphSettings.requireClassDefinitions -and $classDefs.Count -eq 0) {
        $issues += ('Dense graph has {0} nodes but no `classDef` styling. Use styled node classes so readers can distinguish groups, entities, relationships, evidence, uncertainty, and other semantic roles.' -f $graphNodeIds.Count)
      }

      $maxSubgraphCount = if ($denseGraphSettings.maxSubgraphCount -ne $null) { [int]$denseGraphSettings.maxSubgraphCount } else { 4 }
      if ($subgraphCount -gt $maxSubgraphCount) {
        $issues += ('Dense graph uses {0} Mermaid subgraph clusters. Dense knowledge maps should usually use styled group nodes and a connected semantic spine; reserve subgraph clusters for a few large regions or explicitly requested cluster views.' -f $subgraphCount)
      }

      $adjacency = @{}
      foreach ($nodeId in $graphNodeIds) {
        $adjacency[$nodeId] = New-Object 'System.Collections.Generic.HashSet[string]'
      }
      foreach ($edge in $edges) {
        if (-not $adjacency.ContainsKey($edge.Source)) {
          $adjacency[$edge.Source] = New-Object 'System.Collections.Generic.HashSet[string]'
        }
        if (-not $adjacency.ContainsKey($edge.Target)) {
          $adjacency[$edge.Target] = New-Object 'System.Collections.Generic.HashSet[string]'
        }
        [void]$adjacency[$edge.Source].Add($edge.Target)
        [void]$adjacency[$edge.Target].Add($edge.Source)
      }

      $visited = New-Object 'System.Collections.Generic.HashSet[string]'
      $componentCount = 0
      foreach ($nodeId in @($graphNodeIds | Sort-Object)) {
        if ($visited.Contains($nodeId)) {
          continue
        }

        $componentCount += 1
        $queue = New-Object 'System.Collections.Generic.Queue[string]'
        [void]$visited.Add($nodeId)
        $queue.Enqueue($nodeId)

        while ($queue.Count -gt 0) {
          $current = $queue.Dequeue()
          foreach ($neighbor in $adjacency[$current]) {
            if (-not $visited.Contains($neighbor)) {
              [void]$visited.Add($neighbor)
              $queue.Enqueue($neighbor)
            }
          }
        }
      }

      $maxDisconnectedComponents = if ($denseGraphSettings.maxDisconnectedComponents -ne $null) { [int]$denseGraphSettings.maxDisconnectedComponents } else { 2 }
      if ($componentCount -gt $maxDisconnectedComponents) {
        $issues += ('Dense graph has {0} disconnected components. Dense knowledge maps should usually have a connected semantic spine, such as root -> group -> entity -> detail, unless the user explicitly requests separate disconnected diagrams.' -f $componentCount)
      }
    }
  }

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

  if ($null -ne $validationSettings -and $null -ne $validationSettings.uncertaintyClasses) {
    $stylePattern = if ($validationSettings.uncertaintyClassStylePattern) { [string]$validationSettings.uncertaintyClassStylePattern } else { "stroke-dasharray" }
    foreach ($className in @($validationSettings.uncertaintyClasses)) {
      if ($classDefs.Contains($className) -and $classDefLines.ContainsKey($className) -and $classDefLines[$className] -notmatch $stylePattern) {
        $issues += ('Uncertainty-style class `{0}` should include visual uncertainty styling matching `{1}`.' -f $className, $stylePattern)
      }
    }
  }

  if ($null -ne $validationSettings -and $null -ne $validationSettings.labelRoleRules) {
    foreach ($rule in @($validationSettings.labelRoleRules)) {
      foreach ($nodeId in @($nodeLabels.Keys | Sort-Object)) {
        $label = $nodeLabels[$nodeId]
        $matchesRule = $false
        foreach ($pattern in @($rule.patterns)) {
          if ($label -match $pattern) {
            $matchesRule = $true
            break
          }
        }

        if (-not $matchesRule) {
          continue
        }

        $hasAllowedClass = $false
        if ($classAssignments.ContainsKey($nodeId)) {
          foreach ($allowedClass in @($rule.allowedClasses)) {
            if ($classAssignments[$nodeId].Contains($allowedClass)) {
              $hasAllowedClass = $true
              break
            }
          }
        }

        if (-not $hasAllowedClass) {
          $issues += ('Node `{0}` label `{1}` matches visual role rule but is not assigned to one of: {2}. {3}' -f $nodeId, $label, (@($rule.allowedClasses) -join ", "), $rule.description)
        }
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
    [string]$InputPath,
    [string]$OutputPath,
    [object]$Settings,
    [string]$PuppeteerConfig
  )

  Assert-MermaidClassValidation $InputPath $Settings
  Assert-MermaidLayoutValidation $InputPath $Settings
  $renderSize = Get-MermaidRenderSize $InputPath $Settings
  $outputDirectory = Split-Path -Parent $OutputPath
  if (-not [string]::IsNullOrWhiteSpace($outputDirectory) -and -not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
  }

  $args = @(
    "-p", $PuppeteerConfig,
    "-i", $InputPath,
    "-o", $OutputPath,
    "-b", $Settings.background,
    "-w", $renderSize.Width,
    "-H", $renderSize.Height
  )

  if ([System.IO.Path]::GetExtension($OutputPath).ToLowerInvariant() -eq ".png") {
    $args += @("-s", $Settings.pngScale)
  }

  Write-Output ('Rendering {0} -> {1} ({2}x{3}, nodes={4}, edges={5}, maxFanOut={6})' -f $InputPath, $OutputPath, $renderSize.Width, $renderSize.Height, $renderSize.NodeCount, $renderSize.EdgeCount, $renderSize.MaxFanOut)
  & mmdc @args
  if ($LASTEXITCODE -ne 0) {
    throw "Mermaid render failed for $InputPath with exit code $LASTEXITCODE"
  }
}

function Read-PreviousMetrics {
  param([string]$ReportPath)

  $metrics = @{}
  if (-not (Test-Path $ReportPath)) {
    return $metrics
  }

  foreach ($line in Get-Content $ReportPath) {
    if ($line -match '^\|\s*([^|]+?)\s*\|\s*([0-9]+)\s*\|') {
      $metrics[$matches[1].Trim()] = [int]$matches[2]
    }
  }

  return $metrics
}

function Update-ReportSection {
  param(
    [string]$ReportPath,
    [string[]]$ReportLines
  )

  $startMarker = "<!-- VISUALIZATION-REFRESH-REPORT:START -->"
  $endMarker = "<!-- VISUALIZATION-REFRESH-REPORT:END -->"
  $replacement = @($startMarker) + $ReportLines + @($endMarker)

  if (-not (Test-Path $ReportPath)) {
    Set-Content -Path $ReportPath -Value $replacement -Encoding UTF8
    return
  }

  $content = @(Get-Content $ReportPath)
  $startIndex = [Array]::IndexOf($content, $startMarker)
  $endIndex = [Array]::IndexOf($content, $endMarker)

  if ($startIndex -ge 0 -and $endIndex -gt $startIndex) {
    $updated = @()
    if ($startIndex -gt 0) {
      $updated += $content[0..($startIndex - 1)]
    }
    $updated += $replacement
    if ($endIndex -lt ($content.Count - 1)) {
      $updated += $content[($endIndex + 1)..($content.Count - 1)]
    }

    Set-Content -Path $ReportPath -Value $updated -Encoding UTF8
    return
  }

  $updated = $content + @("", "## Refresh Tracker", "") + $replacement
  Set-Content -Path $ReportPath -Value $updated -Encoding UTF8
}

function Format-Delta {
  param(
    [hashtable]$Previous,
    [string]$Key,
    [int]$Current
  )

  if (-not $Previous.ContainsKey($Key)) {
    return "n/a"
  }

  $delta = $Current - [int]$Previous[$Key]
  if ($delta -gt 0) {
    return "+$delta"
  }

  return "$delta"
}

function Format-SnapshotDelta {
  param(
    [object]$PreviousSnapshot,
    [int]$PreviousValue,
    [int]$CurrentValue
  )

  if ($null -eq $PreviousSnapshot) {
    return "n/a"
  }

  $delta = $CurrentValue - $PreviousValue
  if ($delta -gt 0) {
    return "+$delta"
  }

  return "$delta"
}

function Get-GraphStats {
  param([string]$GraphPath)

  $nodes = New-Object 'System.Collections.Generic.HashSet[string]'
  $linked = New-Object 'System.Collections.Generic.HashSet[string]'
  $edges = @()
  $relationshipLabels = @{}
  $relationshipSources = @{}
  $relationshipTargets = @{}

  foreach ($line in Get-Content $GraphPath) {
    if ($line -match '^\s+([A-Za-z0-9_]+)\["(.+)"\]') {
      $nodeId = $matches[1]
      $label = $matches[2]
      if ($nodeId -match '^rel_[0-9]+$') {
        $relationshipLabels[$nodeId] = (($label -replace '<br/>', ' ') -replace '\\"', '"').Trim()
      } else {
        [void]$nodes.Add($nodeId)
      }
      continue
    }

    if ($line -match '^\s+([A-Za-z0-9_]+)\s+-->\|([^|]+)\|\s+([A-Za-z0-9_]+)') {
      $source = $matches[1]
      $label = $matches[2].Trim()
      $target = $matches[3]

      $edges += [pscustomobject]@{
        source = $source
        target = $target
        label = $label
        key = "$source|$label|$target"
        endpointKey = "$source|$target"
      }

      [void]$linked.Add($source)
      [void]$linked.Add($target)
      continue
    }

    if ($line -match '^\s+([A-Za-z0-9_]+)\s+-->\s+(rel_[0-9]+)') {
      $relationshipSources[$matches[2]] = $matches[1]
      continue
    }

    if ($line -match '^\s+(rel_[0-9]+)\s+-->\s+([A-Za-z0-9_]+)') {
      $relationshipTargets[$matches[1]] = $matches[2]
      continue
    }
  }

  foreach ($relationshipId in $relationshipLabels.Keys) {
    if (-not $relationshipSources.ContainsKey($relationshipId) -or -not $relationshipTargets.ContainsKey($relationshipId)) {
      continue
    }

    $source = $relationshipSources[$relationshipId]
    $target = $relationshipTargets[$relationshipId]
    $label = $relationshipLabels[$relationshipId]

    $edges += [pscustomobject]@{
      source = $source
      target = $target
      label = $label
      key = "$source|$label|$target"
      endpointKey = "$source|$target"
    }

    [void]$linked.Add($source)
    [void]$linked.Add($target)
  }

  $orphans = @()
  foreach ($node in $nodes) {
    if (-not $linked.Contains($node)) {
      $orphans += $node
    }
  }

  return [pscustomobject]@{
    NodeIds = @($nodes | Sort-Object)
    Relationships = @($edges | Sort-Object key)
    OrphanNodes = $orphans
  }
}

function New-GraphSnapshot {
  param(
    [object]$Stats,
    [object[]]$Views,
    [string[]]$RenderedFiles,
    [string[]]$BrokenLinks,
    [string[]]$PendingNodes,
    [string]$Timestamp
  )

  return [pscustomobject]@{
    generated_at = $Timestamp
    nodes = @($Stats.NodeIds)
    relationships = @($Stats.Relationships | ForEach-Object {
      [pscustomobject]@{
        source = $_.source
        target = $_.target
        label = $_.label
        key = $_.key
        endpointKey = $_.endpointKey
      }
    })
    views = @($Views | ForEach-Object { $_.name })
    rendered_files = @($RenderedFiles)
    broken_links = @($BrokenLinks)
    orphan_nodes = @($Stats.OrphanNodes)
    pending_nodes = @($PendingNodes)
  }
}

function Read-PreviousSnapshot {
  param([string]$SnapshotPath)

  if (-not (Test-Path $SnapshotPath)) {
    return $null
  }

  return Get-Content $SnapshotPath -Raw | ConvertFrom-Json
}

function Compare-StringSet {
  param(
    [string[]]$Previous,
    [string[]]$Current
  )

  $previousSet = New-Object 'System.Collections.Generic.HashSet[string]'
  $currentSet = New-Object 'System.Collections.Generic.HashSet[string]'

  foreach ($item in @($Previous)) {
    if (-not [string]::IsNullOrWhiteSpace($item)) {
      [void]$previousSet.Add($item)
    }
  }

  foreach ($item in @($Current)) {
    if (-not [string]::IsNullOrWhiteSpace($item)) {
      [void]$currentSet.Add($item)
    }
  }

  $added = @()
  foreach ($item in $currentSet) {
    if (-not $previousSet.Contains($item)) {
      $added += $item
    }
  }

  $removed = @()
  foreach ($item in $previousSet) {
    if (-not $currentSet.Contains($item)) {
      $removed += $item
    }
  }

  return [pscustomobject]@{
    Added = @($added | Sort-Object)
    Removed = @($removed | Sort-Object)
  }
}

function Get-DuplicateRelationships {
  param([object[]]$Relationships)

  return @(
    $Relationships |
      Group-Object key |
      Where-Object { $_.Count -gt 1 } |
      ForEach-Object { "$($_.Name) x$($_.Count)" } |
      Sort-Object
  )
}

function Get-ChangedRelationships {
  param(
    [object[]]$PreviousRelationships,
    [object[]]$CurrentRelationships
  )

  $previousByEndpoint = @{}
  foreach ($relationship in @($PreviousRelationships)) {
    if (-not $previousByEndpoint.ContainsKey($relationship.endpointKey)) {
      $previousByEndpoint[$relationship.endpointKey] = New-Object 'System.Collections.Generic.HashSet[string]'
    }
    [void]$previousByEndpoint[$relationship.endpointKey].Add($relationship.label)
  }

  $currentByEndpoint = @{}
  foreach ($relationship in @($CurrentRelationships)) {
    if (-not $currentByEndpoint.ContainsKey($relationship.endpointKey)) {
      $currentByEndpoint[$relationship.endpointKey] = New-Object 'System.Collections.Generic.HashSet[string]'
    }
    [void]$currentByEndpoint[$relationship.endpointKey].Add($relationship.label)
  }

  $changes = @()
  foreach ($endpoint in $currentByEndpoint.Keys) {
    if (-not $previousByEndpoint.ContainsKey($endpoint)) {
      continue
    }

    $previousLabels = @($previousByEndpoint[$endpoint] | Sort-Object)
    $currentLabels = @($currentByEndpoint[$endpoint] | Sort-Object)
    if (($previousLabels -join " || ") -ne ($currentLabels -join " || ")) {
      $parts = $endpoint -split '\|'
      $changes += [pscustomobject]@{
        source = $parts[0]
        target = $parts[1]
        previous = ($previousLabels -join "; ")
        current = ($currentLabels -join "; ")
      }
    }
  }

  return @($changes | Sort-Object source,target)
}

function Get-PendingGraphNodes {
  $statePath = Resolve-RepoPath "CURRENT_STATE.md"
  $pending = @()
  $inSection = $false

  foreach ($line in Get-Content $statePath) {
    if ($line -eq "### Deferred Graph Nodes") {
      $inSection = $true
      continue
    }

    if ($inSection -and $line -match '^###\s+') {
      break
    }

    if ($inSection -and $line -match '^\-\s+(.+)$') {
      $pending += ($matches[1].Trim() -replace '\]\(Investigations/', '](../Investigations/')
    }
  }

  return $pending
}

function Get-BrokenMarkdownLinks {
  $broken = @()
  $markdownFiles = Get-ChildItem -Recurse -Filter "*.md" |
    Where-Object {
      $_.FullName -notmatch '\\.git\\' -and
      $_.FullName -notmatch '\\Source\\' -and
      $_.Name -ne "TEMPLATE.md"
    }

  foreach ($file in $markdownFiles) {
    $text = Get-Content $file.FullName -Raw
    $matches = [regex]::Matches($text, '\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)')

    foreach ($match in $matches) {
      $target = $match.Groups[1].Value.Trim()
      $target = $target.Trim("<", ">")

      if ($target -match '^(https?:|mailto:)') {
        continue
      }

      $target = [uri]::UnescapeDataString($target)
      $targetPath = Join-Path $file.DirectoryName $target

      if (-not (Test-Path $targetPath)) {
        $targetFullPath = [System.IO.Path]::GetFullPath($targetPath)
        $repoFullPath = [System.IO.Path]::GetFullPath($repoRoot)
        $plannedGlossaryRoot = [System.IO.Path]::GetFullPath((Join-Path $repoFullPath "Glossary_Threads"))
        if ($targetFullPath.StartsWith($plannedGlossaryRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
          continue
        }
        $relativeFile = Resolve-Path -Relative $file.FullName
        $broken += "$relativeFile -> $target"
      }
    }
  }

  return $broken
}

function Convert-SlugToNodeId {
  param([string]$Slug)

  $name = [System.IO.Path]::GetFileNameWithoutExtension($Slug)
  return ($name -replace '-', '_')
}

function Convert-SlugToFallbackLabel {
  param([string]$Slug)

  $name = [System.IO.Path]::GetFileNameWithoutExtension($Slug)
  $name = $name -replace '^(artifact|character|concept|deity|epoch|event|faction|family|item|location|mystery|pathway|tarot-card|timeline|uniqueness)-', ''
  $parts = @($name -split '-' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  $labelParts = foreach ($part in $parts) {
    if ($part -match '^[0-9]+$') {
      $part
    } elseif ($part -match '^[0-9]+_[0-9]+$') {
      $part -replace '_', '-'
    } else {
      $part.Substring(0, 1).ToUpperInvariant() + $part.Substring(1)
    }
  }

  return ($labelParts -join ' ')
}

function Convert-NodeIdToFallbackLabel {
  param([string]$NodeId)

  $slug = $NodeId -replace '_', '-'
  return Convert-SlugToFallbackLabel $slug
}

function Read-GlossaryNodes {
  $nodes = @{}
  $files = Get-ChildItem -Path (Resolve-RepoPath "Glossary_Threads") -Recurse -Filter "*.md" |
    Where-Object { $_.Name -ne "TEMPLATE.md" }

  foreach ($file in $files) {
    $slug = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $nodeId = Convert-SlugToNodeId $slug
    $label = $null
    $subjectVisibleFrom = ""
    $status = ""
    foreach ($line in Get-Content $file.FullName) {
      if ($null -eq $label -and $line -match '^#\s+(.+)$') {
        $label = $matches[1].Trim()
      }
      if ([string]::IsNullOrWhiteSpace($subjectVisibleFrom) -and $line -match '^Subject Visible From:\s*(.+?)\s*$') {
        $subjectVisibleFrom = $matches[1].Trim()
      }
      if ([string]::IsNullOrWhiteSpace($status) -and $line -match '^Status:\s*(.+?)\s*$') {
        $status = $matches[1].Trim().ToLowerInvariant()
      }
      if ($null -ne $label -and -not [string]::IsNullOrWhiteSpace($subjectVisibleFrom) -and -not [string]::IsNullOrWhiteSpace($status)) {
        break
      }
    }
    if ($null -eq $label) {
      $label = Convert-SlugToFallbackLabel $slug
    }
    $nodes[$nodeId] = [pscustomobject]@{
      label = $label
      subject_visible_from = $subjectVisibleFrom
      status = $status
    }
  }

  return $nodes
}

function Get-MarkdownSection {
  param(
    [string]$Text,
    [string]$Heading
  )

  $pattern = "(?ms)^##\s+" + [regex]::Escape($Heading) + "\s*\r?\n(.*?)(?=^##\s+|\z)"
  $match = [regex]::Match($Text, $pattern)
  if ($match.Success) {
    return $match.Groups[1].Value
  }
  return ""
}

function Get-FencedYamlBlocks {
  param([string]$Text)

  $blocks = @()
  foreach ($match in [regex]::Matches($Text, '```yaml\s*(.*?)```', [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
    $blocks += [pscustomobject]@{
      Text = $match.Groups[1].Value.Trim()
    }
  }
  return @($blocks)
}

function Get-RelationshipYaml {
  param([string]$Text)

  $section = Get-MarkdownSection $Text "Relationship Seeds"
  if ([string]::IsNullOrWhiteSpace($section)) {
    return ""
  }
  $match = [regex]::Match($section, '```yaml\s*(.*?)```', [System.Text.RegularExpressions.RegexOptions]::Singleline)
  if ($match.Success) {
    return $match.Groups[1].Value.Trim()
  }
  return ""
}

function ConvertTo-ProjectionSlug {
  param([string]$Value)

  $value = (ConvertFrom-Scalar $Value).Trim()
  if (-not $value) {
    return ""
  }
  if ([regex]::IsMatch($value, "^$SlugPattern$")) {
    return $value
  }
  $value = [regex]::Replace($value, "[/\\]+", " ")
  $value = [regex]::Replace($value, "[^A-Za-z0-9]+", "-").Trim("-").ToLowerInvariant()
  return $value
}

function Get-ProjectionKeysForRow {
  param([hashtable]$Row)

  $keys = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($field in @("target", "ability", "event", "pathway", "organization", "item", "label", "field", "entity", "uniqueness")) {
    if (-not $Row.ContainsKey($field) -or -not $Row[$field]) {
      continue
    }
    $slug = ConvertTo-ProjectionSlug $Row[$field]
    if (-not $slug) {
      continue
    }
    [void]$keys.Add($slug)
    foreach ($prefix in $SlugPrefixes) {
      [void]$keys.Add("$prefix-$slug")
    }
  }
  return @($keys)
}

function New-AvailabilityEntry {
  param([hashtable]$Data)

  return [pscustomobject]@{
    medium = if ($Data.ContainsKey("medium")) { $Data["medium"] } else { "" }
    volume = if ($Data.ContainsKey("from_volume")) { $Data["from_volume"] } elseif ($Data.ContainsKey("volume")) { $Data["volume"] } else { "" }
    chapter = if ($Data.ContainsKey("from_chapter")) { $Data["from_chapter"] } elseif ($Data.ContainsKey("chapter")) { $Data["chapter"] } else { "" }
    season = if ($Data.ContainsKey("from_season")) { $Data["from_season"] } elseif ($Data.ContainsKey("season")) { $Data["season"] } else { "" }
    episode = if ($Data.ContainsKey("from_episode")) { $Data["from_episode"] } elseif ($Data.ContainsKey("episode")) { $Data["episode"] } else { "" }
    release_order = if ($Data.ContainsKey("from_release_order")) { $Data["from_release_order"] } elseif ($Data.ContainsKey("release_order")) { $Data["release_order"] } else { "" }
    status = if ($Data.ContainsKey("status")) { $Data["status"] } elseif ($Data.ContainsKey("possession_status")) { $Data["possession_status"] } elseif ($Data.ContainsKey("outcome_status")) { $Data["outcome_status"] } else { "" }
    confidence = if ($Data.ContainsKey("confidence")) { $Data["confidence"] } else { "" }
    graph_visibility = if ($Data.ContainsKey("graph_visibility")) { $Data["graph_visibility"] } else { "" }
  }
}

function Add-ProjectionRow {
  param(
    [string]$RootKey,
    [string]$SectionKey,
    [string]$NoteSlug,
    [hashtable]$Row,
    [object[]]$Availability,
    [hashtable]$Projections
  )

  if ($null -eq $Row -or -not $RootKey -or -not $SectionKey -or @($Availability).Count -eq 0) {
    return
  }
  foreach ($key in Get-ProjectionKeysForRow $Row) {
    $projectionSource = "$RootKey.$SectionKey[$key]"
    $Projections["$NoteSlug|$projectionSource"] = @($Availability)
    if (-not $Projections.ContainsKey($projectionSource)) {
      $Projections[$projectionSource] = @($Availability)
    }
  }
}

function Read-DataProjections {
  $projections = @{}
  $files = Get-ChildItem -Path (Resolve-RepoPath "Glossary_Threads") -Recurse -Filter "*.md" |
    Where-Object { $_.Name -ne "TEMPLATE.md" }

  foreach ($file in $files) {
    $text = [System.IO.File]::ReadAllText($file.FullName, [System.Text.UTF8Encoding]::new($true))
    $noteSlug = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $relationshipBlock = Get-RelationshipYaml $text
    foreach ($block in Get-FencedYamlBlocks $text) {
      if ($relationshipBlock -and $block.Text -eq $relationshipBlock) {
        continue
      }

      $rootKey = ""
      $sectionKey = ""
      $row = $null
      $availability = @()
      $availabilityItem = $null
      $inAvailability = $false
      $inFrom = $false

      foreach ($rawLine in $block.Text -split "`r?`n") {
        if ([string]::IsNullOrWhiteSpace($rawLine) -or -not $rawLine.Contains(":")) {
          continue
        }
        $indent = $rawLine.Length - $rawLine.TrimStart(" ").Length
        $line = $rawLine.Trim()

        if ($indent -eq 0 -and -not $line.StartsWith("- ")) {
          if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
          Add-ProjectionRow $rootKey $sectionKey $noteSlug $row $availability $projections
          $row = $null; $availability = @(); $availabilityItem = $null; $inAvailability = $false; $inFrom = $false
          $parts = $line.Split(":", 2)
          $rootKey = if ((ConvertFrom-Scalar $parts[1]) -eq "") { $parts[0].Trim() } else { "" }
          $sectionKey = ""
          continue
        }

        if ($rootKey -and $indent -eq 2 -and -not $line.StartsWith("- ")) {
          if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
          Add-ProjectionRow $rootKey $sectionKey $noteSlug $row $availability $projections
          $row = $null; $availability = @(); $availabilityItem = $null; $inAvailability = $false; $inFrom = $false
          $parts = $line.Split(":", 2)
          $sectionKey = if ((ConvertFrom-Scalar $parts[1]) -eq "") { $parts[0].Trim() } else { "" }
          continue
        }

        if ($rootKey -and $sectionKey -and $indent -eq 4 -and $line.StartsWith("- ")) {
          if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
          Add-ProjectionRow $rootKey $sectionKey $noteSlug $row $availability $projections
          $row = @{}; $availability = @(); $availabilityItem = $null; $inAvailability = $false; $inFrom = $false
          $line = $line.Substring(2).Trim()
          if (-not $line.Contains(":")) {
            continue
          }
        }

        if ($null -eq $row) {
          continue
        }

        $parts = $line.Split(":", 2)
        $key = $parts[0].Trim().TrimStart("-").Trim()
        $value = ConvertFrom-Scalar $parts[1]

        if ($indent -eq 4) {
          $row[$key] = $value
          $inAvailability = $false
          $inFrom = $false
        } elseif ($indent -eq 6 -and $key -ne "availability" -and -not $inAvailability) {
          $row[$key] = $value
        } elseif ($indent -eq 6 -and $key -eq "availability") {
          if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
          $availabilityItem = $null
          $inAvailability = $true
          $inFrom = $false
        } elseif ($indent -eq 8 -and $line.StartsWith("- ")) {
          if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
          $availabilityItem = @{}
          if ($key) { $availabilityItem[$key] = $value }
          $inAvailability = $true
          $inFrom = $false
        } elseif ($inAvailability -and $null -ne $availabilityItem) {
          if ($key -eq "from") {
            $mapping = ConvertFrom-InlineMapping $value
            foreach ($mappingKey in $mapping.Keys) {
              $availabilityItem["from_$mappingKey"] = $mapping[$mappingKey]
            }
            $inFrom = $true
          } elseif ($inFrom -and $indent -ge 12) {
            $availabilityItem["from_$key"] = $value
          } else {
            $availabilityItem[$key] = $value
            $inFrom = $false
          }
        }
      }
      if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
      Add-ProjectionRow $rootKey $sectionKey $noteSlug $row $availability $projections
    }
  }

  return $projections
}

function Read-RelationshipSeeds {
  $relationships = @()
  $files = Get-ChildItem -Path (Resolve-RepoPath "Glossary_Threads") -Recurse -Filter "*.md" |
    Where-Object { $_.Name -ne "TEMPLATE.md" }

  foreach ($file in $files) {
    $inSection = $false
    $inCode = $false
    $current = $null

    foreach ($line in Get-Content $file.FullName) {
      if ($line -eq "## Relationship Seeds") {
        $inSection = $true
        continue
      }

      if ($inSection -and -not $inCode -and $line -match '^##\s+') {
        break
      }

      if (-not $inSection) {
        continue
      }

      if ($line -match '^```') {
        if ($inCode -and $null -ne $current) {
          $relationships += $current
          $current = $null
        }
        $inCode = -not $inCode
        continue
      }

      if (-not $inCode) {
        continue
      }

      if ($line -match '^\s+-\s+source:\s*(.+?)\s*$') {
        if ($null -ne $current) {
          $relationships += $current
        }
        $current = [ordered]@{
          source = $matches[1].Trim()
          target = ""
          relationship_type = ""
          medium = ""
          volume = ""
          chapter = ""
          status = ""
          confidence = ""
          projection_source = ""
          projection_scope = ""
          history_label = ""
        }
        continue
      }

      if ($null -eq $current) {
        continue
      }

      if ($line -match '^\s+target:\s*(.+?)\s*$') {
        $current.target = $matches[1].Trim()
      } elseif ($line -match '^\s+relationship_type:\s*(.+?)\s*$') {
        $current.relationship_type = $matches[1].Trim()
      } elseif ([string]::IsNullOrWhiteSpace($current.medium) -and $line -match '^\s+medium:\s*(.+?)\s*$') {
        $current.medium = $matches[1].Trim()
      } elseif ([string]::IsNullOrWhiteSpace($current.volume) -and $line -match '^\s+volume:\s*(.+?)\s*$') {
        $current.volume = $matches[1].Trim()
      } elseif ([string]::IsNullOrWhiteSpace($current.chapter) -and $line -match '^\s+chapter:\s*(.+?)\s*$') {
        $current.chapter = $matches[1].Trim()
      } elseif ($line -match '^\s+status:\s*(.+?)\s*$') {
        $current.status = $matches[1].Trim()
      } elseif ($line -match '^\s+confidence:\s*(.+?)\s*$') {
        $current.confidence = $matches[1].Trim()
      } elseif ($line -match '^\s+projection_source:\s*(.+?)\s*$') {
        $current.projection_source = $matches[1].Trim()
      } elseif ($line -match '^\s+projection_scope:\s*(.+?)\s*$') {
        $current.projection_scope = $matches[1].Trim()
      }
    }

    if ($inSection -and $inCode -and $null -ne $current) {
      $relationships += $current
    }
  }

  return @($relationships | Where-Object {
    -not [string]::IsNullOrWhiteSpace($_.source) -and
    -not [string]::IsNullOrWhiteSpace($_.target) -and
    -not [string]::IsNullOrWhiteSpace($_.relationship_type)
  })
}

function Convert-BoundaryNumber {
  param([object]$Value)

  $text = [string]$Value
  if ($text -match '^\d+$') {
    return [int]$text
  }
  return $null
}

function Convert-SubjectVisibleFrom {
  param([string]$Value)

  if ($Value -match '\bNovel\s+V(?:ol(?:ume)?)?\s*(\d+)\s+Ch(?:apter)?\s*(\d+)\b') {
    return [pscustomobject]@{
      medium = "novel"
      volume = [int]$matches[1]
      chapter = [int]$matches[2]
    }
  }

  return [pscustomobject]@{
    medium = ""
    volume = $null
    chapter = $null
  }
}

function Test-PositionVisible {
  param(
    [object]$Medium,
    [object]$Volume,
    [object]$Chapter,
    [object]$Boundary
  )

  $boundaryMedium = ([string]$Boundary.medium).Trim().ToLowerInvariant()
  if (-not [string]::IsNullOrWhiteSpace($boundaryMedium) -and ([string]$Medium).Trim().ToLowerInvariant() -ne $boundaryMedium) {
    return $false
  }

  $volumeNumber = Convert-BoundaryNumber $Volume
  $chapterNumber = Convert-BoundaryNumber $Chapter
  if ($null -eq $volumeNumber -or $null -eq $chapterNumber) {
    return [bool]$Boundary.includeUnknownPositions
  }

  if ($null -ne $Boundary.maxVolume -and $volumeNumber -gt [int]$Boundary.maxVolume) {
    return $false
  }

  if ($null -ne $Boundary.maxVolume -and $null -ne $Boundary.maxChapter -and $volumeNumber -eq [int]$Boundary.maxVolume -and $chapterNumber -gt [int]$Boundary.maxChapter) {
    return $false
  }

  return $true
}

function Select-NodesForBoundary {
  param(
    [hashtable]$Nodes,
    [object]$Boundary
  )

  $filtered = @{}
  if ($null -eq $Boundary) {
    foreach ($nodeId in $Nodes.Keys) {
      $filtered[$nodeId] = $Nodes[$nodeId].label
    }
    return $filtered
  }

  foreach ($nodeId in $Nodes.Keys) {
    $node = $Nodes[$nodeId]
    if ([string]::IsNullOrWhiteSpace($node.subject_visible_from)) {
      if ([bool]$Boundary.includeUnknownSubjects) {
        $filtered[$nodeId] = $node.label
      }
      continue
    }

    $visibleFrom = Convert-SubjectVisibleFrom $node.subject_visible_from
    if (Test-PositionVisible $visibleFrom.medium $visibleFrom.volume $visibleFrom.chapter $Boundary) {
      $filtered[$nodeId] = $node.label
    }
  }

  return $filtered
}

function Test-AvailabilityPinned {
  param([object]$Entry)

  if ($Entry.medium -eq "novel") {
    return ($null -ne (Convert-BoundaryNumber $Entry.volume) -and $null -ne (Convert-BoundaryNumber $Entry.chapter))
  }
  if ($Entry.medium -eq "donghua") {
    foreach ($key in @("season", "episode", "release_order")) {
      if (-not [string]::IsNullOrWhiteSpace($Entry.$key) -and $Entry.$key -ne "TBD") {
        return $true
      }
    }
  }
  return $false
}

function Test-AvailabilityVisible {
  param(
    [object]$Entry,
    [object]$Boundary
  )

  if (-not (Test-AvailabilityPinned $Entry)) {
    return $false
  }
  if ($null -ne $Boundary -and -not (Test-PositionVisible $Entry.medium $Entry.volume $Entry.chapter $Boundary)) {
    return $false
  }
  if ($Entry.graph_visibility -eq "hidden") {
    return $false
  }
  return $true
}

function Format-AvailabilityEntry {
  param(
    [object]$Entry,
    [switch]$TimingSpoilerFree
  )

  $parts = @()
  if (-not $TimingSpoilerFree) {
    if ($Entry.medium -eq "novel" -and -not [string]::IsNullOrWhiteSpace($Entry.chapter)) {
      $parts += "ch$($Entry.chapter)"
    } elseif ($Entry.medium -eq "donghua") {
      if (-not [string]::IsNullOrWhiteSpace($Entry.season) -and $Entry.season -ne "TBD") {
        $parts += "s$($Entry.season)"
      }
      if (-not [string]::IsNullOrWhiteSpace($Entry.episode) -and $Entry.episode -ne "TBD") {
        $parts += "e$($Entry.episode)"
      }
    }
  }
  if (-not [string]::IsNullOrWhiteSpace($Entry.confidence)) {
    $parts += $Entry.confidence
  } elseif (-not [string]::IsNullOrWhiteSpace($Entry.status) -and $Entry.status -notin @("active", "current-at-boundary")) {
    $parts += $Entry.status
  }
  return ($parts -join " ")
}

function Format-AvailabilityHistory {
  param(
    [object[]]$Entries,
    [switch]$TimingSpoilerFree
  )

  $byMedium = [ordered]@{}
  foreach ($entry in @($Entries)) {
    if (-not (Test-AvailabilityVisible $entry $null)) {
      continue
    }
    if ($entry.medium -eq "donghua") {
      $hasDonghuaPosition = $false
      foreach ($key in @("season", "episode", "release_order")) {
        if (-not [string]::IsNullOrWhiteSpace($entry.$key) -and $entry.$key -ne "TBD") {
          $hasDonghuaPosition = $true
        }
      }
      if (-not $hasDonghuaPosition) {
        continue
      }
    }
    $line = Format-AvailabilityEntry $entry -TimingSpoilerFree:$TimingSpoilerFree
    if ([string]::IsNullOrWhiteSpace($line)) {
      continue
    }
    $medium = if ([string]::IsNullOrWhiteSpace($entry.medium)) { "unknown" } else { $entry.medium }
    if (-not $byMedium.Contains($medium)) {
      $byMedium[$medium] = @()
    }
    if ($byMedium[$medium] -notcontains $line) {
      $byMedium[$medium] += $line
    }
  }

  $lines = @()
  foreach ($medium in @($byMedium.Keys | Sort-Object)) {
    $history = $byMedium[$medium] -join " -> "
    if ($TimingSpoilerFree) {
      $lines += $history
    } else {
      $lines += "$medium $history"
    }
  }
  return ($lines -join "; ")
}

function Select-CurrentAvailability {
  param(
    [object[]]$Entries,
    [object]$Boundary
  )

  $visibleEntries = @($Entries | Where-Object { Test-AvailabilityVisible $_ $Boundary })
  if ($visibleEntries.Count -eq 0) {
    return $null
  }
  return $visibleEntries[$visibleEntries.Count - 1]
}

function Get-RelationshipScore {
  param([object]$Relationship)

  $score = 0
  if (-not [string]::IsNullOrWhiteSpace($Relationship.history_label)) { $score += 1000 }
  if (-not [string]::IsNullOrWhiteSpace($Relationship.projection_source)) { $score += 100 }
  if ($Relationship.projection_scope -eq "canonical") { $score += 10 }
  switch ($Relationship.confidence) {
    "confirmed" { $score += 3 }
    "strong-evidence" { $score += 2 }
    "strong-inference" { $score += 2 }
    "clue" { $score += 1 }
  }
  return $score
}

function Copy-Relationship {
  param([object]$Relationship)

  $copy = [ordered]@{}
  if ($Relationship -is [System.Collections.IDictionary]) {
    foreach ($key in $Relationship.Keys) {
      $copy[$key] = $Relationship[$key]
    }
  } else {
    foreach ($property in $Relationship.PSObject.Properties) {
      $copy[$property.Name] = $property.Value
    }
  }
  return [pscustomobject]$copy
}

function Select-RelationshipsForBoundary {
  param(
    [object[]]$Relationships,
    [object]$Boundary,
    [object[]]$VisibleNodeIds = @(),
    [object[]]$KnownNodeIds = @(),
    [hashtable]$DataProjections = @{},
    [switch]$TimingSpoilerFree
  )

  $visible = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($nodeId in @($VisibleNodeIds)) {
    [void]$visible.Add([string]$nodeId)
  }
  $known = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($nodeId in @($KnownNodeIds)) {
    [void]$known.Add([string]$nodeId)
  }
  $selected = @{}

  foreach ($relationship in @($Relationships)) {
    $sourceNode = Convert-SlugToNodeId $relationship.source
    $targetNode = Convert-SlugToNodeId $relationship.target
    if ($visible.Count -gt 0) {
      $hasHiddenKnownEndpoint = $false
      foreach ($nodeId in @($sourceNode, $targetNode)) {
        if (-not $visible.Contains($nodeId) -and $known.Contains($nodeId)) {
          $hasHiddenKnownEndpoint = $true
        }
      }
      if ($hasHiddenKnownEndpoint) {
        continue
      }
    }

    $rendered = Copy-Relationship $relationship
    $namespacedProjectionSource = "$($relationship.source)|$($relationship.projection_source)"
    if (-not [string]::IsNullOrWhiteSpace($relationship.projection_source) -and ($DataProjections.ContainsKey($namespacedProjectionSource) -or $DataProjections.ContainsKey($relationship.projection_source))) {
      if ($DataProjections.ContainsKey($namespacedProjectionSource)) {
        $availability = @($DataProjections[$namespacedProjectionSource])
      } else {
        $availability = @($DataProjections[$relationship.projection_source])
      }
      $current = Select-CurrentAvailability $availability $Boundary
      if ($null -eq $current) {
        continue
      }
      $rendered.medium = $current.medium
      $rendered.volume = $current.volume
      $rendered.chapter = $current.chapter
      $rendered.status = $current.status
      $rendered.confidence = $current.confidence
      $eligible = @($availability | Where-Object { Test-AvailabilityVisible $_ $Boundary })
      $rendered.history_label = Format-AvailabilityHistory $eligible -TimingSpoilerFree:$TimingSpoilerFree
    } elseif ($null -ne $Boundary -and -not (Test-PositionVisible $rendered.medium $rendered.volume $rendered.chapter $Boundary)) {
      continue
    }

    $key = "$($rendered.source)|$($rendered.relationship_type)|$($rendered.target)"
    if (-not $selected.ContainsKey($key) -or (Get-RelationshipScore $rendered) -gt (Get-RelationshipScore $selected[$key])) {
      $selected[$key] = $rendered
    }
  }

  return @($selected.Keys | Sort-Object | ForEach-Object { $selected[$_] })
}

function Get-MissingRelationshipEndpoints {
  param(
    [object[]]$Relationships,
    [object[]]$KnownNodeIds
  )

  $known = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($nodeId in @($KnownNodeIds)) {
    [void]$known.Add([string]$nodeId)
  }
  $missing = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($relationship in @($Relationships)) {
    foreach ($slug in @($relationship.source, $relationship.target)) {
      $nodeId = Convert-SlugToNodeId $slug
      if (-not $known.Contains($nodeId)) {
        [void]$missing.Add($nodeId)
      }
    }
  }
  return @($missing)
}

function Format-RelationshipLabel {
  param(
    [object]$Relationship,
    [switch]$TimingSpoilerFree
  )

  $parts = @($Relationship.relationship_type)
  if (-not [string]::IsNullOrWhiteSpace($Relationship.history_label)) {
    $parts += $Relationship.history_label
    return ($parts -join ' ')
  }
  if (-not $TimingSpoilerFree -and -not [string]::IsNullOrWhiteSpace($Relationship.chapter)) {
    $parts += "ch$($Relationship.chapter)"
  }

  if (-not [string]::IsNullOrWhiteSpace($Relationship.status) -and $Relationship.status -ne "active") {
    $parts += $Relationship.status
  }

  if (-not [string]::IsNullOrWhiteSpace($Relationship.confidence) -and $Relationship.confidence -ne "confirmed") {
    $parts += $Relationship.confidence
  }

  return ($parts -join ' ')
}

function Format-RelationshipNodeLabel {
  param(
    [object]$Relationship,
    [switch]$TimingSpoilerFree
  )

  if (-not [string]::IsNullOrWhiteSpace($Relationship.history_label)) {
    $parts = @($Relationship.relationship_type, $Relationship.history_label)
    return (($parts | ForEach-Object { $_ -replace '"', '\"' }) -join '<br/>')
  }

  $parts = @($Relationship.relationship_type)
  if (-not $TimingSpoilerFree -and -not [string]::IsNullOrWhiteSpace($Relationship.chapter)) {
    $parts += "ch$($Relationship.chapter)"
  }

  if (-not [string]::IsNullOrWhiteSpace($Relationship.status) -and $Relationship.status -ne "active") {
    $parts += $Relationship.status
  }

  if (-not [string]::IsNullOrWhiteSpace($Relationship.confidence) -and $Relationship.confidence -ne "confirmed") {
    $parts += $Relationship.confidence
  }

  return (($parts | ForEach-Object { $_ -replace '"', '\"' }) -join '<br/>')
}

function Write-MermaidGraph {
  param(
    [string]$GraphPath,
    [hashtable]$Nodes,
    [object[]]$Relationships,
    [switch]$TimingSpoilerFree,
    [object[]]$KnownNodeIds = $null,
    [object[]]$PendingNodeIds = @(),
    [object[]]$PendingEndpointNodeIds = @()
  )

  $known = New-Object 'System.Collections.Generic.HashSet[string]'
  if ($null -eq $KnownNodeIds) {
    foreach ($nodeId in $Nodes.Keys) {
      [void]$known.Add([string]$nodeId)
    }
  } else {
    foreach ($nodeId in $KnownNodeIds) {
      [void]$known.Add([string]$nodeId)
    }
  }
  $pendingNodes = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($nodeId in @($PendingNodeIds)) {
    [void]$pendingNodes.Add([string]$nodeId)
  }
  $pendingEndpointNodes = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($nodeId in @($PendingEndpointNodeIds)) {
    [void]$pendingEndpointNodes.Add([string]$nodeId)
  }
  $missingEndpointNodes = New-Object 'System.Collections.Generic.HashSet[string]'

  foreach ($relationship in $Relationships) {
    $source = Convert-SlugToNodeId $relationship.source
    $target = Convert-SlugToNodeId $relationship.target
    if (-not $known.Contains($source)) {
      [void]$missingEndpointNodes.Add($source)
    }
    if (-not $known.Contains($target)) {
      [void]$missingEndpointNodes.Add($target)
    }
    if (-not $Nodes.ContainsKey($source)) {
      $Nodes[$source] = Convert-NodeIdToFallbackLabel $source
    }
    if (-not $Nodes.ContainsKey($target)) {
      $Nodes[$target] = Convert-NodeIdToFallbackLabel $target
    }
  }

  $lines = @("graph TD")
  foreach ($nodeId in @($Nodes.Keys | Sort-Object)) {
    $label = $Nodes[$nodeId] -replace '"', '\"'
    $lines += ('  {0}["{1}"]' -f $nodeId, $label)
  }

  $lines += ""
  $lines += "  classDef artifact fill:#f3ead7,stroke:#b7791f,stroke-width:2px,color:#1f2937"
  $lines += "  classDef character fill:#ecebff,stroke:#7c5cff,stroke-width:2px,color:#1f2937"
  $lines += "  classDef concept fill:#e8f5f0,stroke:#2f855a,stroke-width:2px,color:#1f2937"
  $lines += "  classDef deity fill:#fae8ff,stroke:#c026d3,stroke-width:2px,color:#1f2937"
  $lines += "  classDef epoch fill:#ede9fe,stroke:#6d28d9,stroke-width:2px,color:#1f2937"
  $lines += "  classDef event fill:#fff1f2,stroke:#e11d48,stroke-width:2px,color:#1f2937"
  $lines += "  classDef faction fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#1f2937"
  $lines += "  classDef family fill:#fce7f3,stroke:#be185d,stroke-width:2px,color:#1f2937"
  $lines += "  classDef item fill:#ecfccb,stroke:#65a30d,stroke-width:2px,color:#1f2937"
  $lines += "  classDef location fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1f2937"
  $lines += "  classDef mystery fill:#e5e7eb,stroke:#4b5563,stroke-width:2px,color:#1f2937"
  $lines += "  classDef pathway fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#1f2937"
  $lines += "  classDef tarot fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#1f2937"
  $lines += "  classDef timeline fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1f2937"
  $lines += "  classDef uniqueness fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#1f2937"
  $lines += "  classDef missingEndpoint fill:#f8fafc,stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3,color:#1f2937"
  $lines += "  classDef pendingNode stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3"
  $lines += "  classDef pendingEndpoint fill:#f8fafc,stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3,color:#1f2937"
  $lines += "  classDef relationship fill:#f7f2e9,stroke:#c69245,stroke-width:1.5px,color:#1f2937"
  $lines += ""
  foreach ($nodeId in @($Nodes.Keys | Sort-Object)) {
    if ($missingEndpointNodes.Contains($nodeId)) {
      $className = if ($pendingEndpointNodes.Contains($nodeId)) { "pendingEndpoint" } else { "missingEndpoint" }
      $lines += ('  class {0} {1}' -f $nodeId, $className)
      continue
    }
    $className = ($nodeId -split '_')[0]
    if (@("artifact", "character", "concept", "deity", "epoch", "event", "faction", "family", "item", "location", "mystery", "pathway", "tarot", "timeline", "uniqueness") -contains $className) {
      $lines += ('  class {0} {1}' -f $nodeId, $className)
    }
    if ($pendingNodes.Contains($nodeId)) {
      $lines += ('  class {0} pendingNode' -f $nodeId)
    }
  }

  $lines += ""
  $seenEdges = New-Object 'System.Collections.Generic.HashSet[string]'
  $edges = @()

  foreach ($relationship in $Relationships) {
    $source = Convert-SlugToNodeId $relationship.source
    $target = Convert-SlugToNodeId $relationship.target

    $label = Format-RelationshipLabel $relationship -TimingSpoilerFree:$TimingSpoilerFree
    $key = "$source|$label|$target"
    if ($seenEdges.Add($key)) {
      $edges += [pscustomobject]@{
        source = $source
        target = $target
        label = $label
        nodeLabel = (Format-RelationshipNodeLabel $relationship -TimingSpoilerFree:$TimingSpoilerFree)
      }
    }
  }

  $relationshipIndex = 1
  foreach ($edge in @($edges | Sort-Object source,target,label)) {
    $relationshipId = 'rel_{0:d3}' -f $relationshipIndex
    $lines += ('  {0}["{1}"]' -f $relationshipId, $edge.nodeLabel)
    $lines += ('  class {0} relationship' -f $relationshipId)
    $lines += ('  {0} --> {1}' -f $edge.source, $relationshipId)
    $lines += ('  {0} --> {1}' -f $relationshipId, $edge.target)
    $relationshipIndex += 1
  }

  Set-Content -Path $GraphPath -Value $lines -Encoding UTF8
}

function Update-MermaidGraphs {
  param([object[]]$Views)

  $nodes = Read-GlossaryNodes
  $relationships = Read-RelationshipSeeds
  $dataProjections = Read-DataProjections
  $pendingNodeIds = @($nodes.Keys | Where-Object { $nodes[$_].status -eq "pending" })

  foreach ($view in $Views) {
    $graphPath = Resolve-RepoPath $view.input
    $timingSpoilerFree = $view.input -match 'timing-spoiler-free'
    $viewNodes = Select-NodesForBoundary $nodes $view.readerBoundary
    $viewRelationships = Select-RelationshipsForBoundary $relationships $view.readerBoundary @($viewNodes.Keys) @($nodes.Keys) $dataProjections -TimingSpoilerFree:$timingSpoilerFree
    $visiblePendingNodeIds = @($pendingNodeIds | Where-Object { $viewNodes.ContainsKey($_) })
    $pendingEndpointNodeIds = Get-MissingRelationshipEndpoints $viewRelationships @($nodes.Keys)
    Write-MermaidGraph $graphPath $viewNodes.Clone() $viewRelationships -TimingSpoilerFree:$timingSpoilerFree -KnownNodeIds @($nodes.Keys) -PendingNodeIds $visiblePendingNodeIds -PendingEndpointNodeIds $pendingEndpointNodeIds
  }
}

function Invoke-ManualRenderMode {
  param(
    [object]$Settings,
    [string]$PuppeteerConfig
  )

  if ([string]::IsNullOrWhiteSpace($InputPath)) {
    throw "Render mode requires -InputPath. Aliases: -Input, -Graph."
  }

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
    Invoke-MermaidRender $inputFullPath (Resolve-RepoPath $output) $Settings $PuppeteerConfig
  }
}

function Invoke-ValidateMode {
  param(
    [object]$Settings
  )

  $nodes = Read-GlossaryNodes
  $relationships = Read-RelationshipSeeds
  $dataProjections = Read-DataProjections
  $pendingNodeIds = @($nodes.Keys | Where-Object { $nodes[$_].status -eq "pending" })
  Write-Output ('Source parse: nodes={0} relationships={1}' -f $nodes.Count, $relationships.Count)

  $issues = @()
  foreach ($view in @($Settings.views)) {
    $graphPath = Resolve-RepoPath $view.input
    if (-not (Test-Path $graphPath)) {
      $issues += "Configured graph is missing: $($view.input)"
      continue
    }

    $classIssues = @(Get-MermaidClassValidation $graphPath $Settings)
    $layoutIssues = @(Get-MermaidLayoutValidation $graphPath $Settings)
    Write-Output ('Existing graph: {0} class_issues={1} layout_issues={2}' -f $view.input, $classIssues.Count, $layoutIssues.Count)
    $issues += $classIssues | ForEach-Object { "$($view.input): $_" }
    $issues += $layoutIssues | ForEach-Object { "$($view.input): $_" }
  }

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('lotm-visualization-validate-' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $tempRoot | Out-Null
  try {
    foreach ($view in @($Settings.views)) {
      $tempGraph = Join-Path $tempRoot ([System.IO.Path]::GetFileName($view.input))
      $timingSpoilerFree = $view.input -like '*timing-spoiler-free*'
      $viewNodes = Select-NodesForBoundary $nodes $view.readerBoundary
      $viewRelationships = Select-RelationshipsForBoundary $relationships $view.readerBoundary @($viewNodes.Keys) @($nodes.Keys) $dataProjections -TimingSpoilerFree:$timingSpoilerFree
      $visiblePendingNodeIds = @($pendingNodeIds | Where-Object { $viewNodes.ContainsKey($_) })
      $pendingEndpointNodeIds = Get-MissingRelationshipEndpoints $viewRelationships @($nodes.Keys)
      Write-MermaidGraph $tempGraph $viewNodes.Clone() $viewRelationships -TimingSpoilerFree:$timingSpoilerFree -KnownNodeIds @($nodes.Keys) -PendingNodeIds $visiblePendingNodeIds -PendingEndpointNodeIds $pendingEndpointNodeIds
      $classIssues = @(Get-MermaidClassValidation $tempGraph $Settings)
      $layoutIssues = @(Get-MermaidLayoutValidation $tempGraph $Settings)
      Write-Output ('Generated graph: {0} class_issues={1} layout_issues={2}' -f $view.input, $classIssues.Count, $layoutIssues.Count)
      $issues += $classIssues | ForEach-Object { "generated $($view.input): $_" }
      $issues += $layoutIssues | ForEach-Object { "generated $($view.input): $_" }
    }
  } finally {
    if (Test-Path $tempRoot) {
      Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
  }

  if ($issues.Count -gt 0) {
    throw ("Visualization validation failed:`n- " + ($issues -join "`n- "))
  }

  Write-Output "Visualization validation passed."
}

function Invoke-RefreshMode {
  param(
    [object]$Settings,
    [string]$PuppeteerConfig
  )

  Update-MermaidGraphs $Settings.views

  if (-not $SkipRender) {
    foreach ($view in $Settings.views) {
      foreach ($output in $view.outputs) {
        Invoke-MermaidRender (Resolve-RepoPath $view.input) (Resolve-RepoPath $output) $Settings $PuppeteerConfig
      }
    }
  }

  $viewStats = @()
  foreach ($view in $Settings.views) {
    $graphStats = Get-GraphStats (Resolve-RepoPath $view.input)
    $viewStats += [pscustomobject]@{
      name = $view.name
      input = $view.input
      nodes = @($graphStats.NodeIds)
      relationships = @($graphStats.Relationships | ForEach-Object {
        [pscustomobject]@{
          source = $_.source
          target = $_.target
          label = $_.label
          key = $_.key
          endpointKey = $_.endpointKey
        }
      })
      orphan_nodes = @($graphStats.OrphanNodes)
    }
  }

  $primaryView = $viewStats[0]
  $pendingNodes = Get-PendingGraphNodes
  $brokenLinks = Get-BrokenMarkdownLinks
  $renderedFiles = @()

  foreach ($view in $Settings.views) {
    foreach ($output in $view.outputs) {
      if (Test-Path (Resolve-RepoPath $output)) {
        $renderedFiles += $output
      }
    }
  }

  $reportPath = Resolve-RepoPath $Settings.reportPath
  $snapshotPath = Resolve-RepoPath $Settings.snapshotPath
  $previousSnapshot = Read-PreviousSnapshot $snapshotPath
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
  $snapshot = [pscustomobject]@{
    generated_at = $timestamp
    nodes = @($primaryView.nodes)
    relationships = @($primaryView.relationships)
    views = @($Settings.views | ForEach-Object { $_.name })
    view_stats = @($viewStats)
    rendered_files = @($renderedFiles)
    broken_links = @($brokenLinks)
    orphan_nodes = @($primaryView.orphan_nodes)
    pending_nodes = @($pendingNodes)
  }

  $previousViewCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.views).Count }
  $previousRenderedCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.rendered_files).Count }
  $previousBrokenLinkCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.broken_links).Count }
  $previousPendingCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.pending_nodes).Count }

  $viewsDelta = Format-SnapshotDelta $previousSnapshot $previousViewCount @($snapshot.views).Count
  $renderedDelta = Format-SnapshotDelta $previousSnapshot $previousRenderedCount @($snapshot.rendered_files).Count
  $brokenLinksDelta = Format-SnapshotDelta $previousSnapshot $previousBrokenLinkCount @($snapshot.broken_links).Count
  $pendingNodesDelta = Format-SnapshotDelta $previousSnapshot $previousPendingCount @($snapshot.pending_nodes).Count

  $previousViewStats = @{}
  if ($null -ne $previousSnapshot -and $null -ne $previousSnapshot.view_stats) {
    foreach ($view in @($previousSnapshot.view_stats)) {
      if (-not [string]::IsNullOrWhiteSpace($view.input)) {
        $previousViewStats[$view.input] = $view
      }
      if (-not [string]::IsNullOrWhiteSpace($view.name)) {
        $previousViewStats[$view.name] = $view
      }
    }
  }

  $viewReports = @()
  for ($index = 0; $index -lt $viewStats.Count; $index += 1) {
    $view = $viewStats[$index]
    $previousView = $null
    if ($previousViewStats.ContainsKey($view.input)) {
      $previousView = $previousViewStats[$view.input]
    } elseif ($previousViewStats.ContainsKey($view.name)) {
      $previousView = $previousViewStats[$view.name]
    } elseif ($index -eq 0 -and $null -ne $previousSnapshot) {
      $previousView = [pscustomobject]@{
        nodes = @($previousSnapshot.nodes)
        relationships = @($previousSnapshot.relationships)
        orphan_nodes = @($previousSnapshot.orphan_nodes)
      }
    } else {
      $previousView = [pscustomobject]@{
        nodes = @()
        relationships = @()
        orphan_nodes = @()
      }
    }

    $nodeDiff = Compare-StringSet @($previousView.nodes) @($view.nodes)
    $relationshipDiff = Compare-StringSet @($previousView.relationships | ForEach-Object { $_.key }) @($view.relationships | ForEach-Object { $_.key })
    $duplicateRelationships = Get-DuplicateRelationships @($view.relationships)
    $changedRelationships = if ($null -eq $previousSnapshot) { @() } else { Get-ChangedRelationships @($previousView.relationships) @($view.relationships) }

    $viewReports += [pscustomobject]@{
      view = $view
      previous = $previousView
      node_diff = $nodeDiff
      relationship_diff = $relationshipDiff
      duplicate_relationships = @($duplicateRelationships)
      changed_relationships = @($changedRelationships)
    }
  }

  $validationIssueCount = @($brokenLinks).Count
  foreach ($viewReport in $viewReports) {
    $validationIssueCount += @($viewReport.view.orphan_nodes).Count
    $validationIssueCount += @($viewReport.duplicate_relationships).Count
    $validationIssueCount += @($viewReport.relationship_diff.Removed).Count
  }

  $report = @()
  $report += "Last Updated: $timestamp"
  $report += ""
  $report += "### Summary"
  $report += ""
  $report += "| Metric | Count | Delta |"
  $report += "| --- | ---: | ---: |"
  $report += "| Views Updated | $($Settings.views.Count) | $viewsDelta |"
  $report += "| Rendered Files | $($renderedFiles.Count) | $renderedDelta |"
  $report += "| Broken Links | $($brokenLinks.Count) | $brokenLinksDelta |"
  $report += "| Pending Nodes | $($pendingNodes.Count) | $pendingNodesDelta |"
  $report += "| Validation Issues | $validationIssueCount | n/a |"
  $report += ""
  $report += "### View Summary"
  $report += ""
  $report += "| View | Nodes | Delta | Relationships | Delta | Orphan Nodes |"
  $report += "| --- | ---: | ---: | ---: | ---: | ---: |"
  foreach ($viewReport in $viewReports) {
    $view = $viewReport.view
    $previousView = $viewReport.previous
    $nodeDelta = Format-SnapshotDelta $previousSnapshot @($previousView.nodes).Count @($view.nodes).Count
    $relationshipDelta = Format-SnapshotDelta $previousSnapshot @($previousView.relationships).Count @($view.relationships).Count
    $report += "| $($view.name) | $(@($view.nodes).Count) | $nodeDelta | $(@($view.relationships).Count) | $relationshipDelta | $(@($view.orphan_nodes).Count) |"
  }
  $report += ""
  $report += "### Semantic Changes"
  $report += ""
  foreach ($viewReport in $viewReports) {
    $report += "#### $($viewReport.view.name)"
    $report += ""
    $report += "- Added nodes: $($viewReport.node_diff.Added.Count)"
    $report += "- Removed nodes: $($viewReport.node_diff.Removed.Count)"
    $report += "- Added relationships: $($viewReport.relationship_diff.Added.Count)"
    $report += "- Removed relationships: $($viewReport.relationship_diff.Removed.Count)"
    $report += "- Changed relationship labels: $($viewReport.changed_relationships.Count)"
    $report += "- Duplicate relationships: $($viewReport.duplicate_relationships.Count)"
    $report += ""
  }
  $report += "### Views"
  $report += ""
  foreach ($view in $Settings.views) {
    $report += ('- {0}: `{1}`' -f $view.name, $view.input)
  }
  $report += ""
  $report += "### Rendered Outputs"
  $report += ""
  foreach ($file in $renderedFiles) {
    $item = Get-Item (Resolve-RepoPath $file)
    $report += ('- `{0}` ({1} bytes)' -f $file, $item.Length)
  }
  $report += ""
  $report += "### Hygiene"
  $report += ""
  $report += "- Broken links: $($brokenLinks.Count)"
  $report += "- Orphan nodes: $(($viewReports | ForEach-Object { @($_.view.orphan_nodes).Count } | Measure-Object -Sum).Sum)"
  $report += "- Duplicate relationships: $(($viewReports | ForEach-Object { @($_.duplicate_relationships).Count } | Measure-Object -Sum).Sum)"
  $report += "- Removed relationships: $(($viewReports | ForEach-Object { @($_.relationship_diff.Removed).Count } | Measure-Object -Sum).Sum)"
  $report += "- Changed relationship labels: $(($viewReports | ForEach-Object { @($_.changed_relationships).Count } | Measure-Object -Sum).Sum)"
  $report += "- Pending graph nodes: $($pendingNodes.Count)"

  foreach ($viewReport in $viewReports) {
    $viewName = $viewReport.view.name
    $sections = @(
      [pscustomobject]@{ Title = "Added Nodes"; Items = @($viewReport.node_diff.Added) },
      [pscustomobject]@{ Title = "Removed Nodes"; Items = @($viewReport.node_diff.Removed) },
      [pscustomobject]@{ Title = "Added Relationships"; Items = @($viewReport.relationship_diff.Added) },
      [pscustomobject]@{ Title = "Removed Relationships"; Items = @($viewReport.relationship_diff.Removed) },
      [pscustomobject]@{ Title = "Duplicate Relationships"; Items = @($viewReport.duplicate_relationships) },
      [pscustomobject]@{ Title = "Orphan Nodes"; Items = @($viewReport.view.orphan_nodes) }
    )
    foreach ($section in $sections) {
      if ($section.Items.Count -gt 0) {
        $report += ""
        $report += "#### $viewName - $($section.Title)"
        $report += ""
        foreach ($item in $section.Items) {
          $report += ('- `{0}`' -f $item)
        }
      }
    }

    if ($viewReport.changed_relationships.Count -gt 0) {
      $report += ""
      $report += "#### $viewName - Changed Relationship Labels"
      $report += ""
      foreach ($relationship in $viewReport.changed_relationships) {
        $report += ('- `{0}` -> `{1}` changed from `{2}` to `{3}`' -f $relationship.source, $relationship.target, $relationship.previous, $relationship.current)
      }
    }
  }

  if ($brokenLinks.Count -gt 0) {
    $report += ""
    $report += "#### Broken Links"
    $report += ""
    foreach ($link in $brokenLinks) {
      $report += "- $link"
    }
  }

  if ($pendingNodes.Count -gt 0) {
    $report += ""
    $report += "#### Pending Nodes"
    $report += ""
    foreach ($node in $pendingNodes) {
      $report += ('- `{0}`' -f $node)
    }
  }

  Update-ReportSection $reportPath $report
  $snapshot | ConvertTo-Json -Depth 10 | Set-Content -Path $snapshotPath -Encoding UTF8
  Write-Output "Visualization refresh tracker updated in $($Settings.reportPath)"
}

$Mode = Resolve-VisualizationMode $Mode
$settingsFullPath = Resolve-RepoPath $SettingsPath
$settings = Get-Content $settingsFullPath -Raw | ConvertFrom-Json
$puppeteerConfig = Resolve-RepoPath $settings.puppeteerConfig

if ($Mode -eq "Render") {
  Invoke-ManualRenderMode $settings $puppeteerConfig
} elseif ($Mode -eq "Validate") {
  Invoke-ValidateMode $settings
} else {
  Invoke-RefreshMode $settings $puppeteerConfig
}
