param(
  [string]$Root = ".",
  [string]$OutputDir = "Obsidian_Export",
  [switch]$IncludeStubs,
  [switch]$Clean,
  [switch]$Json
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
  "file",
  "location",
  "pathway",
  "related_ats_formula",
  "related_deity",
  "source",
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
  }
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

function Get-CanonicalNotes {
  param(
    [string]$RepoRoot,
    [bool]$IncludeStubPages
  )
  $notes = @{}
  $relationships = @()
  $dataReferences = @()

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
      $typeName = $metadata["type"]
      $note = [pscustomobject]@{
        slug = $slug
        title = Get-FirstHeading $text (ConvertTo-SlugTitle $slug)
        source_path = $file.FullName
        relative_source = $relativeSource
      metadata = $metadata
      relationships = $noteRelationships
      data_references = $noteDataRefs
      type_name = $typeName
      export_folder = Get-ExportFolder $typeName
      export_file_stem = ConvertTo-SafeFileName (Get-FirstHeading $text (ConvertTo-SlugTitle $slug))
    }
      $notes[$slug] = $note
      $relationships += $noteRelationships
      $dataReferences += $noteDataRefs
    }
  }

  return [pscustomobject]@{
    Notes = $notes
    Relationships = @($relationships)
    DataReferences = @($dataReferences)
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
    [hashtable]$Notes
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
    $label = $parts[1]
    if ($grouped[$key].Count -gt 1) {
      $label = "$label x$($grouped[$key].Count)"
    }
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

function ConvertTo-VisualizationRelationshipGraph {
  param(
    [object[]]$Relationships,
    [hashtable]$Notes
  )
  $nodes = @{}
  foreach ($note in $Notes.Values) {
    if ($note.type_name -ne "Volume Summary") {
      $nodes[(ConvertTo-MermaidNodeId $note.slug)] = $note.title
    }
  }
  foreach ($rel in $Relationships) {
    $source = ConvertTo-MermaidNodeId $rel.source
    $target = ConvertTo-MermaidNodeId $rel.target
    if (-not $nodes.ContainsKey($source)) { $nodes[$source] = ConvertTo-SlugTitle $rel.source }
    if (-not $nodes.ContainsKey($target)) { $nodes[$target] = ConvertTo-SlugTitle $rel.target }
  }

  $seenEdges = New-Object 'System.Collections.Generic.HashSet[string]'
  $edges = @()
  foreach ($rel in $Relationships) {
    if (-not $rel.source -or -not $rel.target -or -not $rel.relationship_type) {
      continue
    }
    $source = ConvertTo-MermaidNodeId $rel.source
    $target = ConvertTo-MermaidNodeId $rel.target
    $parts = @($rel.relationship_type)
    if ($rel.start_chapter) { $parts += "ch$($rel.start_chapter)" }
    if ($rel.status -and $rel.status -ne "active") { $parts += $rel.status }
    if ($rel.confidence -and $rel.confidence -ne "confirmed") { $parts += $rel.confidence }
    $label = $parts -join " "
    $key = "$source|$label|$target"
    if ($seenEdges.Add($key)) {
      $edges += [pscustomobject]@{
        source = $source
        target = $target
        label = $label
        nodeLabel = (($parts | ForEach-Object { ConvertTo-MermaidEscaped $_ }) -join "<br/>")
      }
    }
  }

  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add("graph TD") | Out-Null
  foreach ($nodeId in @($nodes.Keys | Sort-Object)) {
    $lines.Add(('  {0}["{1}"]' -f $nodeId, (ConvertTo-MermaidEscaped $nodes[$nodeId]))) | Out-Null
  }
  $lines.Add("") | Out-Null
  $lines.Add("  classDef artifact fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef character fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef concept fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef deity fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef event fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef faction fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef location fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef pathway fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef tarot fill:#f5f3ff,stroke:#8b5cf6,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef uniqueness fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#1f2937") | Out-Null
  $lines.Add("  classDef relationship fill:#f7f2e9,stroke:#c69245,stroke-width:1.5px,color:#1f2937") | Out-Null
  $lines.Add("") | Out-Null
  foreach ($nodeId in @($nodes.Keys | Sort-Object)) {
    $className = ($nodeId -split "_")[0]
    if ($className -eq "tarot") { $className = "tarot" }
    $lines.Add("  class $nodeId $className") | Out-Null
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
  foreach ($rel in @($Relationships | Sort-Object source,relationship_type,target)) {
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
  $loops = @($Relationships | Where-Object { $_.source -and $_.source -eq $_.target })
  $seen = @{}
  foreach ($rel in $Relationships) {
    $key = "$($rel.source)|$($rel.relationship_type)|$($rel.target)"
    if (-not $seen.ContainsKey($key)) { $seen[$key] = @() }
    $seen[$key] = @($seen[$key] + $rel)
  }
  $duplicates = @($seen.Values | Where-Object { $_.Count -gt 1 })
  $edgeTypes = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($rel in $Relationships) {
    [void]$edgeTypes.Add("$($rel.source)|$($rel.relationship_type)|$($rel.target)")
  }
  $missingReciprocals = @($Relationships | Where-Object {
    $_.relationship_type -and
    $ReciprocalTypes.ContainsKey($_.relationship_type) -and
    -not $edgeTypes.Contains("$($_.target)|$($ReciprocalTypes[$_.relationship_type])|$($_.source)")
  })
  $sameTypeKnownEdges = @($Relationships | Where-Object {
    $_.source -and $_.target -and $Notes.ContainsKey($_.source) -and $Notes.ContainsKey($_.target) -and
    $Notes[$_.source].type_name -eq $Notes[$_.target].type_name
  })
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

function Write-ObsidianExport {
  param(
    [string]$RepoRoot,
    [string]$ExportPath,
    [bool]$CleanOutput,
    [hashtable]$Notes,
    [object[]]$Relationships,
    [object[]]$DataReferences
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
  Write-TextFile (Join-Path $generatedDir "QA-relationship-node-graph.mmd") (ConvertTo-RelationshipNodeGraph $Relationships $Notes)
  Write-TextFile (Join-Path $generatedDir "visualization-relationship-graph.mmd") (ConvertTo-VisualizationRelationshipGraph $Relationships $Notes)
  Write-TextFile (Join-Path $generatedDir "data-reference-index.md") (ConvertTo-DataReferenceIndex $DataReferences $Notes)
  Write-TextFile (Join-Path $generatedDir "orphan-report.md") (ConvertTo-OrphanReport $Notes $Relationships $DataReferences)
  Write-TextFile (Join-Path $generatedDir "suspicious-edges.md") (ConvertTo-SuspiciousEdges $Notes $Relationships)
}

$repoRoot = (Resolve-Path -LiteralPath $Root).Path
$exportPath = if ([System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir } else { Join-Path $repoRoot $OutputDir }
$discovered = Get-CanonicalNotes $repoRoot ([bool]$IncludeStubs)
Write-ObsidianExport $repoRoot $exportPath ([bool]$Clean) $discovered.Notes $discovered.Relationships $discovered.DataReferences

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
}

if ($Json) {
  $summary | ConvertTo-Json -Depth 5
  exit 0
}

Write-Output "Generated $($summary.notes) Obsidian QA notes."
Write-Output "Relationship Seeds: $($summary.relationships); data block references: $($summary.data_references)."
Write-Output "Output: $($summary.output_dir)"
Write-Output ("QA: {0} unknown relationship sources, {1} unknown relationship targets, {2} unknown data targets, {3} self loops, {4} duplicate edge groups, {5} missing expected reciprocals." -f $summary.unknown_relationship_sources, $summary.unknown_relationship_targets, $summary.unknown_data_targets, $summary.self_loops, $summary.duplicate_edge_groups, $summary.missing_reciprocals)
