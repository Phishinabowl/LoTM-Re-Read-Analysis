param(
  [string]$SettingsPath = "Visualization/config/render-settings.json",
  [switch]$SkipRender
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

function Resolve-RepoPath {
  param([string]$Path)
  return (Join-Path $repoRoot $Path)
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

  foreach ($line in Get-Content $GraphPath) {
    if ($line -match '^\s+([A-Za-z0-9_]+)\["') {
      [void]$nodes.Add($matches[1])
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
    }
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
      $pending += $matches[1].Trim()
    }
  }

  return $pending
}

function Get-BrokenMarkdownLinks {
  $broken = @()
  $markdownFiles = Get-ChildItem -Recurse -Filter "*.md" |
    Where-Object {
      $_.FullName -notmatch '\\.git\\' -and
      $_.FullName -notmatch '\\Source\\'
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
        $relativeFile = Resolve-Path -Relative $file.FullName
        $broken += "$relativeFile -> $target"
      }
    }
  }

  return $broken
}

$settingsFullPath = Resolve-RepoPath $SettingsPath
$settings = Get-Content $settingsFullPath -Raw | ConvertFrom-Json
$puppeteerConfig = Resolve-RepoPath $settings.puppeteerConfig

if (-not $SkipRender) {
  foreach ($view in $settings.views) {
    foreach ($output in $view.outputs) {
      $args = @(
        "-p", $puppeteerConfig,
        "-i", (Resolve-RepoPath $view.input),
        "-o", (Resolve-RepoPath $output),
        "-b", $settings.background,
        "-w", $settings.width,
        "-H", $settings.height
      )

      if ([System.IO.Path]::GetExtension($output).ToLowerInvariant() -eq ".png") {
        $args += @("-s", $settings.pngScale)
      }

      & mmdc @args
    }
  }
}

$primaryGraph = Resolve-RepoPath $settings.views[0].input
$stats = Get-GraphStats $primaryGraph
$pendingNodes = Get-PendingGraphNodes
$brokenLinks = Get-BrokenMarkdownLinks
$renderedFiles = @()

foreach ($view in $settings.views) {
  foreach ($output in $view.outputs) {
    if (Test-Path (Resolve-RepoPath $output)) {
      $renderedFiles += $output
    }
  }
}

$reportPath = Resolve-RepoPath $settings.reportPath
$snapshotPath = Resolve-RepoPath $settings.snapshotPath
$previousSnapshot = Read-PreviousSnapshot $snapshotPath
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$snapshot = New-GraphSnapshot $stats $settings.views $renderedFiles $brokenLinks $pendingNodes $timestamp

$previousNodeCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.nodes).Count }
$previousRelationshipCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.relationships).Count }
$previousViewCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.views).Count }
$previousRenderedCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.rendered_files).Count }
$previousBrokenLinkCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.broken_links).Count }
$previousOrphanCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.orphan_nodes).Count }
$previousPendingCount = if ($null -eq $previousSnapshot) { 0 } else { @($previousSnapshot.pending_nodes).Count }

$nodesDelta = Format-SnapshotDelta $previousSnapshot $previousNodeCount @($snapshot.nodes).Count
$relationshipsDelta = Format-SnapshotDelta $previousSnapshot $previousRelationshipCount @($snapshot.relationships).Count
$viewsDelta = Format-SnapshotDelta $previousSnapshot $previousViewCount @($snapshot.views).Count
$renderedDelta = Format-SnapshotDelta $previousSnapshot $previousRenderedCount @($snapshot.rendered_files).Count
$brokenLinksDelta = Format-SnapshotDelta $previousSnapshot $previousBrokenLinkCount @($snapshot.broken_links).Count
$orphanNodesDelta = Format-SnapshotDelta $previousSnapshot $previousOrphanCount @($snapshot.orphan_nodes).Count
$pendingNodesDelta = Format-SnapshotDelta $previousSnapshot $previousPendingCount @($snapshot.pending_nodes).Count

$nodeDiff = if ($null -eq $previousSnapshot) { Compare-StringSet @() @($snapshot.nodes) } else { Compare-StringSet @($previousSnapshot.nodes) @($snapshot.nodes) }
$relationshipDiff = if ($null -eq $previousSnapshot) { Compare-StringSet @() @($snapshot.relationships | ForEach-Object { $_.key }) } else { Compare-StringSet @($previousSnapshot.relationships | ForEach-Object { $_.key }) @($snapshot.relationships | ForEach-Object { $_.key }) }
$duplicateRelationships = Get-DuplicateRelationships @($snapshot.relationships)
$changedRelationships = if ($null -eq $previousSnapshot) { @() } else { Get-ChangedRelationships @($previousSnapshot.relationships) @($snapshot.relationships) }

