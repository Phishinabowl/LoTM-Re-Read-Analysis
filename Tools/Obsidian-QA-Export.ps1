param(
  [string]$Root = ".",
  [string]$OutputDir = "Obsidian_Export",
  [switch]$IncludeStubs,
  [switch]$Clean,
  [switch]$Json,
  [string[]]$BoundedGraph = @(),
  [string[]]$BoundedPage = @()
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$TypeFolders = @{
  "artifact" = "Artifacts"
  "character" = "Characters"
  "concept" = "Concepts"
  "event" = "Events"
  "faction" = "Factions"
  "item" = "Items"
  "knowledge source" = "Knowledge_Sources"
  "location" = "Locations"
  "pathway" = "Pathways"
  "uniqueness" = "Uniquenesses"
  "volume summary" = "Volumes"
}

$ReciprocalTypes = @{
  "superior" = "subordinate"
  "subordinate" = "superior"
  "mentor" = "student"
  "student" = "mentor"
  "investigates" = "investigated-by"
  "investigated-by" = "investigates"
}

$SlugPrefixes = @(
  "artifact",
  "character",
  "concept",
  "deity",
  "event",
  "faction",
  "item",
  "source",
  "location",
  "pathway",
  "tarot-card",
  "uniqueness"
)

$SlugPattern = "\b(?:" + (($SlugPrefixes | ForEach-Object { [regex]::Escape($_) }) -join "|") + ")-[a-z0-9][a-z0-9-]*\b"
$DataReferenceKeys = New-Object 'System.Collections.Generic.HashSet[string]'
@(
  "",
  "artifact",
  "character",
  "concept",
  "concept_index",
  "dedicated_article",
  "entity",
  "event",
  "faction",
  "item",
  "file",
  "location",
  "pathway",
  "provider",
  "related_ats_formula",
  "related_deity",
  "reader",
  "source",
  "source_node",
  "target"
) | ForEach-Object { [void]$DataReferenceKeys.Add($_) }

function Read-TextFile {
  param([string]$Path)
  return [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($true))
}

function Write-TextFile {
  param(
    [string]$Path,
    [string]$Value
  )
  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllText($Path, $Value, $utf8NoBom)
}

function ConvertTo-RelativePath {
  param(
    [string]$Path,
    [string]$BasePath
  )
  $baseUri = [System.Uri]::new((Resolve-Path -LiteralPath $BasePath).Path.TrimEnd('\') + '\')
  $pathUri = [System.Uri]::new((Resolve-Path -LiteralPath $Path).Path)
  return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString())
}

function ConvertTo-SlugTitle {
  param([string]$Slug)
  $prefixPattern = "^(?:" + (($SlugPrefixes | ForEach-Object { [regex]::Escape($_) }) -join "|") + ")-"
  $cleaned = $Slug -replace $prefixPattern, ""
  return (($cleaned -split "-" | Where-Object { $_ } | ForEach-Object {
    if ($_.Length -le 1) { $_.ToUpperInvariant() } else { $_.Substring(0, 1).ToUpperInvariant() + $_.Substring(1) }
  }) -join " ")
}

function Get-FirstHeading {
  param(
    [string]$Text,
    [string]$Fallback
  )
  foreach ($line in $Text -split "`r?`n") {
    if ($line.StartsWith("# ")) {
      $heading = $line.Substring(2).Trim()
      if (-not [string]::IsNullOrWhiteSpace($heading)) {
        return $heading
      }
    }
  }
  return $Fallback
}

function Get-MarkdownSection {
  param(
    [string]$Text,
    [string]$Heading
  )
  $pattern = "(?m)^## " + [regex]::Escape($Heading) + "\s*$"
  $match = [regex]::Match($Text, $pattern)
  if (-not $match.Success) {
    return ""
  }
  $start = $match.Index + $match.Length
  $remaining = $Text.Substring($start)
  $next = [regex]::Match($remaining, "(?m)^##\s+")
  $end = if ($next.Success) { $start + $next.Index } else { $Text.Length }
  return $Text.Substring($start, $end - $start).Trim()
}

function Get-Metadata {
  param([string]$Text)
  $metadata = [ordered]@{}
  foreach ($line in (Get-MarkdownSection $Text "Metadata") -split "`r?`n") {
    if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith("-") -or -not $line.Contains(":")) {
      continue
    }
    $parts = $line.Split(":", 2)
    $key = $parts[0].Trim().ToLowerInvariant().Replace(" ", "_")
    $value = $parts[1].Trim()
    if ($key -and $value) {
      $metadata[$key] = $value
    }
  }
  return $metadata
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

function Get-FencedYamlBlocks {
  param([string]$Text)
  $blocks = @()
  $index = 1
  foreach ($match in [regex]::Matches($Text, '```yaml\s*(.*?)```', [System.Text.RegularExpressions.RegexOptions]::Singleline)) {
    $blocks += [pscustomobject]@{
      Name = "yaml-block-$index"
      Text = $match.Groups[1].Value.Trim()
    }
    $index += 1
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

function New-Relationship {
  param(
    [hashtable]$Data,
    [string]$SourceFile
  )
  return [pscustomobject]@{
    source = if ($Data.ContainsKey("source")) { $Data["source"] } else { "" }
    target = if ($Data.ContainsKey("target")) { $Data["target"] } else { "" }
    relationship_type = if ($Data.ContainsKey("relationship_type")) { $Data["relationship_type"] } else { "" }
    status = if ($Data.ContainsKey("status")) { $Data["status"] } else { "" }
    confidence = if ($Data.ContainsKey("confidence")) { $Data["confidence"] } else { "" }
    notes = if ($Data.ContainsKey("notes")) { $Data["notes"] } else { "" }
    source_file = $SourceFile
    start_medium = if ($Data.ContainsKey("start_medium")) { $Data["start_medium"] } else { "" }
    start_volume = if ($Data.ContainsKey("start_volume")) { $Data["start_volume"] } else { "" }
    start_chapter = if ($Data.ContainsKey("start_chapter")) { $Data["start_chapter"] } else { "" }
    projection_source = if ($Data.ContainsKey("projection_source")) { $Data["projection_source"] } else { "" }
  }
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
  foreach ($field in @("target", "ability", "event", "pathway", "organization", "item", "source", "source_unit_id", "batch_id", "fragment_id", "label", "field", "entity", "uniqueness")) {
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
    status = if ($Data.ContainsKey("status")) { $Data["status"] } elseif ($Data.ContainsKey("possession_status")) { $Data["possession_status"] } elseif ($Data.ContainsKey("access_status")) { $Data["access_status"] } elseif ($Data.ContainsKey("outcome_status")) { $Data["outcome_status"] } else { "" }
    confidence = if ($Data.ContainsKey("confidence")) { $Data["confidence"] } else { "" }
    graph_visibility = if ($Data.ContainsKey("graph_visibility")) { $Data["graph_visibility"] } else { "" }
    adaptation_relationship = if ($Data.ContainsKey("adaptation_relationship")) { $Data["adaptation_relationship"] } else { "" }
  }
}

function Get-DataProjections {
  param(
    [string]$Text,
    [string]$NoteSlug
  )
  $projections = @{}
  $relationshipBlock = Get-RelationshipYaml $Text

  foreach ($block in Get-FencedYamlBlocks $Text) {
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

    function Finish-ProjectionRow {
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
        $projection = [pscustomobject]@{
          source_slug = $NoteSlug
          projection_source = $projectionSource
          availability = @($Availability)
        }
        $Projections["$NoteSlug|$projectionSource"] = $projection
        if (-not $Projections.ContainsKey($projectionSource)) {
          $Projections[$projectionSource] = $projection
        }
      }
    }

    foreach ($rawLine in $block.Text -split "`r?`n") {
      if ([string]::IsNullOrWhiteSpace($rawLine) -or -not $rawLine.Contains(":")) {
        continue
      }
      $indent = $rawLine.Length - $rawLine.TrimStart(" ").Length
      $line = $rawLine.Trim()

      if ($indent -eq 0 -and -not $line.StartsWith("- ")) {
        if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
        Finish-ProjectionRow $rootKey $sectionKey $NoteSlug $row $availability $projections
        $row = $null; $availability = @(); $availabilityItem = $null; $inAvailability = $false; $inFrom = $false
        $parts = $line.Split(":", 2)
        $rootKey = if ((ConvertFrom-Scalar $parts[1]) -eq "") { $parts[0].Trim() } else { "" }
        $sectionKey = ""
        continue
      }

      if ($rootKey -and $indent -eq 2 -and -not $line.StartsWith("- ")) {
        if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
        Finish-ProjectionRow $rootKey $sectionKey $NoteSlug $row $availability $projections
        $row = $null; $availability = @(); $availabilityItem = $null; $inAvailability = $false; $inFrom = $false
        $parts = $line.Split(":", 2)
        $sectionKey = if ((ConvertFrom-Scalar $parts[1]) -eq "") { $parts[0].Trim() } else { "" }
        continue
      }

      if ($rootKey -and $sectionKey -and $indent -eq 4 -and $line.StartsWith("- ")) {
        if ($null -ne $availabilityItem) { $availability += @(New-AvailabilityEntry $availabilityItem) }
        Finish-ProjectionRow $rootKey $sectionKey $NoteSlug $row $availability $projections
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
          foreach ($mappingKey in (ConvertFrom-InlineMapping $value).Keys) {
            $availabilityItem["from_$mappingKey"] = (ConvertFrom-InlineMapping $value)[$mappingKey]
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
    Finish-ProjectionRow $rootKey $sectionKey $NoteSlug $row $availability $projections
  }

  return $projections
}

function Get-FirstAppearanceBeats {
  param([string]$Text)

  $beats = @()
  $relationshipBlock = Get-RelationshipYaml $Text

  foreach ($block in Get-FencedYamlBlocks $Text) {
    if ($relationshipBlock -and $block.Text -eq $relationshipBlock) {
      continue
    }

    $rootKey = ""
    $sectionKey = ""
    $row = $null
    $position = @{}
    $graphDisplay = @{}
    $context = ""

    foreach ($rawLine in $block.Text -split "`r?`n") {
      if ([string]::IsNullOrWhiteSpace($rawLine) -or -not $rawLine.Contains(":")) {
        continue
      }
      $indent = $rawLine.Length - $rawLine.TrimStart(" ").Length
      $line = $rawLine.Trim()

      if ($indent -eq 0 -and -not $line.StartsWith("- ")) {
        if ($null -ne $row) {
          $beats += [pscustomobject]@{
            medium = if ($row.ContainsKey("medium")) { $row["medium"] } else { "" }
            beat_type = if ($row.ContainsKey("beat_type")) { $row["beat_type"] } else { "" }
            title = if ($row.ContainsKey("title")) { $row["title"] } else { "" }
            position = $position.Clone()
            reader_knowledge_state = if ($row.ContainsKey("reader_knowledge_state")) { $row["reader_knowledge_state"] } else { "" }
            viewer_knowledge_state = if ($row.ContainsKey("viewer_knowledge_state")) { $row["viewer_knowledge_state"] } else { "" }
            graph_behavior = if ($graphDisplay.ContainsKey("behavior")) { $graphDisplay["behavior"] } else { "" }
            graph_label = if ($graphDisplay.ContainsKey("label")) { $graphDisplay["label"] } else { "" }
            status = if ($row.ContainsKey("status")) { $row["status"] } else { "" }
            confidence = if ($row.ContainsKey("confidence")) { $row["confidence"] } else { "" }
          }
        }
        $row = $null; $position = @{}; $graphDisplay = @{}; $context = ""
        $parts = $line.Split(":", 2)
        $rootKey = if ((ConvertFrom-Scalar $parts[1]) -eq "") { $parts[0].Trim() } else { "" }
        $sectionKey = ""
        continue
      }

      if ($rootKey -and $indent -eq 2 -and -not $line.StartsWith("- ")) {
        if ($null -ne $row) {
          $beats += [pscustomobject]@{
            medium = if ($row.ContainsKey("medium")) { $row["medium"] } else { "" }
            beat_type = if ($row.ContainsKey("beat_type")) { $row["beat_type"] } else { "" }
            title = if ($row.ContainsKey("title")) { $row["title"] } else { "" }
            position = $position.Clone()
            reader_knowledge_state = if ($row.ContainsKey("reader_knowledge_state")) { $row["reader_knowledge_state"] } else { "" }
            viewer_knowledge_state = if ($row.ContainsKey("viewer_knowledge_state")) { $row["viewer_knowledge_state"] } else { "" }
            graph_behavior = if ($graphDisplay.ContainsKey("behavior")) { $graphDisplay["behavior"] } else { "" }
            graph_label = if ($graphDisplay.ContainsKey("label")) { $graphDisplay["label"] } else { "" }
            status = if ($row.ContainsKey("status")) { $row["status"] } else { "" }
            confidence = if ($row.ContainsKey("confidence")) { $row["confidence"] } else { "" }
          }
        }
        $row = $null; $position = @{}; $graphDisplay = @{}; $context = ""
        $parts = $line.Split(":", 2)
        $sectionKey = if ((ConvertFrom-Scalar $parts[1]) -eq "") { $parts[0].Trim() } else { "" }
        continue
      }

      if ($rootKey -and $sectionKey -eq "first_appearance_beats" -and $indent -eq 4 -and $line.StartsWith("- ")) {
        if ($null -ne $row) {
          $beats += [pscustomobject]@{
            medium = if ($row.ContainsKey("medium")) { $row["medium"] } else { "" }
            beat_type = if ($row.ContainsKey("beat_type")) { $row["beat_type"] } else { "" }
            title = if ($row.ContainsKey("title")) { $row["title"] } else { "" }
            position = $position.Clone()
            reader_knowledge_state = if ($row.ContainsKey("reader_knowledge_state")) { $row["reader_knowledge_state"] } else { "" }
            viewer_knowledge_state = if ($row.ContainsKey("viewer_knowledge_state")) { $row["viewer_knowledge_state"] } else { "" }
            graph_behavior = if ($graphDisplay.ContainsKey("behavior")) { $graphDisplay["behavior"] } else { "" }
            graph_label = if ($graphDisplay.ContainsKey("label")) { $graphDisplay["label"] } else { "" }
            status = if ($row.ContainsKey("status")) { $row["status"] } else { "" }
            confidence = if ($row.ContainsKey("confidence")) { $row["confidence"] } else { "" }
          }
        }
        $row = @{}; $position = @{}; $graphDisplay = @{}; $context = ""
        $line = $line.Substring(2).Trim()
        if (-not $line.Contains(":")) {
          continue
        }
      }

      if ($null -eq $row -or $sectionKey -ne "first_appearance_beats") {
        continue
      }

      $parts = $line.Split(":", 2)
      $key = $parts[0].Trim().TrimStart("-").Trim()
      $value = ConvertFrom-Scalar $parts[1]

      if ($indent -eq 4) {
        $row[$key] = $value
        $context = ""
      } elseif ($indent -eq 6) {
        if ($key -in @("position", "graph_display")) {
          $context = $key
          $mapping = ConvertFrom-InlineMapping $value
          foreach ($mappingKey in $mapping.Keys) {
            if ($key -eq "position") {
              $position[$mappingKey] = $mapping[$mappingKey]
            } else {
              $graphDisplay[$mappingKey] = $mapping[$mappingKey]
            }
          }
          continue
        }
        $row[$key] = $value
        $context = ""
      } elseif ($indent -ge 8) {
        if ($context -eq "position") {
          $position[$key] = $value
        } elseif ($context -eq "graph_display") {
          $graphDisplay[$key] = $value
        }
      }
    }

    if ($null -ne $row) {
      $beats += [pscustomobject]@{
        medium = if ($row.ContainsKey("medium")) { $row["medium"] } else { "" }
        beat_type = if ($row.ContainsKey("beat_type")) { $row["beat_type"] } else { "" }
        title = if ($row.ContainsKey("title")) { $row["title"] } else { "" }
        position = $position.Clone()
        reader_knowledge_state = if ($row.ContainsKey("reader_knowledge_state")) { $row["reader_knowledge_state"] } else { "" }
        viewer_knowledge_state = if ($row.ContainsKey("viewer_knowledge_state")) { $row["viewer_knowledge_state"] } else { "" }
        graph_behavior = if ($graphDisplay.ContainsKey("behavior")) { $graphDisplay["behavior"] } else { "" }
        graph_label = if ($graphDisplay.ContainsKey("label")) { $graphDisplay["label"] } else { "" }
        status = if ($row.ContainsKey("status")) { $row["status"] } else { "" }
        confidence = if ($row.ContainsKey("confidence")) { $row["confidence"] } else { "" }
      }
    }
  }

  return @($beats)
}

function Get-RelationshipsFromYaml {
  param(
    [string]$Block,
    [string]$SourceFile
  )
  $relationships = @()
  $current = $null
  $nestedKey = ""

  foreach ($rawLine in $Block -split "`r?`n") {
    if ([string]::IsNullOrWhiteSpace($rawLine) -or $rawLine.Trim() -eq "relationships:") {
      continue
    }
    $indent = $rawLine.Length - $rawLine.TrimStart(" ").Length
    $line = $rawLine.Trim()

    if ($line.StartsWith("- ")) {
      if ($null -ne $current) {
        $relationships += (New-Relationship $current $SourceFile)
      }
      $current = @{}
      $nestedKey = ""
      $line = $line.Substring(2).Trim()
      if (-not $line) {
        continue
      }
    }

    if ($null -eq $current -or -not $line.Contains(":")) {
      continue
    }

    $parts = $line.Split(":", 2)
    $key = $parts[0].Trim()
    $value = ConvertFrom-Scalar $parts[1]

    if ($indent -le 4) {
      if ($value -eq "") {
        $nestedKey = $key
      } else {
        $nestedKey = ""
        $current[$key] = $value
      }
    } elseif ($nestedKey) {
      $current["${nestedKey}_${key}"] = $value
    } else {
      $current[$key] = $value
    }
  }

  if ($null -ne $current) {
    $relationships += (New-Relationship $current $SourceFile)
  }
  return @($relationships | Where-Object { $_.source -or $_.target })
}

function Get-SlugCandidatesFromYamlValue {
  param([string]$Value)
  $value = (ConvertFrom-Scalar $Value).Trim()
  if (-not $value -or $value.StartsWith("{") -or $value.StartsWith("[")) {
    return @()
  }
  if ([regex]::IsMatch($value, "^$SlugPattern$")) {
    return @($value)
  }
  $pathMatch = [regex]::Match($value, "(?:^|/|\\)($SlugPattern)\.md$")
  if ($pathMatch.Success) {
    return @($pathMatch.Groups[1].Value)
  }
  return @()
}

function Get-DataReferences {
  param(
    [string]$Text,
    [string]$NoteSlug,
    [string]$SourceFile
  )
  $refs = @{}
  $relationshipBlock = Get-RelationshipYaml $Text
  foreach ($block in Get-FencedYamlBlocks $Text) {
    if ($relationshipBlock -and $block.Text -eq $relationshipBlock) {
      continue
    }
    foreach ($rawLine in $block.Text -split "`r?`n") {
      $line = $rawLine.Trim()
      $key = ""
      $candidates = @()
      if ($line.Contains(":")) {
        $parts = $line.Split(":", 2)
        $key = $parts[0].Trim().TrimStart("-").Trim()
        $candidates = @(Get-SlugCandidatesFromYamlValue $parts[1])
      } elseif ($line.StartsWith("- ")) {
        $candidates = @(Get-SlugCandidatesFromYamlValue $line.Substring(2))
      }

      if (-not $DataReferenceKeys.Contains($key)) {
        continue
      }

      foreach ($slug in $candidates) {
        if ($slug -eq $NoteSlug) {
          continue
        }
        $refKey = "$NoteSlug|$slug|$SourceFile|$($block.Name)|$key"
        $refs[$refKey] = [pscustomobject]@{
          source = $NoteSlug
          target = $slug
          source_file = $SourceFile
          yaml_block = $block.Name
          context_key = $key
        }
      }
    }
  }
  return @($refs.Values | Sort-Object target,yaml_block,context_key)
}

function Get-ExportFolder {
  param([string]$TypeName)
  $key = $TypeName.ToLowerInvariant()
  if ($TypeFolders.ContainsKey($key)) {
    return $TypeFolders[$key]
  }
  return "Other"
}

function ConvertTo-SafeFileName {
  param([string]$Name)
  $invalidChars = [System.IO.Path]::GetInvalidFileNameChars()
  $builder = [System.Text.StringBuilder]::new()
  foreach ($char in $Name.ToCharArray()) {
    if ($invalidChars -contains $char) {
      [void]$builder.Append("-")
    } else {
      [void]$builder.Append($char)
    }
  }
  $safeName = [regex]::Replace($builder.ToString(), "\s+", " ").Trim().TrimEnd(".")
  if ([string]::IsNullOrWhiteSpace($safeName)) {
    return "Untitled"
  }
  return $safeName
}

function ConvertTo-SafeSlug {
  param(
    [string]$Value,
    [string]$Fallback
  )
  $cleaned = [regex]::Replace($Value.Trim(), "[^A-Za-z0-9._-]+", "-").Trim("-._")
  if ([string]::IsNullOrWhiteSpace($cleaned)) {
    return $Fallback
  }
  return $cleaned
}

function ConvertTo-BoolValue {
  param([string]$Value)
  $normalized = $Value.Trim().ToLowerInvariant()
  if ($normalized -in @("1", "true", "yes", "y", "on")) {
    return $true
  }
  if ($normalized -in @("0", "false", "no", "n", "off")) {
    return $false
  }
  throw "Expected boolean value, got: $Value"
}

function ConvertFrom-BoundedGraphSpec {
  param(
    [string]$Spec,
    [int]$Index
  )
  $Spec = (ConvertFrom-Scalar $Spec).Trim().Trim('"').Trim("'")
  $aliases = @{
    "maxvolume" = "max_volume"
    "max-volume" = "max_volume"
    "volume" = "max_volume"
    "maxchapter" = "max_chapter"
    "max-chapter" = "max_chapter"
    "chapter" = "max_chapter"
    "maxseason" = "max_season"
    "max-season" = "max_season"
    "season" = "max_season"
    "maxepisode" = "max_episode"
    "max-episode" = "max_episode"
    "episode" = "max_episode"
    "maxreleaseorder" = "max_release_order"
    "max-release-order" = "max_release_order"
    "releaseorder" = "max_release_order"
    "release-order" = "max_release_order"
    "includeunknownsubjects" = "include_unknown_subjects"
    "include-unknown-subjects" = "include_unknown_subjects"
    "includeunknownpositions" = "include_unknown_positions"
    "include-unknown-positions" = "include_unknown_positions"
    "file" = "file_stem"
    "filename" = "file_stem"
    "file-stem" = "file_stem"
  }
  $values = @{}
  foreach ($part in $Spec -split ",") {
    $part = $part.Trim().Trim('"').Trim("'")
    if (-not $part) {
      continue
    }
    if (-not $part.Contains("=")) {
      throw "Invalid -BoundedGraph segment '$part'. Use key=value pairs."
    }
    $pieces = $part.Split("=", 2)
    $key = $pieces[0].Trim().Trim('"').Trim("'")
    $normalizedKey = $key.Replace("_", "-").ToLowerInvariant()
    if ($aliases.ContainsKey($normalizedKey)) {
      $normalizedKey = $aliases[$normalizedKey]
    } else {
      $normalizedKey = $key.Trim().Replace("-", "_").ToLowerInvariant()
    }
    $values[$normalizedKey] = (ConvertFrom-Scalar $pieces[1].Trim()).Trim('"').Trim("'")
  }

  $name = if ($values.ContainsKey("name") -and $values["name"]) { $values["name"] } else { "bounded-graph-$Index" }
  $medium = if ($values.ContainsKey("medium") -and $values["medium"]) { $values["medium"] } else { "novel" }
  $fileStemSource = if ($values.ContainsKey("file_stem") -and $values["file_stem"]) { $values["file_stem"] } else { $name }
  $hasBoundary = $false
  foreach ($key in @("max_volume", "max_chapter", "max_season", "max_episode", "max_release_order")) {
    if ($values.ContainsKey($key) -and $values[$key]) {
      $hasBoundary = $true
    }
  }
  if (-not $hasBoundary) {
    throw "-BoundedGraph '$Spec' must include at least one max boundary, such as maxVolume=1."
  }

  return [pscustomobject]@{
    name = $name
    file_stem = ConvertTo-SafeSlug $fileStemSource "bounded-graph-$Index"
    medium = $medium
    max_volume = if ($values.ContainsKey("max_volume")) { $values["max_volume"] } else { "" }
    max_chapter = if ($values.ContainsKey("max_chapter")) { $values["max_chapter"] } else { "" }
    max_season = if ($values.ContainsKey("max_season")) { $values["max_season"] } else { "" }
    max_episode = if ($values.ContainsKey("max_episode")) { $values["max_episode"] } else { "" }
    max_release_order = if ($values.ContainsKey("max_release_order")) { $values["max_release_order"] } else { "" }
    include_unknown_subjects = ConvertTo-BoolValue $(if ($values.ContainsKey("include_unknown_subjects")) { $values["include_unknown_subjects"] } else { "false" })
    include_unknown_positions = ConvertTo-BoolValue $(if ($values.ContainsKey("include_unknown_positions")) { $values["include_unknown_positions"] } else { "false" })
  }
}

function ConvertFrom-BoundedGraphSpecs {
  param([string[]]$Specs)
  $result = @()
  $index = 1
  foreach ($rawSpec in @($Specs)) {
    foreach ($spec in ($rawSpec -split ";")) {
      if (-not $spec.Trim()) {
        continue
      }
      $result += ConvertFrom-BoundedGraphSpec $spec $index
      $index += 1
    }
  }
  return @($result)
}

function ConvertFrom-BoundedPageSpec {
  param(
    [string]$Spec,
    [int]$Index
  )
  $Spec = (ConvertFrom-Scalar $Spec).Trim().Trim('"').Trim("'")
  $aliases = @{
    "maxvolume" = "max_volume"
    "max-volume" = "max_volume"
    "volume" = "max_volume"
    "maxchapter" = "max_chapter"
    "max-chapter" = "max_chapter"
    "chapter" = "max_chapter"
    "maxseason" = "max_season"
    "max-season" = "max_season"
    "season" = "max_season"
    "maxepisode" = "max_episode"
    "max-episode" = "max_episode"
    "episode" = "max_episode"
    "maxreleaseorder" = "max_release_order"
    "max-release-order" = "max_release_order"
    "releaseorder" = "max_release_order"
    "release-order" = "max_release_order"
    "includeanonymouspreview" = "include_anonymous_preview"
    "include-anonymous-preview" = "include_anonymous_preview"
    "file" = "file_stem"
    "filename" = "file_stem"
    "file-stem" = "file_stem"
  }
  $values = @{}
  foreach ($part in $Spec -split ",") {
    $part = $part.Trim().Trim('"').Trim("'")
    if (-not $part) {
      continue
    }
    if (-not $part.Contains("=")) {
      throw "Invalid -BoundedPage segment '$part'. Use key=value pairs."
    }
    $pieces = $part.Split("=", 2)
    $key = $pieces[0].Trim().Trim('"').Trim("'")
    $normalizedKey = $key.Replace("_", "-").ToLowerInvariant()
    if ($aliases.ContainsKey($normalizedKey)) {
      $normalizedKey = $aliases[$normalizedKey]
    } else {
      $normalizedKey = $key.Trim().Replace("-", "_").ToLowerInvariant()
    }
    $values[$normalizedKey] = (ConvertFrom-Scalar $pieces[1].Trim()).Trim('"').Trim("'")
  }

  if (-not $values.ContainsKey("slug") -or -not $values["slug"]) {
    throw "-BoundedPage '$Spec' must include slug=<canonical-slug>."
  }
  $hasBoundary = $false
  foreach ($key in @("max_volume", "max_chapter", "max_season", "max_episode", "max_release_order")) {
    if ($values.ContainsKey($key) -and $values[$key]) {
      $hasBoundary = $true
    }
  }
  if (-not $hasBoundary) {
    throw "-BoundedPage '$Spec' must include at least one max boundary, such as maxChapter=30."
  }

  return [pscustomobject]@{
    slug = $values["slug"]
    name = if ($values.ContainsKey("name")) { $values["name"] } else { "" }
    file_stem = if ($values.ContainsKey("file_stem")) { $values["file_stem"] } else { "" }
    medium = if ($values.ContainsKey("medium") -and $values["medium"]) { $values["medium"] } else { "novel" }
    max_volume = if ($values.ContainsKey("max_volume")) { $values["max_volume"] } else { "" }
    max_chapter = if ($values.ContainsKey("max_chapter")) { $values["max_chapter"] } else { "" }
    max_season = if ($values.ContainsKey("max_season")) { $values["max_season"] } else { "" }
    max_episode = if ($values.ContainsKey("max_episode")) { $values["max_episode"] } else { "" }
    max_release_order = if ($values.ContainsKey("max_release_order")) { $values["max_release_order"] } else { "" }
    include_anonymous_preview = ConvertTo-BoolValue $(if ($values.ContainsKey("include_anonymous_preview")) { $values["include_anonymous_preview"] } else { "true" })
  }
}

function ConvertFrom-BoundedPageSpecs {
  param([string[]]$Specs)
  $result = @()
  $index = 1
  foreach ($rawSpec in @($Specs)) {
    foreach ($spec in ($rawSpec -split ";")) {
      if (-not $spec.Trim()) {
        continue
      }
      $result += ConvertFrom-BoundedPageSpec $spec $index
      $index += 1
    }
  }
  return @($result)
}

function Import-YamlModuleForBoundedPages {
  param([object[]]$BoundedPageSpecs)
  if (@($BoundedPageSpecs).Count -eq 0) {
    return
  }
  try {
    Import-Module powershell-yaml -ErrorAction Stop
  } catch {
    throw "Bounded page generation requires the PowerShell module 'powershell-yaml'. Install it with: Install-Module powershell-yaml -Scope CurrentUser -Force -AllowClobber"
  }
}

function Get-CanonicalNotes {
  param(
    [string]$RepoRoot,
    [bool]$IncludeStubPages
  )
  $notes = @{}
  $relationships = @()
  $dataReferences = @()
  $dataProjections = @{}

  foreach ($searchPath in @((Join-Path $RepoRoot "Glossary_Threads"), (Join-Path $RepoRoot "Volumes"))) {
    if (-not (Test-Path -LiteralPath $searchPath)) {
      continue
    }
    $files = Get-ChildItem -Path $searchPath -Recurse -Filter "*.md" |
      Where-Object { $_.Name.ToUpperInvariant() -ne "TEMPLATE.MD" } |
      Sort-Object FullName
    foreach ($file in $files) {
      $text = Read-TextFile $file.FullName
      $metadata = Get-Metadata $text
      if (-not $metadata.Contains("type")) {
        continue
      }
      if (-not $IncludeStubPages -and $metadata.Contains("status") -and $metadata["status"].ToLowerInvariant() -eq "stub") {
        continue
      }

      $relativeSource = (ConvertTo-RelativePath $file.FullName $RepoRoot) -replace "\\", "/"
      $slug = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
      $noteRelationships = @(Get-RelationshipsFromYaml (Get-RelationshipYaml $text) $relativeSource)
      $noteDataRefs = @(Get-DataReferences $text $slug $relativeSource)
      $noteDataProjections = Get-DataProjections $text $slug
      $noteFirstAppearanceBeats = @(Get-FirstAppearanceBeats $text)
      $typeName = $metadata["type"]
      $note = [pscustomobject]@{
        slug = $slug
        title = Get-FirstHeading $text (ConvertTo-SlugTitle $slug)
        source_path = $file.FullName
        relative_source = $relativeSource
      metadata = $metadata
      first_appearance_beats = $noteFirstAppearanceBeats
      relationships = $noteRelationships
      data_references = $noteDataRefs
      data_projections = $noteDataProjections
      type_name = $typeName
      export_folder = Get-ExportFolder $typeName
      export_file_stem = ConvertTo-SafeFileName (Get-FirstHeading $text (ConvertTo-SlugTitle $slug))
    }
      $notes[$slug] = $note
      $relationships += $noteRelationships
      $dataReferences += $noteDataRefs
      foreach ($projectionKey in $noteDataProjections.Keys) {
        $dataProjections[$projectionKey] = $noteDataProjections[$projectionKey]
      }
    }
  }

  return [pscustomobject]@{
    Notes = $notes
    Relationships = @($relationships)
    DataReferences = @($dataReferences)
    DataProjections = $dataProjections
  }
}

function Format-WikiLink {
  param(
    [string]$Slug,
    [hashtable]$Notes
  )
  if ($Notes.ContainsKey($Slug)) {
    $note = $Notes[$Slug]
    return "[[$($note.export_folder)/$($note.export_file_stem)|$($note.title)]]"
  }
  return "[[$(ConvertTo-SlugTitle $Slug)]]"
}

function Format-TableWikiLink {
  param(
    [string]$Slug,
    [hashtable]$Notes
  )
  if ($Notes.ContainsKey($Slug)) {
    $note = $Notes[$Slug]
    return "[[$($note.export_folder)/$($note.export_file_stem)|$($note.title)]]"
  }
  return "[[$(ConvertTo-SlugTitle $Slug)]]"
}

function Format-SourceLink {
  param([string]$SourceFile)
  $sourceWithoutSuffix = if ($SourceFile.EndsWith(".md")) { $SourceFile.Substring(0, $SourceFile.Length - 3) } else { $SourceFile }
  return "[[$sourceWithoutSuffix|$SourceFile]]"
}

function Format-TableSourceLink {
  param([string]$SourceFile)
  $sourceWithoutSuffix = if ($SourceFile.EndsWith(".md")) { $SourceFile.Substring(0, $SourceFile.Length - 3) } else { $SourceFile }
  return "[[$sourceWithoutSuffix]]"
}

function ConvertTo-YamlQuote {
  param([object]$Value)
  if ($Value -is [bool]) {
    if ($Value) { return "true" }
    return "false"
  }
  $escaped = ([string]$Value).Replace("\", "\\").Replace('"', '\"')
  return '"' + $escaped + '"'
}

function ConvertTo-MermaidEscaped {
  param([string]$Value)
  return $Value.Replace("\", "\\").Replace('"', '\"')
}

function ConvertTo-MermaidNodeId {
  param([string]$Slug)
  $cleaned = [regex]::Replace($Slug, "[^A-Za-z0-9_]", "_")
  if (-not $cleaned -or [char]::IsDigit($cleaned[0])) {
    $cleaned = "node_$cleaned"
  }
  return $cleaned
}

function Get-MermaidNodeTitle {
  param(
    [string]$Slug,
    [hashtable]$Notes
  )
  if ($Notes.ContainsKey($Slug)) {
    return $Notes[$Slug].title
  }
  return ConvertTo-SlugTitle $Slug
}

function Format-EdgeLine {
  param(
    [object]$Relationship,
    [hashtable]$Notes,
    [switch]$Incoming
  )
  $subjectSlug = if ($Incoming) { $Relationship.source } else { $Relationship.target }
  $subject = Format-WikiLink $subjectSlug $Notes
  $relationshipType = if ($Relationship.relationship_type) { $Relationship.relationship_type } else { "relationship" }
  $fieldName = if ($Incoming) { "incoming-$relationshipType" } else { $relationshipType }
  $details = @()
  if ($Relationship.status) { $details += "status: $($Relationship.status)" }
  if ($Relationship.confidence) { $details += "confidence: $($Relationship.confidence)" }
  $startParts = @($Relationship.start_medium, $Relationship.start_volume, $Relationship.start_chapter) | Where-Object { $_ }
  if ($startParts.Count -gt 0) { $details += "start: $($startParts -join ' ')" }
  $suffix = if ($details.Count -gt 0) { " ($($details -join '; '))" } else { "" }
  return "- ${fieldName}:: $subject$suffix"
}

function Format-DataRefLine {
  param(
    [object]$Reference,
    [hashtable]$Notes,
    [switch]$Incoming
  )
  $subjectSlug = if ($Incoming) { $Reference.source } else { $Reference.target }
  $subject = Format-WikiLink $subjectSlug $Notes
  $key = if ($Reference.context_key) { $Reference.context_key } else { "yaml-reference" }
  return "- ${key}:: $subject ($($Reference.yaml_block); $(Format-SourceLink $Reference.source_file))"
}

function Format-TableCell {
  param([string]$Value)
  if ($null -eq $Value) {
    return ""
  }
  return $Value.Replace("|", "\|")
}

function Format-BeatPosition {
  param([hashtable]$Position)
  $parts = @()
  foreach ($item in @(
    @{ key = "book"; label = "book" },
    @{ key = "volume"; label = "vol" },
    @{ key = "chapter"; label = "ch" },
    @{ key = "season"; label = "s" },
    @{ key = "episode"; label = "ep" },
    @{ key = "release_order"; label = "order" }
  )) {
    if ($Position.ContainsKey($item.key) -and $Position[$item.key]) {
      $parts += "$($item.label) $($Position[$item.key])"
    }
  }
  return ($parts -join ", ")
}

function ConvertTo-FirstAppearanceBeatMarkdown {
  param([object[]]$Beats)
  $lines = @("", "## First Appearance Beats", "")
  if ($Beats.Count -eq 0) {
    $lines += "- None generated."
    return @($lines)
  }

  $lines += "| Medium | Beat | Position | Reader / Viewer Knowledge | Graph Display | Status |"
  $lines += "|---|---|---|---|---|---|"
  foreach ($beat in $Beats) {
    $beatTitle = @(if ($beat.beat_type) { $beat.beat_type }; if ($beat.title) { $beat.title }) -join " - "
    $knowledge = @(if ($beat.reader_knowledge_state) { $beat.reader_knowledge_state }; if ($beat.viewer_knowledge_state) { $beat.viewer_knowledge_state }) -join " / "
    $graphDisplay = $beat.graph_behavior
    if ($beat.graph_label) {
      $graphDisplay = if ($graphDisplay) { "${graphDisplay}: $($beat.graph_label)" } else { $beat.graph_label }
    }
    $status = @(if ($beat.status) { $beat.status }; if ($beat.confidence) { $beat.confidence }) -join " / "
    $cells = @(
      (Format-TableCell $beat.medium),
      (Format-TableCell $beatTitle),
      (Format-TableCell (Format-BeatPosition $beat.position)),
      (Format-TableCell $knowledge),
      (Format-TableCell $graphDisplay),
      (Format-TableCell $status)
    )
    $lines += "| $($cells -join ' | ') |"
  }
  return @($lines)
}

function ConvertTo-NoteMarkdown {
  param(
    [object]$Note,
    [hashtable]$Notes,
    [object[]]$Relationships,
    [object[]]$DataReferences
  )
  $generatedAt = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ss+00:00")
  $outgoing = @($Relationships | Where-Object { $_.source -eq $Note.slug })
  $incoming = @($Relationships | Where-Object { $_.target -eq $Note.slug -and $_.source -ne $Note.slug })
  $outgoingRefs = @($DataReferences | Where-Object { $_.source -eq $Note.slug })
  $incomingRefs = @($DataReferences | Where-Object { $_.target -eq $Note.slug -and $_.source -ne $Note.slug })

  $lines = @(
    "---",
    "source_file: $(ConvertTo-YamlQuote $Note.relative_source)",
    "source_slug: $(ConvertTo-YamlQuote $Note.slug)",
    "type: $(ConvertTo-YamlQuote $Note.type_name.ToLowerInvariant())",
    "status: $(ConvertTo-YamlQuote $(if ($Note.metadata.Contains('status')) { $Note.metadata['status'] } else { '' }))",
    "reader_boundary: $(ConvertTo-YamlQuote $(if ($Note.metadata.Contains('reader_knowledge_boundary')) { $Note.metadata['reader_knowledge_boundary'] } else { '' }))",
    "spoiler_boundary: $(ConvertTo-YamlQuote $(if ($Note.metadata.Contains('spoiler_boundary')) { $Note.metadata['spoiler_boundary'] } else { '' }))",
    "generated: true",
    "generated_at: $(ConvertTo-YamlQuote $generatedAt)",
    "---",
    "",
    "# $($Note.title)",
    "",
    "## Canonical Source",
    "",
    "- $(Format-SourceLink $Note.relative_source)",
    "",
    "## Metadata Mirror",
    ""
  )

  foreach ($key in @("type", "status", "reader_knowledge_boundary", "spoiler_boundary", "confidence_level", "tags")) {
    if ($Note.metadata.Contains($key)) {
      $displayKey = (($key -replace "_", " ") -split " " | ForEach-Object { $_.Substring(0, 1).ToUpperInvariant() + $_.Substring(1) }) -join " "
      $lines += "- ${displayKey}:: $($Note.metadata[$key])"
    }
  }

  $lines += ConvertTo-FirstAppearanceBeatMarkdown $Note.first_appearance_beats

  $lines += @("", "## Outgoing Relationship Seeds", "")
  if ($outgoing.Count -gt 0) {
    foreach ($rel in $outgoing) { $lines += Format-EdgeLine $rel $Notes }
  } else {
    $lines += "- None generated."
  }

  $lines += @("", "## Incoming Relationship Seeds", "")
  if ($incoming.Count -gt 0) {
    foreach ($rel in $incoming) { $lines += Format-EdgeLine $rel $Notes -Incoming }
  } else {
    $lines += "- None generated."
  }

  $lines += @("", "## Data Block References", "")
  if ($outgoingRefs.Count -gt 0) {
    foreach ($ref in $outgoingRefs) { $lines += Format-DataRefLine $ref $Notes }
  } else {
    $lines += "- None generated."
  }

  $lines += @("", "## Incoming Data Block References", "")
  if ($incomingRefs.Count -gt 0) {
    foreach ($ref in $incomingRefs) { $lines += Format-DataRefLine $ref $Notes -Incoming }
  } else {
    $lines += "- None generated."
  }

  $lines += @("", "## Seed Evidence", "")
  if ($outgoing.Count -gt 0 -or $incoming.Count -gt 0) {
    foreach ($rel in @($outgoing + $incoming)) {
      $type = if ($rel.relationship_type) { $rel.relationship_type } else { "relationship" }
      $lines += "- ``$($rel.source)`` --$type--> ``$($rel.target)`` from $(Format-SourceLink $rel.source_file)"
    }
  } else {
    $lines += "- No Relationship Seeds mention this note."
  }

  $lines += ""
  return ($lines -join "`n")
}

function Get-QAGraphClassDefinitions {
  param([switch]$IncludeRelationship)
  $lines = @(
    "",
    "  classDef character fill:#dbeafe,stroke:#2563eb,color:#111827",
    "  classDef faction fill:#fee2e2,stroke:#dc2626,color:#111827",
    "  classDef artifact fill:#fef3c7,stroke:#d97706,color:#111827",
    "  classDef concept fill:#ede9fe,stroke:#7c3aed,color:#111827",
    "  classDef pathway fill:#dcfce7,stroke:#16a34a,color:#111827",
    "  classDef location fill:#ffedd5,stroke:#ea580c,color:#111827",
    "  classDef event fill:#fce7f3,stroke:#db2777,color:#111827",
    "  classDef item fill:#ecfccb,stroke:#65a30d,color:#111827",
    "  classDef source fill:#cffafe,stroke:#0891b2,color:#111827",
    "  classDef volume fill:#e5e7eb,stroke:#6b7280,color:#111827",
    "  classDef unknown fill:#f8fafc,stroke:#64748b,stroke-dasharray: 4 3,color:#111827"
  )
  if ($IncludeRelationship) {
    $lines += "  classDef relationship fill:#f8fafc,stroke:#475569,stroke-width:1.5px,color:#111827"
  }
  return $lines
}

function Add-QAGraphClassAssignments {
  param(
    [System.Collections.Generic.List[string]]$Lines,
    [string[]]$UsedSlugs,
    [hashtable]$Notes
  )
  $classMap = @{
    "Character" = "character"
    "Faction" = "faction"
    "Artifact" = "artifact"
    "Concept" = "concept"
    "Pathway" = "pathway"
    "Location" = "location"
    "Event" = "event"
    "Item" = "item"
    "Knowledge Source" = "source"
    "Volume Summary" = "volume"
  }
  foreach ($slug in $UsedSlugs) {
    $className = "unknown"
    if ($Notes.ContainsKey($slug) -and $classMap.ContainsKey($Notes[$slug].type_name)) {
      $className = $classMap[$Notes[$slug].type_name]
    }
    $Lines.Add("  class $(ConvertTo-MermaidNodeId $slug) $className") | Out-Null
  }
}

function Group-Relationships {
  param([object[]]$Relationships)
  $grouped = @{}
  foreach ($rel in $Relationships) {
    if (-not $rel.source -or -not $rel.target) {
      continue
    }
    $type = if ($rel.relationship_type) { $rel.relationship_type } else { "relationship" }
    $key = "$($rel.source)|$type|$($rel.target)"
    if (-not $grouped.ContainsKey($key)) {
      $grouped[$key] = @()
    }
    $grouped[$key] = @($grouped[$key] + $rel)
  }
  return $grouped
}

function Get-UsedSlugs {
  param([hashtable]$Grouped)
  $set = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($key in $Grouped.Keys) {
    $parts = $key -split "\|", 3
    [void]$set.Add($parts[0])
    [void]$set.Add($parts[2])
  }
  return @($set | Sort-Object)
}

function Get-SingularDomainLabel {
  param([string]$Value)
  $normalized = $Value.Trim().ToLowerInvariant().Replace("_", "-")
  $mapping = @{
    "artifacts" = "artifact"
    "characters" = "character"
    "concepts" = "concept"
    "deities" = "deity"
    "events" = "event"
    "factions" = "faction"
    "items" = "item"
    "knowledge-sources" = "source"
    "knowledge_sources" = "source"
    "locations" = "location"
    "pathways" = "pathway"
    "tarot-cards" = "tarot"
    "uniquenesses" = "uniqueness"
    "volumes" = "volume"
  }
  if ($mapping.ContainsKey($normalized)) {
    return $mapping[$normalized]
  }
  if ($normalized.EndsWith("s")) {
    return $normalized.Substring(0, $normalized.Length - 1)
  }
  if ([string]::IsNullOrWhiteSpace($normalized)) {
    return "source"
  }
  return $normalized
}

function Get-RelationshipSourceDomain {
  param([string]$SourceFile)
  $parts = @($SourceFile -split '[\\/]')
  $glossaryIndex = [array]::IndexOf($parts, "Glossary_Threads")
  if ($glossaryIndex -ge 0 -and $glossaryIndex + 1 -lt $parts.Count) {
    return Get-SingularDomainLabel $parts[$glossaryIndex + 1]
  }
  if ($parts.Count -gt 0 -and $parts[0] -eq "Volumes") {
    return "volume"
  }
  $stem = [System.IO.Path]::GetFileNameWithoutExtension($SourceFile)
  foreach ($prefix in $SlugPrefixes) {
    if ($stem.StartsWith("$prefix-")) {
      if ($prefix -eq "tarot-card") { return "tarot" }
      return $prefix
    }
  }
  return "source"
}

function Get-RelationshipProvenanceLines {
  param(
    [object[]]$Relationships,
    [hashtable]$DataProjections = @{}
  )
  $lines = @()
  foreach ($rel in @($Relationships | Sort-Object @{ Expression = { Get-RelationshipSourceDomain $_.source_file } }, confidence, start_chapter, source_file)) {
    if ($DataProjections.Count -gt 0) {
      $line = Format-RelationshipSourceLine $rel $DataProjections
      if ($line) {
        $lines += $line
        continue
      }
    }
    $parts = @(Get-RelationshipSourceDomain $rel.source_file, "seed")
    if ($rel.start_medium) { $parts += $rel.start_medium }
    if ($rel.confidence) { $parts += $rel.confidence }
    if ($rel.start_chapter) { $parts += "ch$($rel.start_chapter)" }
    if ($rel.status -and $rel.status -ne "active") { $parts += $rel.status }
    $lines += ($parts -join " ")
  }
  return $lines
}

function ConvertTo-LabeledRelationshipGraph {
  param(
    [object[]]$Relationships,
    [hashtable]$Notes
  )
  $grouped = Group-Relationships $Relationships
  $usedSlugs = Get-UsedSlugs $grouped
  $lines = [System.Collections.Generic.List[string]]::new()
  @(
    "%% QA Relationship Graph",
    "%% Generated from Relationship Seeds as a QA-only Mermaid view.",
    "%% Duplicate seed edges are collapsed and marked with counts.",
    "%% Unknown nodes are Relationship Seed slugs that do not currently resolve to generated mirror notes.",
    "graph LR"
  ) | ForEach-Object { $lines.Add($_) | Out-Null }

  foreach ($slug in $usedSlugs) {
    $lines.Add(('  {0}["{1}"]' -f (ConvertTo-MermaidNodeId $slug), (ConvertTo-MermaidEscaped (Get-MermaidNodeTitle $slug $Notes)))) | Out-Null
  }
  $lines.Add("") | Out-Null

  foreach ($key in @($grouped.Keys | Sort-Object)) {
    $parts = $key -split "\|", 3
    $label = $parts[1]
    if ($grouped[$key].Count -gt 1) {
      $label = "$label x$($grouped[$key].Count)"
    }
    $lines.Add(('  {0} -->|"{1}"| {2}' -f (ConvertTo-MermaidNodeId $parts[0]), (ConvertTo-MermaidEscaped $label), (ConvertTo-MermaidNodeId $parts[2]))) | Out-Null
  }

  foreach ($line in Get-QAGraphClassDefinitions) { $lines.Add($line) | Out-Null }
  Add-QAGraphClassAssignments $lines $usedSlugs $Notes
  $lines.Add("") | Out-Null
  return ($lines -join "`n")
}

function ConvertTo-RelationshipNodeGraph {
  param(
    [object[]]$Relationships,
    [hashtable]$Notes,
    [hashtable]$DataProjections
  )
  $grouped = Group-Relationships $Relationships
  $usedSlugs = Get-UsedSlugs $grouped
  $lines = [System.Collections.Generic.List[string]]::new()
  @(
    "%% QA Relationship Node Graph",
    "%% Generated from Relationship Seeds as a QA-only Mermaid view with relationship nodes.",
    "%% Duplicate seed edges are collapsed into relationship nodes and marked with counts.",
    "%% Unknown nodes are Relationship Seed slugs that do not currently resolve to generated mirror notes.",
    "graph LR"
  ) | ForEach-Object { $lines.Add($_) | Out-Null }

  foreach ($slug in $usedSlugs) {
    $lines.Add(('  {0}["{1}"]' -f (ConvertTo-MermaidNodeId $slug), (ConvertTo-MermaidEscaped (Get-MermaidNodeTitle $slug $Notes)))) | Out-Null
  }
  $lines.Add("") | Out-Null

  $index = 1
  foreach ($key in @($grouped.Keys | Sort-Object)) {
    $parts = $key -split "\|", 3
    $labelLines = @(if ($grouped[$key].Count -gt 1) { "$($parts[1]) x$($grouped[$key].Count)" } else { $parts[1] })
    $sourceLines = @(Get-RelationshipSourceLines $grouped[$key] $DataProjections)
    if ($sourceLines.Count -gt 0) {
      $labelLines += $sourceLines
    }
    if ($grouped[$key].Count -gt 1) {
      foreach ($fallbackLine in @(Get-RelationshipProvenanceLines $grouped[$key] $DataProjections)) {
        if ($labelLines -notcontains $fallbackLine) {
          $labelLines += $fallbackLine
        }
      }
    }
    $label = $labelLines -join "<br/>"
    $relationshipNodeId = "rel_{0:d3}" -f $index
    $lines.Add(('  {0}["{1}"]' -f $relationshipNodeId, (ConvertTo-MermaidEscaped $label))) | Out-Null
    $lines.Add(('  {0} --> {1}' -f (ConvertTo-MermaidNodeId $parts[0]), $relationshipNodeId)) | Out-Null
    $lines.Add(('  {0} --> {1}' -f $relationshipNodeId, (ConvertTo-MermaidNodeId $parts[2]))) | Out-Null
    $index += 1
  }

  foreach ($line in Get-QAGraphClassDefinitions -IncludeRelationship) { $lines.Add($line) | Out-Null }
  Add-QAGraphClassAssignments $lines $usedSlugs $Notes
  if ($index -gt 1) {
    foreach ($relIndex in 1..($index - 1)) {
      $lines.Add(("  class rel_{0:d3} relationship" -f $relIndex)) | Out-Null
    }
  }
  $lines.Add("") | Out-Null
  return ($lines -join "`n")
}

function Get-RelationshipSourceLines {
  param(
    [object[]]$Relationships,
    [hashtable]$DataProjections
  )
  $seen = New-Object 'System.Collections.Generic.HashSet[string]'
  $lines = @()
  foreach ($rel in @($Relationships | Sort-Object @{ Expression = { Get-RelationshipSourceDomain $_.source_file } }, source_file)) {
    $line = Format-RelationshipSourceLine $rel $DataProjections
    if ($line -and $seen.Add($line)) {
      $lines += $line
    }
  }
  return @($lines)
}

function Format-RelationshipSourceLine {
  param(
    [object]$Relationship,
    [hashtable]$DataProjections
  )
  $domain = Get-RelationshipSourceDomain $Relationship.source_file
  $namespacedProjectionSource = "$($Relationship.source)|$($Relationship.projection_source)"
  if ($Relationship.projection_source -and ($DataProjections.ContainsKey($namespacedProjectionSource) -or $DataProjections.ContainsKey($Relationship.projection_source))) {
    if ($DataProjections.ContainsKey($namespacedProjectionSource)) {
      $projection = $DataProjections[$namespacedProjectionSource]
    } else {
      $projection = $DataProjections[$Relationship.projection_source]
    }
    $history = Format-AvailabilityHistory @($projection.availability)
    if ($history) {
      return "$domain data $history"
    }
  }

  $parts = @($domain, "seed")
  if ($Relationship.start_medium) { $parts += $Relationship.start_medium }
  if ($Relationship.start_chapter) { $parts += "ch$($Relationship.start_chapter)" }
  if ($Relationship.confidence) { $parts += $Relationship.confidence }
  if ($Relationship.status -and $Relationship.status -ne "active") { $parts += $Relationship.status }
  return ($parts -join " ")
}

function Format-AvailabilityHistory {
  param([object[]]$Entries)
  $byMedium = @{}
  foreach ($entry in $Entries) {
    $entryText = Format-AvailabilityEntry $entry
    if (-not $entryText) {
      continue
    }
    $medium = if ($entry.medium) { $entry.medium } else { "unknown" }
    if (-not $byMedium.ContainsKey($medium)) {
      $byMedium[$medium] = @()
    }
    if ($byMedium[$medium] -notcontains $entryText) {
      $byMedium[$medium] += $entryText
    }
  }
  $lines = @()
  foreach ($medium in @($byMedium.Keys | Sort-Object)) {
    $lines += "$medium $($byMedium[$medium] -join ' -> ')"
  }
  return ($lines -join "; ")
}

function Format-AvailabilityEntry {
  param([object]$Entry)
  $parts = @()
  if ($Entry.medium -eq "novel" -and $Entry.chapter) {
    $parts += "ch$($Entry.chapter)"
  } elseif ($Entry.medium -eq "donghua") {
    $hasRealPosition = $false
    foreach ($value in @($Entry.season, $Entry.episode, $Entry.release_order)) {
      if ($value -and $value -ne "TBD") { $hasRealPosition = $true }
    }
    if (-not $hasRealPosition) {
      return ""
    }
    if ($Entry.season -and $Entry.season -ne "TBD") { $parts += "s$($Entry.season)" }
    if ($Entry.episode -and $Entry.episode -ne "TBD") { $parts += "e$($Entry.episode)" }
    if ($Entry.release_order -and $Entry.release_order -ne "TBD") { $parts += "r$($Entry.release_order)" }
  } elseif ($Entry.medium) {
    $parts += $Entry.medium
  }
  if ($parts.Count -eq 0) {
    return ""
  }
  if ($Entry.confidence -and $Entry.confidence -ne "TBD") {
    $parts += $Entry.confidence
  } elseif ($Entry.status -and $Entry.status -ne "TBD") {
    $parts += $Entry.status
  }
  if ($Entry.graph_visibility -and $Entry.graph_visibility -ne "full") {
    $parts += $Entry.graph_visibility
  }
  if ($Entry.adaptation_relationship -and $Entry.adaptation_relationship -ne "pending") {
    $parts += $Entry.adaptation_relationship
  }
  return ($parts -join " ")
}

function ConvertTo-VisualizationRelationshipGraph {
  param(
    [object[]]$Relationships,
    [hashtable]$Notes,
    [hashtable]$DataProjections
  )
  $nodes = @{}
  $knownNodeIds = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($note in $Notes.Values) {
    if ($note.type_name -ne "Volume Summary") {
      $nodeId = ConvertTo-MermaidNodeId $note.slug
      $nodes[$nodeId] = $note.title
      [void]$knownNodeIds.Add($nodeId)
    }
  }
  foreach ($rel in $Relationships) {
    $source = ConvertTo-MermaidNodeId $rel.source
    $target = ConvertTo-MermaidNodeId $rel.target
    if (-not $nodes.ContainsKey($source)) { $nodes[$source] = ConvertTo-SlugTitle $rel.source }
    if (-not $nodes.ContainsKey($target)) { $nodes[$target] = ConvertTo-SlugTitle $rel.target }
  }

  $selected = @{}
  foreach ($rel in $Relationships) {
    if (-not $rel.source -or -not $rel.target -or -not $rel.relationship_type) {
      continue
    }
    $rendered = [pscustomobject]@{
      source = $rel.source
      target = $rel.target
      relationship_type = $rel.relationship_type
      start_chapter = $rel.start_chapter
      status = $rel.status
      confidence = $rel.confidence
      projection_source = $rel.projection_source
      history_label = ""
      has_projection = if ($rel.projection_source) { 1 } else { 0 }
      has_history = 0
    }
    $namespacedProjectionSource = "$($rel.source)|$($rel.projection_source)"
    if ($rel.projection_source -and ($DataProjections.ContainsKey($namespacedProjectionSource) -or $DataProjections.ContainsKey($rel.projection_source))) {
      if ($DataProjections.ContainsKey($namespacedProjectionSource)) {
        $projection = $DataProjections[$namespacedProjectionSource]
      } else {
        $projection = $DataProjections[$rel.projection_source]
      }
      $history = Format-AvailabilityHistory @($projection.availability)
      if ($history) {
        $rendered.history_label = $history
        $rendered.has_history = 1
        $availabilityEntries = @($projection.availability)
        $lastAvailability = $availabilityEntries[$availabilityEntries.Count - 1]
        if ($lastAvailability.chapter) { $rendered.start_chapter = $lastAvailability.chapter }
        if ($lastAvailability.status) { $rendered.status = $lastAvailability.status }
        if ($lastAvailability.confidence) { $rendered.confidence = $lastAvailability.confidence }
      }
    }

    $selectionKey = "$($rendered.source)|$($rendered.relationship_type)|$($rendered.target)"
    $confidenceRank = switch ($rendered.confidence) {
      "confirmed" { 3 }
      "strong-evidence" { 2 }
      "strong-inference" { 2 }
      "clue" { 1 }
      default { 0 }
    }
    $score = ($rendered.has_history * 1000) + ($rendered.has_projection * 100) + $confidenceRank
    if (-not $selected.ContainsKey($selectionKey) -or $score -gt $selected[$selectionKey].score) {
      $selected[$selectionKey] = [pscustomobject]@{
        relationship = $rendered
        score = $score
      }
    }
  }

  $edges = @()
  foreach ($entry in $selected.Values) {
    $rel = $entry.relationship
    $source = ConvertTo-MermaidNodeId $rel.source
    $target = ConvertTo-MermaidNodeId $rel.target
    if ($rel.history_label) {
      $parts = @($rel.relationship_type, $rel.history_label)
    } else {
      $parts = @($rel.relationship_type)
      if ($rel.start_chapter) { $parts += "ch$($rel.start_chapter)" }
      if ($rel.status -and $rel.status -ne "active") { $parts += $rel.status }
      if ($rel.confidence) { $parts += $rel.confidence }
    }
    $label = $parts -join " "
    $edges += [pscustomobject]@{
      source = $source
      target = $target
      label = $label
      nodeLabel = (($parts | ForEach-Object { ConvertTo-MermaidEscaped $_ }) -join "<br/>")
    }
  }

  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add("graph TD") | Out-Null
  foreach ($nodeId in @($nodes.Keys | Sort-Object)) {
    $lines.Add(('  {0}["{1}"]' -f $nodeId, (ConvertTo-MermaidEscaped $nodes[$nodeId]))) | Out-Null
  }
  $lines.Add("") | Out-Null
  $lines.Add("  classDef artifact fill:#f3ead7,stroke:#b7791f,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef character fill:#ecebff,stroke:#7c5cff,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef concept fill:#e8f5f0,stroke:#2f855a,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef deity fill:#fae8ff,stroke:#c026d3,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef epoch fill:#ede9fe,stroke:#6d28d9,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef event fill:#fff1f2,stroke:#e11d48,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef faction fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef family fill:#fce7f3,stroke:#be185d,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef item fill:#ecfccb,stroke:#65a30d,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef source fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef location fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef mystery fill:#e5e7eb,stroke:#4b5563,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef pathway fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef tarot fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef timeline fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef uniqueness fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef missingEndpoint fill:#f8fafc,stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3,color:#1f2937") | Out-Null
  $lines.Add("  classDef pendingNode stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3") | Out-Null
  $lines.Add("  classDef pendingEndpoint fill:#f8fafc,stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3,color:#1f2937") | Out-Null
  $lines.Add("  classDef relationship fill:#f7f2e9,stroke:#c69245,stroke-width:1.5px,color:#1f2937") | Out-Null
  $lines.Add("") | Out-Null
  foreach ($nodeId in @($nodes.Keys | Sort-Object)) {
    if (-not $knownNodeIds.Contains($nodeId)) {
      $lines.Add("  class $nodeId pendingEndpoint") | Out-Null
      continue
    }
    $className = ($nodeId -split "_")[0]
    if ($className -in @("artifact", "character", "concept", "deity", "epoch", "event", "faction", "family", "item", "source", "location", "mystery", "pathway", "tarot", "timeline", "uniqueness")) {
      $lines.Add("  class $nodeId $className") | Out-Null
    } else {
      $lines.Add("  class $nodeId missingEndpoint") | Out-Null
    }
  }
  $lines.Add("") | Out-Null

  $relationshipIndex = 1
  foreach ($edge in @($edges | Sort-Object source,target,label)) {
    $relationshipId = "rel_{0:d3}" -f $relationshipIndex
    $lines.Add(('  {0}["{1}"]' -f $relationshipId, $edge.nodeLabel)) | Out-Null
    $lines.Add("  class $relationshipId relationship") | Out-Null
    $lines.Add(('  {0} --> {1}' -f $edge.source, $relationshipId)) | Out-Null
    $lines.Add(('  {0} --> {1}' -f $relationshipId, $edge.target)) | Out-Null
    $relationshipIndex += 1
  }

  return ($lines -join "`n")
}

function ConvertTo-RelationshipIndex {
  param(
    [object[]]$Relationships,
    [hashtable]$Notes
  )
  $lines = @(
    "# Relationship Index",
    "",
    "Generated from Relationship Seeds. Canonical notes remain the source of truth.",
    "",
    "| Source | Relationship | Target | Status | Confidence | Seed File |",
    "|---|---|---|---|---|---|"
  )
  foreach ($rel in @($Relationships | Sort-Object source,relationship_type,target,source_file)) {
    $lines += "| " + (@(
      Format-TableWikiLink $rel.source $Notes
      $rel.relationship_type
      Format-TableWikiLink $rel.target $Notes
      $rel.status
      $rel.confidence
      Format-TableSourceLink $rel.source_file
    ) -join " | ") + " |"
  }
  $lines += ""
  return ($lines -join "`n")
}

function ConvertTo-DataReferenceIndex {
  param(
    [object[]]$DataReferences,
    [hashtable]$Notes
  )
  $lines = @(
    "# Data Block Reference Index",
    "",
    "Generated from non-Relationship-Seed YAML data blocks. These are references, not typed graph edges.",
    "",
    "| Source | Context | Target | YAML Block | File |",
    "|---|---|---|---|---|"
  )
  foreach ($ref in @($DataReferences | Sort-Object source,target,context_key)) {
    $lines += "| " + (@(
      Format-TableWikiLink $ref.source $Notes
      $ref.context_key
      Format-TableWikiLink $ref.target $Notes
      $ref.yaml_block
      Format-TableSourceLink $ref.source_file
    ) -join " | ") + " |"
  }
  $lines += ""
  return ($lines -join "`n")
}

function Get-OrphanAnalysis {
  param(
    [hashtable]$Notes,
    [object[]]$Relationships,
    [object[]]$DataReferences
  )
  $known = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($slug in $Notes.Keys) { [void]$known.Add($slug) }
  $relSources = New-Object 'System.Collections.Generic.HashSet[string]'
  $relTargets = New-Object 'System.Collections.Generic.HashSet[string]'
  $dataSources = New-Object 'System.Collections.Generic.HashSet[string]'
  $dataTargets = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($rel in $Relationships) {
    if ($rel.source) { [void]$relSources.Add($rel.source) }
    if ($rel.target) { [void]$relTargets.Add($rel.target) }
  }
  foreach ($ref in $DataReferences) {
    if ($ref.source) { [void]$dataSources.Add($ref.source) }
    if ($ref.target) { [void]$dataTargets.Add($ref.target) }
  }

  $allSources = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($item in @($relSources + $dataSources)) { [void]$allSources.Add($item) }
  $allTargets = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($item in @($relTargets + $dataTargets)) { [void]$allTargets.Add($item) }

  return [pscustomobject]@{
    unknown_relationship_sources = @($relSources | Where-Object { -not $known.Contains($_) } | Sort-Object)
    unknown_relationship_targets = @($relTargets | Where-Object { -not $known.Contains($_) } | Sort-Object)
    unknown_data_targets = @($dataTargets | Where-Object { -not $known.Contains($_) } | Sort-Object)
    notes_without_any_edges_or_refs = @($known | Where-Object { -not $allSources.Contains($_) -and -not $allTargets.Contains($_) } | Sort-Object)
    notes_without_outgoing_relationships = @($known | Where-Object { -not $relSources.Contains($_) } | Sort-Object)
  }
}

function ConvertTo-OrphanReport {
  param(
    [hashtable]$Notes,
    [object[]]$Relationships,
    [object[]]$DataReferences
  )
  $data = Get-OrphanAnalysis $Notes $Relationships $DataReferences
  $sections = @(
    [pscustomobject]@{ Heading = "Unknown Relationship Sources"; Key = "unknown_relationship_sources" },
    [pscustomobject]@{ Heading = "Unknown Relationship Targets"; Key = "unknown_relationship_targets" },
    [pscustomobject]@{ Heading = "Unknown Data Block Targets"; Key = "unknown_data_targets" },
    [pscustomobject]@{ Heading = "Canonical Notes With No Edges Or Data References"; Key = "notes_without_any_edges_or_refs" },
    [pscustomobject]@{ Heading = "Canonical Notes With No Outgoing Relationship Seeds"; Key = "notes_without_outgoing_relationships" }
  )
  $lines = @("# Orphan Report", "", "Unknown entries do not currently resolve to a generated canonical mirror note.", "")
  foreach ($section in $sections) {
    $lines += @("## $($section.Heading)", "")
    $values = @($data.($section.Key))
    if ($values.Count -gt 0) {
      foreach ($value in $values) {
        $lines += "- $(Format-WikiLink $value $Notes) (``$value``)"
      }
    } else {
      $lines += "- None."
    }
    $lines += ""
  }
  return ($lines -join "`n")
}

function Get-SuspiciousEdgeAnalysis {
  param(
    [object[]]$Relationships,
    [hashtable]$Notes
  )
  $loops = @($Relationships |
    Where-Object { $_.source -and $_.source -eq $_.target } |
    Sort-Object source, relationship_type, target, source_file)
  $seen = @{}
  foreach ($rel in $Relationships) {
    $key = "$($rel.source)|$($rel.relationship_type)|$($rel.target)"
    if (-not $seen.ContainsKey($key)) { $seen[$key] = @() }
    $seen[$key] = @($seen[$key] + $rel)
  }
  $duplicates = @(
    foreach ($key in ($seen.Keys | Sort-Object)) {
      $group = @($seen[$key] | Sort-Object source, relationship_type, target, source_file)
      if ($group.Count -gt 1) { ,$group }
    }
  )
  $edgeTypes = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($rel in $Relationships) {
    [void]$edgeTypes.Add("$($rel.source)|$($rel.relationship_type)|$($rel.target)")
  }
  $missingReciprocals = @($Relationships | Where-Object {
    $_.relationship_type -and
    $ReciprocalTypes.ContainsKey($_.relationship_type) -and
    -not $edgeTypes.Contains("$($_.target)|$($ReciprocalTypes[$_.relationship_type])|$($_.source)")
  } | Sort-Object source, relationship_type, target, source_file)
  $sameTypeKnownEdges = @($Relationships | Where-Object {
    $_.source -and $_.target -and $Notes.ContainsKey($_.source) -and $Notes.ContainsKey($_.target) -and
    $Notes[$_.source].type_name -eq $Notes[$_.target].type_name
  } | Sort-Object source, relationship_type, target, source_file)
  return [pscustomobject]@{
    self_loops = $loops
    duplicate_edges = $duplicates
    missing_reciprocals = $missingReciprocals
    same_type_known_edges = $sameTypeKnownEdges
  }
}

function ConvertTo-SuspiciousEdges {
  param(
    [hashtable]$Notes,
    [object[]]$Relationships
  )
  $data = Get-SuspiciousEdgeAnalysis $Relationships $Notes
  $lines = @("# Suspicious Edges", "", "These are lint-style prompts for human review, not automatic errors.", "")
  $lines += @("## Self Loops", "")
  if ($data.self_loops.Count -gt 0) {
    foreach ($rel in $data.self_loops) {
      $type = if ($rel.relationship_type) { $rel.relationship_type } else { "relationship" }
      $lines += "- $(Format-WikiLink $rel.source $Notes) $type -> $(Format-WikiLink $rel.target $Notes)"
    }
  } else { $lines += "- None." }

  $lines += @("", "## Duplicate Edges", "")
  if ($data.duplicate_edges.Count -gt 0) {
    foreach ($group in $data.duplicate_edges) {
      $rel = $group[0]
      $files = (($group | ForEach-Object { $_.source_file } | Sort-Object -Unique) -join ", ")
      $lines += "- $(Format-WikiLink $rel.source $Notes) $($rel.relationship_type) -> $(Format-WikiLink $rel.target $Notes) appears $($group.Count) times. Sources: $files"
    }
  } else { $lines += "- None." }

  $lines += @("", "## Expected Reciprocals Missing", "")
  if ($data.missing_reciprocals.Count -gt 0) {
    foreach ($rel in $data.missing_reciprocals) {
      $lines += "- $(Format-WikiLink $rel.source $Notes) $($rel.relationship_type) -> $(Format-WikiLink $rel.target $Notes); expected ``$($ReciprocalTypes[$rel.relationship_type])`` back."
    }
  } else { $lines += "- None." }

  $lines += @("", "## Same-Type Known Edges", "")
  if ($data.same_type_known_edges.Count -gt 0) {
    foreach ($rel in $data.same_type_known_edges) {
      $lines += "- $(Format-WikiLink $rel.source $Notes) $($rel.relationship_type) -> $(Format-WikiLink $rel.target $Notes) (``$($Notes[$rel.source].type_name)`` to ``$($Notes[$rel.target].type_name)``)"
    }
  } else { $lines += "- None." }
  $lines += ""
  return ($lines -join "`n")
}

function Assert-SafeOutputPath {
  param(
    [string]$RepoRoot,
    [string]$OutputPath
  )
  $resolvedRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
  if (Test-Path -LiteralPath $OutputPath) {
    $resolvedOutput = (Resolve-Path -LiteralPath $OutputPath).Path
  } else {
    $parent = Split-Path -Parent $OutputPath
    $leaf = Split-Path -Leaf $OutputPath
    $resolvedOutput = Join-Path (Resolve-Path -LiteralPath $parent).Path $leaf
  }
  if ($resolvedOutput -ne $resolvedRoot -and -not $resolvedOutput.StartsWith($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Output directory must stay inside the repository root: $OutputPath"
  }
  return $resolvedOutput
}

function Get-RepoRelativePath {
  param(
    [string]$RepoRoot,
    [string]$Path
  )
  if ([System.IO.Path]::IsPathRooted($Path)) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
  } else {
    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $Path))
  }
  $rootPath = [System.IO.Path]::GetFullPath($RepoRoot)
  if ($fullPath.StartsWith($rootPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $fullPath.Substring($rootPath.Length + 1).Replace("\", "/")
  }
  return $fullPath
}

function Write-RepoRefreshCheck {
  param(
    [string]$RepoRoot,
    [string]$GeneratedDir
  )
  $sourceSettingsPath = Join-Path $RepoRoot "Visualization/config/render-settings.json"
  $settings = Get-Content -LiteralPath $sourceSettingsPath -Raw | ConvertFrom-Json
  $checkDir = Join-Path $GeneratedDir "repo-refresh-check"
  $renderedDir = Join-Path $checkDir "rendered"
  New-Item -ItemType Directory -Path $checkDir -Force | Out-Null

  $settings.reportPath = Get-RepoRelativePath $RepoRoot (Join-Path $checkDir "refresh-check-report.md")
  $settings.snapshotPath = Get-RepoRelativePath $RepoRoot (Join-Path $checkDir "refresh-check-snapshot.json")

  foreach ($view in $settings.views) {
    $inputName = Split-Path -Leaf $view.input
    $view.input = Get-RepoRelativePath $RepoRoot (Join-Path $checkDir $inputName)

    $newOutputs = @()
    foreach ($output in $view.outputs) {
      $outputName = Split-Path -Leaf $output
      $newOutputs += (Get-RepoRelativePath $RepoRoot (Join-Path $renderedDir $outputName))
    }
    $view.outputs = $newOutputs
  }

  $settingsPath = Join-Path $checkDir "refresh-check-settings.json"
  Write-TextFile $settingsPath ($settings | ConvertTo-Json -Depth 50)

  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "Visualization/visualize.ps1") -Mode Refresh -SettingsPath (Get-RepoRelativePath $RepoRoot $settingsPath) -SkipRender
}

function Write-BoundedGraphs {
  param(
    [string]$RepoRoot,
    [string]$GeneratedDir,
    [object[]]$Specs
  )
  if (@($Specs).Count -eq 0) {
    return
  }

  $sourceSettingsPath = Join-Path $RepoRoot "Visualization/config/render-settings.json"
  $settings = Get-Content -LiteralPath $sourceSettingsPath -Raw | ConvertFrom-Json
  $boundedDir = Join-Path $GeneratedDir "bounded-graphs"
  New-Item -ItemType Directory -Path $boundedDir -Force | Out-Null

  $settings.reportPath = Get-RepoRelativePath $RepoRoot (Join-Path $boundedDir "bounded-graphs-report.md")
  $settings.snapshotPath = Get-RepoRelativePath $RepoRoot (Join-Path $boundedDir "bounded-graphs-snapshot.json")
  $settings.views = @()

  foreach ($spec in @($Specs)) {
    $boundary = [ordered]@{
      medium = $spec.medium
      includeUnknownSubjects = [bool]$spec.include_unknown_subjects
      includeUnknownPositions = [bool]$spec.include_unknown_positions
    }
    if ($spec.max_volume) { $boundary["maxVolume"] = $spec.max_volume }
    if ($spec.max_chapter) { $boundary["maxChapter"] = $spec.max_chapter }
    if ($spec.max_season) { $boundary["maxSeason"] = $spec.max_season }
    if ($spec.max_episode) { $boundary["maxEpisode"] = $spec.max_episode }
    if ($spec.max_release_order) { $boundary["maxReleaseOrder"] = $spec.max_release_order }

    $settings.views += [pscustomobject]@{
      name = $spec.name
      input = Get-RepoRelativePath $RepoRoot (Join-Path $boundedDir "$($spec.file_stem).mmd")
      readerBoundary = [pscustomobject]$boundary
      outputs = @()
    }
  }

  $settingsPath = Join-Path $boundedDir "bounded-graphs-settings.json"
  Write-TextFile $settingsPath ($settings | ConvertTo-Json -Depth 50)

  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "Visualization/visualize.ps1") -Mode Refresh -SettingsPath (Get-RepoRelativePath $RepoRoot $settingsPath) -SkipRender
}

function Get-MapValue {
  param(
    [object]$Map,
    [string]$Key,
    [object]$Default = ""
  )
  if ($null -eq $Map) { return $Default }
  if ($Map -is [System.Collections.IDictionary]) {
    if ($Map.Contains($Key)) { return $Map[$Key] }
    return $Default
  }
  $property = $Map.PSObject.Properties[$Key]
  if ($null -ne $property) { return $property.Value }
  return $Default
}

function Test-MapHasKey {
  param(
    [object]$Map,
    [string]$Key
  )
  if ($null -eq $Map) { return $false }
  if ($Map -is [System.Collections.IDictionary]) { return $Map.Contains($Key) }
  return $null -ne $Map.PSObject.Properties[$Key]
}

function Get-MapKeys {
  param([object]$Map)
  if ($null -eq $Map) { return @() }
  if ($Map -is [string] -or $Map.GetType().IsPrimitive) { return @() }
  if ($Map -is [System.Collections.IDictionary]) { return @($Map.Keys) }
  if ($Map -is [System.Collections.IEnumerable]) { return @() }
  return @($Map.PSObject.Properties | ForEach-Object { $_.Name })
}

function Copy-Map {
  param([object]$Map)
  $copy = [ordered]@{}
  if ($Map -is [System.Collections.IDictionary]) {
    foreach ($key in $Map.Keys) {
      $copy[$key] = $Map[$key]
    }
  } elseif ($null -ne $Map) {
    foreach ($property in $Map.PSObject.Properties) {
      $copy[$property.Name] = $property.Value
    }
  }
  return $copy
}

function Get-ProfileYaml {
  param(
    [string]$Text,
    [string]$TypeName
  )
  $rootByType = @{ "character" = "character_profile" }
  $typeKey = $TypeName.ToLowerInvariant()
  if (-not $rootByType.ContainsKey($typeKey)) { return @{} }
  $rootKey = $rootByType[$typeKey]
  $relationshipBlock = Get-RelationshipYaml $Text
  foreach ($block in Get-FencedYamlBlocks $Text) {
    if ($relationshipBlock -and $block.Text -eq $relationshipBlock) { continue }
    try {
      $parsed = ConvertFrom-Yaml -Yaml $block.Text -Ordered
    } catch {
      continue
    }
    if (Test-MapHasKey $parsed $rootKey) {
      return (Get-MapValue $parsed $rootKey @{})
    }
  }
  return @{}
}

function ConvertTo-NullableInt {
  param([object]$Value)
  if ($null -eq $Value) { return $null }
  $text = ([string]$Value).Trim()
  if (-not $text -or $text.ToUpperInvariant() -eq "TBD") { return $null }
  $number = 0
  if ([int]::TryParse($text, [ref]$number)) { return $number }
  return $null
}

function Get-BoundaryLabel {
  param([object]$Spec)
  $medium = ([string]$Spec.medium).ToLowerInvariant()
  if ($medium -eq "novel") {
    $parts = @("novel")
    if ($Spec.max_volume) { $parts += "V$($Spec.max_volume)" }
    if ($Spec.max_chapter) { $parts += "Ch$($Spec.max_chapter)" }
    return ($parts -join " ")
  }
  if ($medium -eq "donghua") {
    $parts = @("donghua")
    if ($Spec.max_season) { $parts += "S$($Spec.max_season)" }
    if ($Spec.max_episode) { $parts += "E$($Spec.max_episode)" }
    if ($Spec.max_release_order) { $parts += "Release $($Spec.max_release_order)" }
    return ($parts -join " ")
  }
  return $Spec.medium
}

function Get-BoundaryPosition {
  param([object]$Spec)
  return [ordered]@{
    medium = ([string]$Spec.medium).ToLowerInvariant()
    volume = ConvertTo-NullableInt $Spec.max_volume
    chapter = ConvertTo-NullableInt $Spec.max_chapter
    season = ConvertTo-NullableInt $Spec.max_season
    episode = ConvertTo-NullableInt $Spec.max_episode
    release_order = ConvertTo-NullableInt $Spec.max_release_order
  }
}

function Get-NormalizedMedium {
  param([object]$Value)
  if ($null -eq $Value) { return "" }
  return ([string]$Value).Trim().ToLowerInvariant()
}

function Get-PositionFromMetadata {
  param([string]$Value)
  $position = [ordered]@{ medium = "" }
  $mediumMatch = [regex]::Match($Value, "\b(Novel|Donghua)\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  if ($mediumMatch.Success) { $position["medium"] = $mediumMatch.Groups[1].Value.ToLowerInvariant() }
  $volume = [regex]::Match($Value, "\bV(?:ol(?:ume)?)?\s*(\d+)\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  $chapter = [regex]::Match($Value, "\bCh(?:apter)?\s*(\d+)\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  $season = [regex]::Match($Value, "\bS(?:eason)?\s*(\d+)\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  $episode = [regex]::Match($Value, "\bE(?:pisode)?\s*(\d+)\b", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  if ($volume.Success) { $position["volume"] = $volume.Groups[1].Value }
  if ($chapter.Success) { $position["chapter"] = $chapter.Groups[1].Value }
  if ($season.Success) { $position["season"] = $season.Groups[1].Value }
  if ($episode.Success) { $position["episode"] = $episode.Groups[1].Value }
  return $position
}

function Get-EntryPosition {
  param([object]$Entry)
  if (@(Get-MapKeys $Entry).Count -eq 0) { return @{} }
  $from = Get-MapValue $Entry "from" $null
  $positionValue = Get-MapValue $Entry "position" $null
  $visibility = Get-MapValue $Entry "visibility" $null
  if (@(Get-MapKeys $from).Count -gt 0) {
    $data = Copy-Map $from
  } elseif (@(Get-MapKeys $positionValue).Count -gt 0) {
    $data = Copy-Map $positionValue
  } elseif (@(Get-MapKeys $visibility).Count -gt 0 -and @(Get-MapKeys (Get-MapValue $visibility "from" $null)).Count -gt 0) {
    $data = Copy-Map (Get-MapValue $visibility "from" @{})
  } else {
    $data = Copy-Map $Entry
  }
  if (-not (Test-MapHasKey $data "medium") -and (Get-MapValue $Entry "medium" "")) {
    $data["medium"] = Get-MapValue $Entry "medium" ""
  }
  return $data
}

function Test-PositionVisible {
  param(
    [object]$Position,
    [object]$Boundary
  )
  $medium = Get-NormalizedMedium (Get-MapValue $Position "medium" "")
  if ($medium -and $medium -ne $Boundary["medium"]) { return $false }
  if ($Boundary["medium"] -eq "novel") {
    $volume = ConvertTo-NullableInt (Get-MapValue $Position "volume" "")
    $chapter = ConvertTo-NullableInt (Get-MapValue $Position "chapter" "")
    $maxVolume = $Boundary["volume"]
    $maxChapter = $Boundary["chapter"]
    if ($null -eq $volume -and $null -eq $chapter) { return $false }
    if ($null -ne $maxVolume -and $null -ne $volume) {
      if ($volume -gt $maxVolume) { return $false }
      if ($volume -lt $maxVolume) { return $true }
    }
    if ($null -ne $maxChapter -and $null -ne $chapter) { return $chapter -le $maxChapter }
    return ($null -ne $maxVolume -and $null -ne $volume -and $volume -le $maxVolume)
  }
  if ($Boundary["medium"] -eq "donghua") {
    $releaseOrder = ConvertTo-NullableInt (Get-MapValue $Position "release_order" "")
    $episode = ConvertTo-NullableInt (Get-MapValue $Position "episode" "")
    $season = ConvertTo-NullableInt (Get-MapValue $Position "season" "")
    $maxReleaseOrder = $Boundary["release_order"]
    $maxEpisode = $Boundary["episode"]
    $maxSeason = $Boundary["season"]
    if ($null -ne $releaseOrder -and $null -ne $maxReleaseOrder) { return $releaseOrder -le $maxReleaseOrder }
    if ($null -eq $season -and $null -eq $episode) { return $false }
    if ($null -ne $maxSeason -and $null -ne $season) {
      if ($season -gt $maxSeason) { return $false }
      if ($season -lt $maxSeason) { return $true }
    }
    if ($null -ne $maxEpisode -and $null -ne $episode) { return $episode -le $maxEpisode }
    return ($null -ne $maxSeason -and $null -ne $season -and $season -le $maxSeason)
  }
  return $false
}

function Get-RowVisibleAvailability {
  param(
    [object]$Row,
    [object]$Boundary
  )
  $entries = Get-MapValue $Row "availability" @()
  if (-not ($entries -is [System.Collections.IEnumerable]) -or $entries -is [string]) { return @() }
  $visible = @()
  foreach ($entry in @($entries)) {
    if (@(Get-MapKeys $entry).Count -gt 0 -and (Test-PositionVisible (Get-EntryPosition $entry) $Boundary)) {
      $visible += $entry
    }
  }
  return @($visible)
}

function Test-RowVisible {
  param(
    [object]$Row,
    [object]$Boundary
  )
  if (@(Get-MapKeys $Row).Count -eq 0) { return $false }
  if (Test-MapHasKey $Row "availability") { return @((Get-RowVisibleAvailability $Row $Boundary)).Count -gt 0 }
  $to = Get-MapValue $Row "to" $null
  if (@(Get-MapKeys $to).Count -gt 0) {
    $endPosition = Copy-Map $to
    if (-not (Test-MapHasKey $endPosition "medium") -and (Get-MapValue $Row "medium" "")) {
      $endPosition["medium"] = Get-MapValue $Row "medium" ""
    }
    return Test-PositionVisible $endPosition $Boundary
  }
  foreach ($key in @("visibility", "from", "position")) {
    if (Test-MapHasKey $Row $key) { return Test-PositionVisible (Get-EntryPosition $Row) $Boundary }
  }
  $sourceRefs = Get-MapValue $Row "source_refs" @()
  if ($sourceRefs -is [System.Collections.IEnumerable] -and -not ($sourceRefs -is [string])) {
    foreach ($ref in @($sourceRefs)) {
      if ($ref -is [System.Collections.IDictionary] -and (Test-PositionVisible (Get-EntryPosition $ref) $Boundary)) { return $true }
    }
  }
  return $false
}

function Merge-RowAtBoundary {
  param(
    [object]$Row,
    [object]$Boundary
  )
  $merged = Copy-Map $Row
  $visible = @(Get-RowVisibleAvailability $Row $Boundary)
  if ($visible.Count -gt 0) {
    $latest = $visible[$visible.Count - 1]
    foreach ($key in Get-MapKeys $latest) {
      if ($key -in @("medium", "from", "notes")) { continue }
      $value = Get-MapValue $latest $key ""
      if ($null -ne $value -and ([string]$value) -ne "") { $merged[$key] = $value }
    }
    $merged["_visible_availability"] = @($visible)
  }
  return $merged
}

function Get-FilteredProfileRowsForBoundary {
  param(
    [object]$Profile,
    [object]$Boundary
  )
  $filtered = [ordered]@{}
  if (-not ($Profile -is [System.Collections.IDictionary])) { return $filtered }
  foreach ($section in $Profile.Keys) {
    $rows = $Profile[$section]
    if ($rows -is [System.Collections.IDictionary] -or @(Get-MapKeys $rows).Count -gt 0) {
      if ((Test-MapHasKey $rows "availability") -or (Test-MapHasKey $rows "source_refs") -or (Test-MapHasKey $rows "position") -or (Test-MapHasKey $rows "visibility") -or (Test-MapHasKey $rows "from") -or (Test-MapHasKey $rows "to")) {
        $rowCandidates = @($rows)
      } else {
        continue
      }
    } elseif ($rows -is [System.Collections.IEnumerable] -and -not ($rows -is [string])) {
      $rowCandidates = @($rows)
    } else {
      continue
    }
    $visibleRows = @()
    foreach ($row in @($rowCandidates)) {
      if ((Test-RowVisible $row $Boundary)) {
        $visibleRows += Merge-RowAtBoundary $row $Boundary
      }
    }
    $filtered[$section] = @($visibleRows)
  }
  return $filtered
}

function Test-PageVisibleAtBoundary {
  param(
    [object]$Note,
    [object]$Boundary
  )
  $visibleFrom = Get-MapValue $Note.metadata "subject_visible_from" ""
  if (-not $visibleFrom) { return $true }
  return Test-PositionVisible (Get-PositionFromMetadata $visibleFrom) $Boundary
}

function Format-Position {
  param([object]$Position)
  if (@(Get-MapKeys $Position).Count -eq 0) { return "" }
  $medium = Get-NormalizedMedium (Get-MapValue $Position "medium" "")
  if ($medium -eq "novel" -or (Get-MapValue $Position "chapter" "") -or (Get-MapValue $Position "volume" "")) {
    $parts = @()
    $volumeValue = Get-MapValue $Position "volume" ""
    $chapterValue = Get-MapValue $Position "chapter" ""
    if ($volumeValue) { $parts += "V$volumeValue" }
    if ($chapterValue) { $parts += "Ch$chapterValue" }
    return ($parts -join " ")
  }
  if ($medium -eq "donghua" -or (Get-MapValue $Position "episode" "") -or (Get-MapValue $Position "season" "")) {
    $parts = @()
    $seasonValue = Get-MapValue $Position "season" ""
    $episodeValue = Get-MapValue $Position "episode" ""
    $releaseOrderValue = Get-MapValue $Position "release_order" ""
    if ($seasonValue) { $parts += "S$seasonValue" }
    if ($episodeValue) { $parts += "E$episodeValue" }
    if ($releaseOrderValue) { $parts += "Release $releaseOrderValue" }
    return ($parts -join " ")
  }
  $parts = @()
  foreach ($key in $Position.Keys) {
    if ($null -ne $Position[$key] -and ([string]$Position[$key]) -ne "") { $parts += "$key`: $($Position[$key])" }
  }
  return ($parts -join ", ")
}

function ConvertTo-TableValue {
  param([object]$Value)
  if ($null -eq $Value) { return "" }
  if (@(Get-MapKeys $Value).Count -gt 0) { return Format-Position $Value }
  if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
    $parts = @()
    foreach ($item in @($Value)) { $parts += ConvertTo-TableValue $item }
    return ($parts -join "<br>")
  }
  return ([string]$Value).Replace("|", "\|").Replace("`r`n", "<br>").Replace("`n", "<br>")
}

function Format-AvailabilityProgression {
  param([object]$Row)
  $entries = Get-MapValue $Row "_visible_availability" @()
  $parts = @()
  if ($entries -is [System.Collections.IEnumerable] -and -not ($entries -is [string]) -and @($entries).Count -gt 0) {
    foreach ($entry in @($entries)) {
      $position = Format-Position (Get-EntryPosition $entry)
      $status = Get-MapValue $entry "status" (Get-MapValue $entry "possession_status" (Get-MapValue $entry "access_status" (Get-MapValue $entry "outcome_status" "")))
      $confidence = Get-MapValue $entry "confidence" ""
      $details = @($status, $confidence) | Where-Object { $_ }
      if ($details.Count -gt 0) { $parts += "$position`: $($details -join ' / ')" } else { $parts += $position }
    }
    return ($parts -join "<br>")
  }
  $positionValue = Get-MapValue $Row "position" $null
  if (@(Get-MapKeys $positionValue).Count -gt 0) {
    $position = Format-Position (Get-EntryPosition $Row)
    $status = Get-MapValue $Row "status" ""
    $confidence = Get-MapValue $Row "confidence" ""
    $details = @($status, $confidence) | Where-Object { $_ }
    if ($position) {
      if ($details.Count -gt 0) { $parts += "$position`: $($details -join ' / ')" } else { $parts += $position }
    }
  }
  $sourceRefs = Get-MapValue $Row "source_refs" @()
  if ($sourceRefs -is [System.Collections.IEnumerable] -and -not ($sourceRefs -is [string])) {
    foreach ($ref in @($sourceRefs)) {
      if (-not ($ref -is [System.Collections.IDictionary])) { continue }
      $position = Format-Position $ref
      if ($position -and -not ($parts | Where-Object { $_.StartsWith($position) })) { $parts += "$position`: source-ref" }
    }
  }
  $graphDisplay = Get-MapValue $Row "graph_display" $null
  if (@(Get-MapKeys $graphDisplay).Count -gt 0) {
    $visibleFrom = Get-MapValue $graphDisplay "visible_from" $null
    $resolvesTo = Get-MapValue $graphDisplay "resolves_to_canonical_at" $null
    if (@(Get-MapKeys $visibleFrom).Count -gt 0) { $parts += "graph visible from $(Format-Position $visibleFrom)" }
    if (@(Get-MapKeys $resolvesTo).Count -gt 0) { $parts += "resolves to canonical at $(Format-Position $resolvesTo)" }
  }
  return ($parts -join "<br>")
}

function Get-GraphDisplayForBoundary {
  param(
    [object]$Note,
    [object]$Filtered,
    [bool]$PageVisible
  )
  $beats = @(Get-MapValue $Filtered "first_appearance_beats" @())
  $graphRows = @()
  foreach ($beat in $beats) {
    $graphDisplay = Get-MapValue $beat "graph_display" $null
    $behavior = ""
    $label = ""
    if (@(Get-MapKeys $graphDisplay).Count -gt 0) {
      $behavior = Get-MapValue $graphDisplay "behavior" ""
      $label = Get-MapValue $graphDisplay "label" ""
    }
    if ($behavior) {
      $graphRows += [pscustomobject]@{
        behavior = $behavior
        label = $label
        title = Get-MapValue $beat "title" ""
      }
    }
  }
  if ($graphRows.Count -gt 0) {
    $preferred = $graphRows[$graphRows.Count - 1]
    return [ordered]@{
      node_visible = if ($preferred.behavior -ne "hidden") { "yes" } else { "no" }
      visibility = $preferred.behavior
      label = if ($preferred.label) { $preferred.label } else { $Note.title }
      source = $preferred.title
    }
  }
  if ($PageVisible) {
    return [ordered]@{
      node_visible = "yes"
      visibility = "canonical-node"
      label = $Note.title
      source = "page visibility"
    }
  }
  return [ordered]@{
    node_visible = "no"
    visibility = "hidden"
    label = ""
    source = "before page visibility"
  }
}

function ConvertTo-GenerationStatsMarkdown {
  param(
    [object]$Note,
    [object]$Spec,
    [bool]$PageVisible,
    [object]$Filtered
  )
  $graphDisplay = Get-GraphDisplayForBoundary $Note $Filtered $PageVisible
  $rows = @(
    @("Boundary", (Get-BoundaryLabel $Spec)),
    @("Canonical page visible", $(if ($PageVisible) { "yes" } else { "no" })),
    @("Graph node visible", $graphDisplay["node_visible"]),
    @("Graph visibility behavior", $graphDisplay["visibility"]),
    @("Graph label", $graphDisplay["label"]),
    @("Graph visibility source", $graphDisplay["source"]),
    @("Visible first appearance beats", "$(@(Get-MapValue $Filtered "first_appearance_beats" @()).Count)"),
    @("Visible timeline entries", "$(@(Get-MapValue $Filtered "timeline_entries" @()).Count)"),
    @("Visible relationship rows", "$(@(Get-MapValue $Filtered "relationships" @()).Count)")
  )
  $lines = @("## Generation Stats", "", "| Field | Value |", "|---|---|")
  foreach ($row in $rows) {
    $lines += "| $(ConvertTo-TableValue $row[0]) | $(ConvertTo-TableValue $row[1]) |"
  }
  $lines += ""
  return @($lines)
}

function ConvertTo-BoundedTableMarkdown {
  param(
    [string]$Title,
    [object[]]$Rows,
    [object[]]$Columns
  )
  $lines = @("## $Title", "")
  if (@($Rows).Count -eq 0) {
    $lines += "- No rows visible at this boundary."
    $lines += ""
    return @($lines)
  }
  $header = @($Columns | ForEach-Object { $_[0] }) + @("Availability Progression")
  $lines += "| $($header -join ' | ') |"
  $lines += "|" + (($header | ForEach-Object { "---" }) -join "|") + "|"
  foreach ($row in @($Rows)) {
    $values = @()
    foreach ($column in $Columns) {
      $values += ConvertTo-TableValue (Get-MapValue $row $column[1] "")
    }
    $values += ConvertTo-TableValue (Format-AvailabilityProgression $row)
    $lines += "| $($values -join ' | ') |"
  }
  $lines += ""
  return @($lines)
}

$BoundedCharacterTables = @(
  [pscustomobject]@{ Title = "First Appearance Beats"; Key = "first_appearance_beats"; Optional = $false; Columns = @(@("Title", "title"), @("Type", "beat_type"), @("State", "reader_knowledge_state"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Identity / Role"; Key = "identities"; Optional = $false; Columns = @(@("Field", "field"), @("Value", "value"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Physical Profile"; Key = "physical_profile"; Optional = $false; Columns = @(@("Field", "field"), @("Value", "value"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Status / Origin / Location"; Key = "status_origin_location"; Optional = $false; Columns = @(@("Field", "field"), @("Value", "value"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Affiliations"; Key = "affiliations"; Optional = $false; Columns = @(@("Organization", "organization"), @("Target", "target"), @("Relationship", "relationship"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Pathway State"; Key = "pathway_state"; Optional = $false; Columns = @(@("Pathway", "pathway"), @("Target", "target"), @("Relationship", "relationship"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Sequence State"; Key = "sequence_state"; Optional = $false; Columns = @(@("Sequence", "sequence"), @("Name", "sequence_name"), @("Pathway", "related_pathway"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Associated Tarot Card"; Key = "associated_tarot_card"; Optional = $true; Columns = @(@("Card", "card_name"), @("Number", "card_number"), @("Target", "target"), @("Alias", "identity_alias"), @("Association", "association_type"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Mythical Creature Form State"; Key = "mythical_creature_form_state"; Optional = $true; Columns = @(@("Form State", "form_state"), @("Stage", "version_stage"), @("Pathway", "related_pathway"), @("Sequence Threshold", "sequence_threshold"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Uniqueness State"; Key = "uniqueness_state"; Optional = $true; Columns = @(@("Uniqueness", "uniqueness"), @("Relationship", "relationship_state"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Ability State"; Key = "ability_state"; Optional = $true; Columns = @(@("Field", "field"), @("Value", "value"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Abilities"; Key = "ability_index"; Optional = $false; Columns = @(@("Ability", "ability"), @("Source", "source"), @("Target", "target"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Equipment / Artifacts / Items"; Key = "equipment_artifacts"; Optional = $false; Columns = @(@("Item", "item"), @("Target", "target"), @("Type", "type"), @("Possession", "possession_status"), @("Significance", "item_significance"), @("Graph", "graph_relevance")) },
  [pscustomobject]@{ Title = "Knowledge Sources & Documents"; Key = "knowledge_sources_documents"; Optional = $true; Columns = @(@("Source", "source"), @("Target", "target"), @("Type", "type"), @("Access", "access_status"), @("Significance", "source_significance"), @("Graph", "graph_relevance")) },
  [pscustomobject]@{ Title = "Personality"; Key = "personality"; Optional = $false; Columns = @(@("Trait", "trait"), @("Evidence", "evidence"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Relationships"; Key = "relationships"; Optional = $false; Columns = @(@("Target", "target"), @("Relationship", "relationship"), @("Status", "status"), @("Confidence", "confidence"), @("Notes", "notes")) },
  [pscustomobject]@{ Title = "Messengers / Servants / Companions"; Key = "messengers_servants_companions"; Optional = $true; Columns = @(@("Entity", "entity"), @("Label", "label"), @("Type", "type"), @("Function", "function"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Prayers & Ritual Access"; Key = "prayers_ritual_access"; Optional = $true; Columns = @(@("Label", "label"), @("Type", "type"), @("Function", "function"), @("Concept Link", "concept_link"), @("Status", "status"), @("Confidence", "confidence")) },
  [pscustomobject]@{ Title = "Major Events"; Key = "major_events_fights"; Optional = $false; Columns = @(@("Event", "event"), @("Target", "target"), @("Type", "event_type"), @("Part", "event_part"), @("Role", "role"), @("Outcome", "outcome_status")) },
  [pscustomobject]@{ Title = "Timeline Entries"; Key = "timeline_entries"; Optional = $false; Columns = @(@("ID", "id"), @("Title", "title"), @("Type", "entry_type"), @("Summary", "summary"), @("Why It Matters", "why_it_matters")) }
)

function Get-TimelineProseBlocks {
  param([string]$Text)
  $section = Get-MarkdownSection $Text "Chronological Development"
  $blocks = @{}
  if ([string]::IsNullOrWhiteSpace($section)) { return $blocks }
  foreach ($match in [regex]::Matches($section, "(?ms)^(#### .+?`n<!-- timeline_id:\s*([a-zA-Z0-9_-]+)\s*-->`n.*?)(?=^#### |\z)")) {
    $blocks[$match.Groups[2].Value] = $match.Groups[1].Value.Trim()
  }
  return $blocks
}

function ConvertTo-BoundedTimelineProseMarkdown {
  param(
    [string]$Text,
    [object[]]$VisibleTimelineRows
  )
  $blocks = Get-TimelineProseBlocks $Text
  $visibleIds = @($VisibleTimelineRows | ForEach-Object { Get-MapValue $_ "id" "" } | Where-Object { $_ })
  $lines = @("## Visible Timeline Prose", "")
  if ($blocks.Count -eq 0) {
    $lines += "- No timeline prose blocks found."
    $lines += ""
    return @($lines)
  }
  $emitted = $false
  foreach ($timelineId in $visibleIds) {
    if ($blocks.ContainsKey($timelineId)) {
      $lines += $blocks[$timelineId]
      $lines += ""
      $emitted = $true
    }
  }
  if (-not $emitted) {
    $lines += "- No timeline prose sections visible at this boundary."
    $lines += ""
  }
  $omitted = @($blocks.Keys | Where-Object { $_ -notin $visibleIds } | Sort-Object)
  $lines += "## Omitted Timeline IDs"
  $lines += ""
  if ($omitted.Count -gt 0) {
    foreach ($timelineId in $omitted) { $lines += "- ``$timelineId``" }
  } else {
    $lines += "- None."
  }
  $lines += ""
  return @($lines)
}

function ConvertTo-BoundedCharacterPageMarkdown {
  param(
    [string]$RepoRoot,
    [object]$Note,
    [object]$Spec
  )
  $text = Read-TextFile $Note.source_path
  $profile = Get-ProfileYaml $text $Note.type_name
  $boundary = Get-BoundaryPosition $Spec
  $pageVisible = Test-PageVisibleAtBoundary $Note $boundary
  $filtered = Get-FilteredProfileRowsForBoundary $profile $boundary
  if (-not $pageVisible -and -not $Spec.include_anonymous_preview) {
    foreach ($key in @($filtered.Keys)) { $filtered[$key] = @() }
  }
  if (-not $pageVisible) {
    $previewRows = @()
    foreach ($row in @(Get-MapValue $filtered "first_appearance_beats" @())) {
      $graphDisplay = Get-MapValue $row "graph_display" $null
      if (@(Get-MapKeys $graphDisplay).Count -gt 0 -and (Get-MapValue $graphDisplay "behavior" "") -eq "anonymized-node") {
        $previewRows += $row
      }
    }
    $filtered["first_appearance_beats"] = @($previewRows)
    foreach ($key in @($filtered.Keys)) {
      if ($key -ne "first_appearance_beats") { $filtered[$key] = @() }
    }
  }

  $title = if ($Spec.name) { $Spec.name } else { $Note.title }
  $boundaryLabel = Get-BoundaryLabel $Spec
  $lines = @(
    "---",
    "generated: true",
    "generated_type: bounded-page-qa",
    "source_file: $(ConvertTo-YamlQuote $Note.relative_source)",
    "source_slug: $(ConvertTo-YamlQuote $Note.slug)",
    "type: $(ConvertTo-YamlQuote $Note.type_name.ToLowerInvariant())",
    "boundary: $(ConvertTo-YamlQuote $boundaryLabel)",
    "canonical_page_visible: $(([string]$pageVisible).ToLowerInvariant())",
    "---",
    "",
    "# $title - Bounded QA ($boundaryLabel)",
    "",
    "> Generated QA projection. Canonical source remains the glossary page.",
    "",
    "- Canonical Source: $(Format-SourceLink $Note.relative_source)",
    "- Canonical Page Visible At Boundary: $(if ($pageVisible) { 'yes' } else { 'no' })"
  )
  if (-not $pageVisible) {
    $lines += "- QA Note: canonical page body is hidden at this boundary; only explicitly modeled anonymous preview beats are shown."
  }
  $lines += ""
  $lines += ConvertTo-GenerationStatsMarkdown $Note $Spec $pageVisible $filtered
  foreach ($table in $BoundedCharacterTables) {
    if ($table.Optional -and -not (Test-MapHasKey $profile $table.Key) -and -not (Test-MapHasKey $filtered $table.Key)) { continue }
    $lines += ConvertTo-BoundedTableMarkdown $table.Title @(Get-MapValue $filtered $table.Key @()) $table.Columns
  }
  if ($pageVisible) {
    $lines += ConvertTo-BoundedTimelineProseMarkdown $text @(Get-MapValue $filtered "timeline_entries" @())
  } else {
    $lines += @("## Visible Timeline Prose", "", "- Canonical timeline prose hidden before page visibility.", "")
  }
  return ($lines -join "`n")
}

function Write-BoundedPages {
  param(
    [string]$RepoRoot,
    [string]$GeneratedDir,
    [hashtable]$Notes,
    [object[]]$Specs
  )
  if (@($Specs).Count -eq 0) { return }
  $boundedDir = Join-Path $GeneratedDir "bounded-pages"
  foreach ($spec in @($Specs)) {
    if (-not $Notes.ContainsKey($spec.slug)) {
      $unknownDir = Join-Path $boundedDir "_Unknown"
      New-Item -ItemType Directory -Path $unknownDir -Force | Out-Null
      $fileStemSource = if ($spec.file_stem) { $spec.file_stem } elseif ($spec.name) { $spec.name } else { $spec.slug }
      $fileStem = ConvertTo-SafeFileName $fileStemSource
      $content = @(
        "---",
        "generated: true",
        "generated_type: bounded-page-qa",
        "source_slug: $(ConvertTo-YamlQuote $spec.slug)",
        "boundary: $(ConvertTo-YamlQuote (Get-BoundaryLabel $spec))",
        "canonical_page_visible: false",
        "---",
        "",
        "# Unknown Bounded Page - $($spec.slug)",
        "",
        "- Requested canonical source slug does not exist in the generated note set.",
        ""
      ) -join "`n"
      Write-TextFile (Join-Path $unknownDir "$fileStem.md") $content
      continue
    }

    $note = $Notes[$spec.slug]
    $outputFolder = Join-Path $boundedDir $note.export_folder
    New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
    $boundaryStem = if ($spec.max_chapter) { "chapter-$($spec.max_chapter)" } else { ConvertTo-SafeSlug (Get-BoundaryLabel $spec) "boundary" }
    $defaultStem = "$($note.export_file_stem) - $boundaryStem"
    $fileStem = ConvertTo-SafeFileName $(if ($spec.file_stem) { $spec.file_stem } else { $defaultStem })
    if ($note.type_name.ToLowerInvariant() -eq "character") {
      $content = ConvertTo-BoundedCharacterPageMarkdown $RepoRoot $note $spec
    } else {
      $content = @(
        "---",
        "generated: true",
        "generated_type: bounded-page-qa",
        "source_file: $(ConvertTo-YamlQuote $note.relative_source)",
        "source_slug: $(ConvertTo-YamlQuote $note.slug)",
        "type: $(ConvertTo-YamlQuote $note.type_name.ToLowerInvariant())",
        "boundary: $(ConvertTo-YamlQuote (Get-BoundaryLabel $spec))",
        "---",
        "",
        "# $($note.title) - Bounded QA ($(Get-BoundaryLabel $spec))",
        "",
        "- Bounded page rendering is currently implemented for character pages only.",
        ""
      ) -join "`n"
    }
    Write-TextFile (Join-Path $outputFolder "$fileStem.md") $content
  }
}

function Write-ObsidianExport {
  param(
    [string]$RepoRoot,
    [string]$ExportPath,
    [bool]$CleanOutput,
    [hashtable]$Notes,
    [object[]]$Relationships,
    [object[]]$DataReferences,
    [hashtable]$DataProjections,
    [object[]]$BoundedGraphSpecs,
    [object[]]$BoundedPageSpecs
  )
  $exportPath = Assert-SafeOutputPath $RepoRoot $ExportPath
  if ($CleanOutput -and (Test-Path -LiteralPath $exportPath)) {
    Remove-Item -LiteralPath $exportPath -Recurse -Force
  }
  New-Item -ItemType Directory -Path $exportPath -Force | Out-Null
  $folders = @($TypeFolders.Values + @("Other", "_Generated") | Sort-Object -Unique)
  foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path (Join-Path $exportPath $folder) -Force | Out-Null
  }
  foreach ($note in $Notes.Values) {
    $fileName = "$($note.export_file_stem).md"
    Write-TextFile (Join-Path (Join-Path $exportPath $note.export_folder) $fileName) (ConvertTo-NoteMarkdown $note $Notes $Relationships $DataReferences)
  }

  $generatedDir = Join-Path $exportPath "_Generated"
  Write-TextFile (Join-Path $generatedDir "relationship-index.md") (ConvertTo-RelationshipIndex $Relationships $Notes)
  Write-TextFile (Join-Path $generatedDir "QA-relationship-graph.mmd") (ConvertTo-LabeledRelationshipGraph $Relationships $Notes)
  Write-TextFile (Join-Path $generatedDir "QA-relationship-node-graph.mmd") (ConvertTo-RelationshipNodeGraph $Relationships $Notes $DataProjections)
  Write-TextFile (Join-Path $generatedDir "visualization-relationship-graph.mmd") (ConvertTo-VisualizationRelationshipGraph $Relationships $Notes $DataProjections)
  Write-RepoRefreshCheck $RepoRoot $generatedDir
  Write-BoundedGraphs $RepoRoot $generatedDir $BoundedGraphSpecs
  Write-BoundedPages $RepoRoot $generatedDir $Notes $BoundedPageSpecs
  Write-TextFile (Join-Path $generatedDir "data-reference-index.md") (ConvertTo-DataReferenceIndex $DataReferences $Notes)
  Write-TextFile (Join-Path $generatedDir "orphan-report.md") (ConvertTo-OrphanReport $Notes $Relationships $DataReferences)
  Write-TextFile (Join-Path $generatedDir "suspicious-edges.md") (ConvertTo-SuspiciousEdges $Notes $Relationships)
}

function Invoke-DisposableCacheCleanup {
  param([string]$RepoRoot)
  try {
    $cleanScript = Join-Path $RepoRoot "Tools/Clean-TempFiles.ps1"
    if (Test-Path -LiteralPath $cleanScript) {
      powershell -NoProfile -ExecutionPolicy Bypass -File $cleanScript -Delete | Out-Null
    }
  } catch {
    return
  }
}

$repoRoot = (Resolve-Path -LiteralPath $Root).Path
$exportPath = if ([System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir } else { Join-Path $repoRoot $OutputDir }
$boundedGraphSpecs = @(ConvertFrom-BoundedGraphSpecs $BoundedGraph)
$boundedPageSpecs = @(ConvertFrom-BoundedPageSpecs $BoundedPage)
Import-YamlModuleForBoundedPages $boundedPageSpecs
$discovered = Get-CanonicalNotes $repoRoot ([bool]$IncludeStubs)
Write-ObsidianExport $repoRoot $exportPath ([bool]$Clean) $discovered.Notes $discovered.Relationships $discovered.DataReferences $discovered.DataProjections $boundedGraphSpecs $boundedPageSpecs

$orphanData = Get-OrphanAnalysis $discovered.Notes $discovered.Relationships $discovered.DataReferences
$suspiciousData = Get-SuspiciousEdgeAnalysis $discovered.Relationships $discovered.Notes
$summary = [ordered]@{
  notes = $discovered.Notes.Count
  relationships = @($discovered.Relationships).Count
  data_references = @($discovered.DataReferences).Count
  output_dir = (Resolve-Path -LiteralPath $exportPath).Path
  unknown_relationship_sources = @($orphanData.unknown_relationship_sources).Count
  unknown_relationship_targets = @($orphanData.unknown_relationship_targets).Count
  unknown_data_targets = @($orphanData.unknown_data_targets).Count
  self_loops = @($suspiciousData.self_loops).Count
  duplicate_edge_groups = @($suspiciousData.duplicate_edges).Count
  missing_reciprocals = @($suspiciousData.missing_reciprocals).Count
  bounded_graphs = @($boundedGraphSpecs).Count
  bounded_pages = @($boundedPageSpecs).Count
}

if ($Json) {
  $summary | ConvertTo-Json -Depth 5
  Invoke-DisposableCacheCleanup $repoRoot
  exit 0
}

Write-Output "Generated $($summary.notes) Obsidian QA notes."
Write-Output "Relationship Seeds: $($summary.relationships); data block references: $($summary.data_references)."
Write-Output "Output: $($summary.output_dir)"
Write-Output ("QA: {0} unknown relationship sources, {1} unknown relationship targets, {2} unknown data targets, {3} self loops, {4} duplicate edge groups, {5} missing expected reciprocals." -f $summary.unknown_relationship_sources, $summary.unknown_relationship_targets, $summary.unknown_data_targets, $summary.self_loops, $summary.duplicate_edge_groups, $summary.missing_reciprocals)
Invoke-DisposableCacheCleanup $repoRoot
