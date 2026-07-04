param(
  [string]$EpubPath = "Source/Lord of Mysteries - Book 1.epub",
  [ValidateRange(1, 9999)]
  [int]$StartChapter = 1,
  [ValidateRange(1, 9999)]
  [int]$EndChapter = 9999,
  [int[]]$Volume,
  [ValidateSet("Chapters", "SideStories", "Appendices", "Artwork", "FrontMatter", "Other", "All")]
  [string[]]$EntryType = @("Chapters"),
  [string]$EntryNamePattern,
  [string]$Pattern,
  [int]$ContextLines = 0,
  [int]$MaxHitsPerChapter = 50,
  [Alias("Counts")]
  [switch]$CountsOnly,
  [Alias("SummaryOnly", "Summary")]
  [switch]$TermSummary,
  [switch]$IncludeLineMatchCounts,
  [switch]$RegexPattern,
  [switch]$CaseSensitive,
  [switch]$Json,
  [switch]$ListEntries
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

if (-not $ListEntries -and [string]::IsNullOrWhiteSpace($Pattern)) {
  throw "Provide -Pattern. For literal multi-term searches, separate terms with |, such as -Pattern `"Dunn|Captain|Nighthawk`". Use -ListEntries to inspect EPUB entries without a search pattern."
}

if ($ListEntries -and $TermSummary) {
  throw "-TermSummary cannot be combined with -ListEntries."
}

if ($StartChapter -gt $EndChapter) {
  throw "StartChapter cannot be greater than EndChapter."
}

if (-not (Test-Path $EpubPath)) {
  throw "EPUB not found: $EpubPath"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Convert-XhtmlToLines {
  param([string]$Xhtml)

  $plain = [regex]::Replace($Xhtml, '<[^>]+>', "`n")
  $plain = [System.Net.WebUtility]::HtmlDecode($plain)
  return @(
    $plain -split "`n" |
      ForEach-Object { $_.Trim() } |
      Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  )
}

function New-SearchRegex {
  param(
    [string[]]$Terms,
    [bool]$UseRegex,
    [bool]$MatchCase
  )

  $parts = if ($UseRegex) {
    $Terms
  } else {
    $Terms | ForEach-Object { [regex]::Escape($_) }
  }

  $options = if ($MatchCase) {
    [System.Text.RegularExpressions.RegexOptions]::None
  } else {
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
  }

  return [regex]::new(($parts -join '|'), $options)
}

function Format-Snippet {
  param(
    [string]$Text,
    [int]$MaxLength = 260
  )

  $snippet = $Text -replace '\s+', ' '
  if ($snippet.Length -gt $MaxLength) {
    return $snippet.Substring(0, $MaxLength) + "..."
  }

  return $snippet
}

function Get-MatchedTerms {
  param(
    [string]$Text,
    [string[]]$Terms,
    [bool]$UseRegex,
    [bool]$MatchCase
  )

  $matched = @()
  foreach ($term in $Terms) {
    $termRegex = New-SearchRegex @($term) $UseRegex $MatchCase
    if ($termRegex.IsMatch($Text)) {
      $matched += $term
    }
  }

  return $matched
}

function Get-TermMatchCounts {
  param(
    [string]$Text,
    [string[]]$Terms,
    [bool]$UseRegex,
    [bool]$MatchCase
  )

  $counts = [ordered]@{}
  foreach ($term in $Terms) {
    $termRegex = New-SearchRegex @($term) $UseRegex $MatchCase
    $count = $termRegex.Matches($Text).Count
    if ($count -gt 0) {
      $counts[$term] = $count
    }
  }

  return [pscustomobject]$counts
}

function New-TermSummaryRows {
  param(
    [object[]]$Documents,
    [string[]]$Terms,
    [bool]$UseRegex,
    [bool]$MatchCase
  )

  $volumeNumbers = @(
    $Documents |
      Where-Object { $null -ne $_.volume } |
      Select-Object -ExpandProperty volume -Unique |
      Sort-Object
  )

  $rows = New-Object 'System.Collections.Generic.List[object]'
  foreach ($term in $Terms) {
    $termRegex = New-SearchRegex @($term) $UseRegex $MatchCase
    $row = [ordered]@{
      term = $term
      total = 0
    }

    foreach ($volumeNumber in $volumeNumbers) {
      $row["vol_$volumeNumber"] = 0
    }

    $row["no_volume"] = 0

    foreach ($document in $Documents) {
      $count = 0
      foreach ($line in $document.lines) {
        $count += $termRegex.Matches($line).Count
      }

      if ($count -le 0) {
        continue
      }

      $row.total += $count
      if ($null -ne $document.volume) {
        $row["vol_$($document.volume)"] += $count
      } else {
        $row.no_volume += $count
      }
    }

    $rows.Add([pscustomobject]$row)
  }

  return @($rows.ToArray())
}

function Format-TermSummaryTable {
  param([object[]]$Rows)

  if ($Rows.Count -eq 0) {
    return @()
  }

  $properties = @($Rows[0].PSObject.Properties.Name)
  $widths = @{}
  foreach ($property in $properties) {
    $maxWidth = $property.Length
    foreach ($row in $Rows) {
      $value = [string]$row.$property
      if ($value.Length -gt $maxWidth) {
        $maxWidth = $value.Length
      }
    }
    $widths[$property] = $maxWidth
  }

  $header = ($properties | ForEach-Object { $_.PadRight($widths[$_]) }) -join ' | '
  $separator = ($properties | ForEach-Object { '-' * $widths[$_] }) -join '-|-'
  $lines = @($header, $separator)

  foreach ($row in $Rows) {
    $lines += (($properties | ForEach-Object {
      $value = [string]$row.$_
      if ($_ -eq 'term') {
        $value.PadRight($widths[$_])
      } else {
        $value.PadLeft($widths[$_])
      }
    }) -join ' | ')
  }

  return $lines
}

function Get-EntryTitle {
  param(
    [string[]]$Lines,
    [Nullable[int]]$Chapter
  )

  if ($Lines.Count -eq 0) {
    return $null
  }

  if ($null -ne $Chapter) {
    $chapterLine = $Lines | Where-Object { $_ -match '^Chapter\s+\d+(:|\b)' } | Select-Object -First 1
    if ($chapterLine) {
      return $chapterLine
    }
  }

  return $Lines[0]
}

function Get-EntryMetadata {
  param(
    [System.IO.Compression.ZipArchiveEntry]$Entry,
    [string[]]$Lines,
    [int]$Order
  )

  $chapter = $null
  $chapterLine = $Lines | Where-Object { $_ -match '^Chapter\s+(\d+)(:|\b)' } | Select-Object -First 1
  if ($chapterLine) {
    $chapter = [int]([regex]::Match($chapterLine, '^Chapter\s+(\d+)').Groups[1].Value)
  }

  $volume = $null
  $fileMatch = [regex]::Match($Entry.FullName, '^OEBPS/Text/volume_(\d+)_')
  if ($fileMatch.Success) {
    $volume = [int]$fileMatch.Groups[1].Value
  }

  $leafName = Split-Path $Entry.FullName -Leaf
  $entryType = if ($leafName -like 'side_stories*') {
    "SideStories"
  } elseif ($null -ne $chapter -and $null -ne $volume) {
    "Chapters"
  } elseif ($leafName -match '^(character|pathways|location)\d+\.xhtml$') {
    "Appendices"
  } elseif ($leafName -match '^(artwork\d*|cover|back_cover)\.xhtml$') {
    "Artwork"
  } elseif ($leafName -match '^(copyright|foreword)\.xhtml$') {
    "FrontMatter"
  } else {
    "Other"
  }

  $sortChapter = if ($null -ne $chapter) { $chapter } else { 100000 + $Order }

  return [pscustomobject]@{
    entry = $Entry
    path = $Entry.FullName
    file_name = $leafName
    entry_type = $entryType
    volume = $volume
    chapter = $chapter
    title = Get-EntryTitle $Lines $chapter
    order = $Order
    sort_chapter = $sortChapter
    lines = $Lines
  }
}

function Get-EpubEntries {
  param($Zip)

  $documents = New-Object 'System.Collections.Generic.List[object]'
  $order = 0
  $xhtmlEntries = $Zip.Entries | Where-Object { $_.FullName -like 'OEBPS/Text/*.xhtml' }

  foreach ($entry in $xhtmlEntries) {
    $reader = [System.IO.StreamReader]::new($entry.Open())
    try {
      $xhtml = $reader.ReadToEnd()
    } finally {
      $reader.Close()
    }

    $lines = Convert-XhtmlToLines $xhtml
    $documents.Add((Get-EntryMetadata $entry $lines $order))
    $order++
  }

  return @($documents.ToArray())
}

function Test-SelectedEntry {
  param($Document)

  $selectedTypes = if ($EntryType -contains "All") {
    @("Chapters", "SideStories", "Appendices", "Artwork", "FrontMatter", "Other")
  } else {
    $EntryType
  }

  if ($selectedTypes -notcontains $Document.entry_type) {
    return $false
  }

  if ($Volume -and ($null -eq $Document.volume -or $Volume -notcontains $Document.volume)) {
    return $false
  }

  if ($null -ne $Document.chapter -and ($Document.chapter -lt $StartChapter -or $Document.chapter -gt $EndChapter)) {
    return $false
  }

  if (-not [string]::IsNullOrWhiteSpace($EntryNamePattern)) {
    if ($Document.path -notlike $EntryNamePattern -and $Document.file_name -notlike $EntryNamePattern) {
      return $false
    }
  }

  return $true
}

function Get-DocumentLabel {
  param($Document)

  if ($null -ne $Document.chapter) {
    if ($Document.entry_type -ne "Chapters") {
      return "$($Document.entry_type) Ch $($Document.chapter)"
    }
    if ($null -ne $Document.volume) {
      return "Ch $($Document.chapter) (Vol $($Document.volume))"
    }
    return "Ch $($Document.chapter)"
  }

  return "$($Document.entry_type): $($Document.file_name)"
}

function Convert-DocumentToJsonObject {
  param($Document)

  return [pscustomobject]@{
    entry_type = $Document.entry_type
    volume = $Document.volume
    chapter = $Document.chapter
    title = $Document.title
    source_path = $Document.path
  }
}

$terms = @()
$searchRegex = $null
if (-not $ListEntries) {
  $terms = if ($RegexPattern) {
    @($Pattern)
  } else {
    @($Pattern -split '\|' | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  }

  $searchRegex = New-SearchRegex $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
}

$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $EpubPath))
$jsonResults = New-Object 'System.Collections.Generic.List[object]'

