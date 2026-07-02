param(
  [string]$EpubPath = "Source/Lord of Mysteries - Book 1.epub",
  [int]$StartChapter = 1,
  [int]$EndChapter = 213,
  [string]$Pattern,
  [int]$ContextLines = 0,
  [int]$MaxHitsPerChapter = 50,
  [switch]$CountsOnly,
  [switch]$RegexPattern,
  [switch]$CaseSensitive
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Pattern)) {
  throw "Provide -Pattern. For literal multi-term searches, separate terms with |, such as -Pattern `"Dunn|Captain|Nighthawk`"."
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

$terms = if ($RegexPattern) {
  @($Pattern)
} else {
  @($Pattern -split '\|' | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

$searchRegex = New-SearchRegex $terms $RegexPattern.IsPresent $CaseSensitive.IsPresent
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $EpubPath))

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
      $countParts = @()
      foreach ($key in $termCounts.Keys) {
        $countParts += "$key=$($termCounts[$key])"
      }
      "Ch ${chapter}: " + ($countParts -join '; ')
      continue
    }

    ""
    "=== Chapter $chapter ==="

    $printed = 0
    foreach ($hitIndex in $hitIndexes) {
      if ($printed -ge $MaxHitsPerChapter) {
        "... hit limit reached for Chapter $chapter ($MaxHitsPerChapter shown of $($hitIndexes.Count))"
        break
      }

      if ($ContextLines -le 0) {
        "[${hitIndex}] $(Format-Snippet $lines[$hitIndex])"
      } else {
        $start = [Math]::Max(0, $hitIndex - $ContextLines)
        $end = [Math]::Min($lines.Count - 1, $hitIndex + $ContextLines)
        for ($contextIndex = $start; $contextIndex -le $end; $contextIndex++) {
          "[${contextIndex}] $(Format-Snippet $lines[$contextIndex])"
        }
        "--"
      }

      $printed++
    }
  }
} finally {
  $zip.Dispose()
}