$validationIssueCount = @($brokenLinks).Count + @($stats.OrphanNodes).Count + @($duplicateRelationships).Count + @($relationshipDiff.Removed).Count + @($changedRelationships).Count

$report = @()
$report += "Last Updated: $timestamp"
$report += ""
$report += "### Summary"
$report += ""
$report += "| Metric | Count | Delta |"
$report += "| --- | ---: | ---: |"
$report += "| Nodes | $(@($snapshot.nodes).Count) | $nodesDelta |"
$report += "| Relationships | $(@($snapshot.relationships).Count) | $relationshipsDelta |"
$report += "| Views Updated | $($settings.views.Count) | $viewsDelta |"
$report += "| Rendered Files | $($renderedFiles.Count) | $renderedDelta |"
$report += "| Broken Links | $($brokenLinks.Count) | $brokenLinksDelta |"
$report += "| Orphan Nodes | $($stats.OrphanNodes.Count) | $orphanNodesDelta |"
$report += "| Pending Nodes | $($pendingNodes.Count) | $pendingNodesDelta |"
$report += "| Validation Issues | $validationIssueCount | n/a |"
$report += ""
$report += "### Semantic Changes"
$report += ""
$report += "- Added nodes: $($nodeDiff.Added.Count)"
$report += "- Removed nodes: $($nodeDiff.Removed.Count)"
$report += "- Added relationships: $($relationshipDiff.Added.Count)"
$report += "- Removed relationships: $($relationshipDiff.Removed.Count)"
$report += "- Changed relationship labels: $($changedRelationships.Count)"
$report += "- Duplicate relationships: $($duplicateRelationships.Count)"
$report += ""
$report += "### Views"
$report += ""
foreach ($view in $settings.views) {
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
$report += "- Orphan nodes: $($stats.OrphanNodes.Count)"
$report += "- Duplicate relationships: $($duplicateRelationships.Count)"
$report += "- Removed relationships: $($relationshipDiff.Removed.Count)"
$report += "- Changed relationship labels: $($changedRelationships.Count)"
$report += "- Pending graph nodes: $($pendingNodes.Count)"

if ($nodeDiff.Added.Count -gt 0) {
  $report += ""
  $report += "#### Added Nodes"
  $report += ""
  foreach ($node in $nodeDiff.Added) {
    $report += ('- `{0}`' -f $node)
  }
}

if ($nodeDiff.Removed.Count -gt 0) {
  $report += ""
  $report += "#### Removed Nodes"
  $report += ""
  foreach ($node in $nodeDiff.Removed) {
    $report += ('- `{0}`' -f $node)
  }
}

if ($relationshipDiff.Added.Count -gt 0) {
  $report += ""
  $report += "#### Added Relationships"
  $report += ""
  foreach ($relationship in $relationshipDiff.Added) {
    $report += ('- `{0}`' -f $relationship)
  }
}

if ($relationshipDiff.Removed.Count -gt 0) {
  $report += ""
  $report += "#### Removed Relationships"
  $report += ""
  foreach ($relationship in $relationshipDiff.Removed) {
    $report += ('- `{0}`' -f $relationship)
  }
}

if ($changedRelationships.Count -gt 0) {
  $report += ""
  $report += "#### Changed Relationship Labels"
  $report += ""
  foreach ($relationship in $changedRelationships) {
    $report += ('- `{0}` -> `{1}` changed from `{2}` to `{3}`' -f $relationship.source, $relationship.target, $relationship.previous, $relationship.current)
  }
}

if ($duplicateRelationships.Count -gt 0) {
  $report += ""
  $report += "#### Duplicate Relationships"
  $report += ""
  foreach ($relationship in $duplicateRelationships) {
    $report += ('- `{0}`' -f $relationship)
  }
}

if ($stats.OrphanNodes.Count -gt 0) {
  $report += ""
  $report += "#### Orphan Nodes"
  $report += ""
  foreach ($node in $stats.OrphanNodes) {
    $report += ('- `{0}`' -f $node)
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
Write-Output "Visualization refresh tracker updated in $($settings.reportPath)"