try {
  $documents = Get-EpubEntries $zip |
    Where-Object { Test-SelectedEntry $_ } |
    Sort-Object sort_chapter, order

  if ($TermSummary) {
    $summaryRows = New-TermSummaryRows $documents $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
    if ($Json) {
      foreach ($row in $summaryRows) {
        $jsonResults.Add($row)
      }
    } else {
      Format-TermSummaryTable $summaryRows
    }
  } elseif ($ListEntries) {
    if ($Json) {
      foreach ($document in $documents) {
        $jsonResults.Add((Convert-DocumentToJsonObject $document))
      }
    } else {
      foreach ($document in $documents) {
        $volumeText = if ($null -ne $document.volume) { "Vol $($document.volume)" } else { "Vol -" }
        $chapterText = if ($null -ne $document.chapter) { "Ch $($document.chapter)" } else { "Ch -" }
        "$($document.entry_type) | $volumeText | $chapterText | $($document.file_name) | $($document.title)"
      }
    }
  } else {
    foreach ($document in $documents) {
      $lines = $document.lines
      $hitIndexes = New-Object 'System.Collections.Generic.List[int]'
      $termCounts = [ordered]@{}

      foreach ($term in $terms) {
        $termRegex = New-SearchRegex @($term) $RegexPattern.IsPresent $CaseSensitive.IsPresent
        $count = 0
        foreach ($line in $lines) {
          $count += $termRegex.Matches($line).Count
        }
        if ($count -gt 0) {
          $termCounts[$term] = $count
        }
      }

      for ($index = 0; $index -lt $lines.Count; $index++) {
        if ($searchRegex.IsMatch($lines[$index])) {
          $hitIndexes.Add($index)
        }
      }

      if ($hitIndexes.Count -eq 0) {
        continue
      }

      if ($CountsOnly) {
        if ($Json) {
          foreach ($key in $termCounts.Keys) {
            $jsonResults.Add([pscustomobject]@{
              entry_type = $document.entry_type
              volume = $document.volume
              chapter = $document.chapter
              title = $document.title
              source_path = $document.path
              term = $key
              count = $termCounts[$key]
            })
          }
          continue
        }

        $countParts = @()
        foreach ($key in $termCounts.Keys) {
          $countParts += "$key=$($termCounts[$key])"
        }
        "$(Get-DocumentLabel $document): " + ($countParts -join '; ')
        continue
      }

      if (-not $Json) {
        ""
        "=== $(Get-DocumentLabel $document): $($document.title) ==="
        "$($document.path)"
      }

      $printed = 0
      foreach ($hitIndex in $hitIndexes) {
        if ($printed -ge $MaxHitsPerChapter) {
          if (-not $Json) {
            "... hit limit reached for $(Get-DocumentLabel $document) ($MaxHitsPerChapter shown of $($hitIndexes.Count))"
          }
          break
        }

        if ($ContextLines -le 0) {
          if ($Json) {
            $matchedTerms = Get-MatchedTerms $lines[$hitIndex] $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
            foreach ($matchedTerm in $matchedTerms) {
              $hit = [ordered]@{
                entry_type = $document.entry_type
                volume = $document.volume
                chapter = $document.chapter
                title = $document.title
                source_path = $document.path
                term = $matchedTerm
                line = $hitIndex + 1
                line_index = $hitIndex
                snippet = Format-Snippet $lines[$hitIndex]
              }
              if ($IncludeLineMatchCounts) {
                $hit.line_term_counts = Get-TermMatchCounts $lines[$hitIndex] $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
              }
              $jsonResults.Add([pscustomobject]$hit)
            }
          } else {
            "[${hitIndex}] $(Format-Snippet $lines[$hitIndex])"
          }
        } else {
          $start = [Math]::Max(0, $hitIndex - $ContextLines)
          $end = [Math]::Min($lines.Count - 1, $hitIndex + $ContextLines)
          if ($Json) {
            $context = @()
            for ($contextIndex = $start; $contextIndex -le $end; $contextIndex++) {
              $context += [pscustomobject]@{
                line = $contextIndex + 1
                line_index = $contextIndex
                snippet = Format-Snippet $lines[$contextIndex]
              }
            }

            $matchedTerms = Get-MatchedTerms $lines[$hitIndex] $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
            foreach ($matchedTerm in $matchedTerms) {
              $hit = [ordered]@{
                entry_type = $document.entry_type
                volume = $document.volume
                chapter = $document.chapter
                title = $document.title
                source_path = $document.path
                term = $matchedTerm
                line = $hitIndex + 1
                line_index = $hitIndex
                snippet = Format-Snippet $lines[$hitIndex]
                context = $context
              }
              if ($IncludeLineMatchCounts) {
                $hit.line_term_counts = Get-TermMatchCounts $lines[$hitIndex] $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
              }
              $jsonResults.Add([pscustomobject]$hit)
            }
          } else {
            for ($contextIndex = $start; $contextIndex -le $end; $contextIndex++) {
              "[${contextIndex}] $(Format-Snippet $lines[$contextIndex])"
            }
            "--"
          }
        }

        $printed++
      }
    }
  }
} finally {
  $zip.Dispose()
}

if ($Json) {
  ConvertTo-Json -InputObject @($jsonResults.ToArray()) -Depth 6
}
