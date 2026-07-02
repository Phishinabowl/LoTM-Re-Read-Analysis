param(
  [string]$EpubPath = "Source/Lord of Mysteries - Book 1.epub",
  [ValidateRange(1, 999)]
  [int]$StartChapter = 1,
  [ValidateRange(1, 999)]
  [int]$EndChapter = 213,
  [string]$Pattern,
  [int]$ContextLines = 0,
  [int]$MaxHitsPerChapter = 50,
  [switch]$CountsOnly,
  [switch]$RegexPattern,
  [switch]$CaseSensitive,
  [switch]$Json
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Pattern)) {
  throw "Provide -Pattern. For literal multi-term searches, separate terms with |, such as -Pattern `"Dunn|Captain|Nighthawk`"."
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

$terms = if ($RegexPattern) {
  @($Pattern)
} else {
  @($Pattern -split '\|' | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

$searchRegex = New-SearchRegex $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $EpubPath))
$jsonResults = New-Object 'System.Collections.Generic.List[object]'

try {
  foreach ($chapter in $StartChapter..$EndChapter) {
    $entryName = "OEBPS/Text/volume_1_clown_chapter_$chapter.xhtml"
    $entry = $zip.Entries | Where-Object { $_.FullName -eq $entryName } | Select-Object -First 1

    if (-not $entry) {
      continue
    }

    $reader = [System.IO.StreamReader]::new($entry.Open())
    try {
      $xhtml = $reader.ReadToEnd()
    } finally {
      $reader.Close()
    }

    $lines = Convert-XhtmlToLines $xhtml
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
            chapter = $chapter
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
      "Ch ${chapter}: " + ($countParts -join '; ')
      continue
    }

    if (-not $Json) {
      ""
      "=== Chapter $chapter ==="
    }

    $printed = 0
    foreach ($hitIndex in $hitIndexes) {
      if ($printed -ge $MaxHitsPerChapter) {
        if (-not $Json) {
          "... hit limit reached for Chapter $chapter ($MaxHitsPerChapter shown of $($hitIndexes.Count))"
        }
        break
      }

      if ($ContextLines -le 0) {
        if ($Json) {
          $matchedTerms = Get-MatchedTerms $lines[$hitIndex] $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
          foreach ($matchedTerm in $matchedTerms) {
            $jsonResults.Add([pscustomobject]@{
              chapter = $chapter
              term = $matchedTerm
              line = $hitIndex + 1
              line_index = $hitIndex
              snippet = Format-Snippet $lines[$hitIndex]
            })
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
            $jsonResults.Add([pscustomobject]@{
              chapter = $chapter
              term = $matchedTerm
              line = $hitIndex + 1
              line_index = $hitIndex
              snippet = Format-Snippet $lines[$hitIndex]
              context = $context
            })
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
} finally {
  $zip.Dispose()
}

if ($Json) {
  ConvertTo-Json -InputObject @($jsonResults.ToArray()) -Depth 6
}
